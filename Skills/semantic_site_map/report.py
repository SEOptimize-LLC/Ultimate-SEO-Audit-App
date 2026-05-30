"""GSC join, four output files, scatter-plot PNG."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # non-interactive backend for server-side rendering
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

logger = logging.getLogger(__name__)

RING_NAMES = ("core", "focus", "expansion", "peripheral")
HIGH_CLICK_QUANTILE = 0.75
# Cosine distance from site center above which a page is a genuine
# "siteRadius outlier" in the May 2024 leak sense (topically off-brand,
# diluting siteFocusScore). Used for both the standalone outlier check
# and the high-click off-topic check.
OUTLIER_RADIUS_THRESHOLD = 0.6
HIGH_RADIUS_THRESHOLD = OUTLIER_RADIUS_THRESHOLD  # legacy alias
# Below this cosine similarity between the unweighted and click-weighted
# centroids, traffic and content are misaligned enough to surface as a
# HIGH-severity finding. 0.9 is empirically the "they basically agree"
# boundary in 1536-dim embedding space.
CENTROID_DRIFT_SIMILARITY_THRESHOLD = 0.9
ACTION_LABELS = ("keep", "grow", "relocate", "prune")


def classify_pages_by_action(
    urls: list[str],
    clicks_per_url: dict[str, float],
    value_per_url: dict[str, float],
) -> dict[str, str]:
    """Assign each URL to one of keep / grow / relocate / prune.

    Median-split on BOTH clicks and value:
        High clicks + High value -> keep
        Low  clicks + High value -> grow      (opportunity)
        High clicks + Low  value -> relocate  (dilution)
        Low  clicks + Low  value -> prune

    A URL missing from clicks_per_url is treated as 0 clicks. A URL
    missing from value_per_url is treated as 0 value. Median is computed
    across the input URL set; ties on the median fall to the LOW side
    (deterministic and conservative - it's easier to graduate a page
    upward later than to undo a "keep" recommendation).

    Args:
        urls: All URLs to classify.
        clicks_per_url: Per-URL click count from GSC (90-day default).
        value_per_url: Per-URL business value score (0..100 from
            ``value.derive_business_value``).

    Returns:
        Dict mapping every input URL to one of ACTION_LABELS.
    """
    if not urls:
        return {}

    clicks = [float(clicks_per_url.get(u, 0)) for u in urls]
    values = [float(value_per_url.get(u, 0)) for u in urls]
    # numpy.median to avoid sorting twice; mirrors how the rest of the
    # report computes quartile thresholds.
    import numpy as np
    clicks_median = float(np.median(clicks))
    value_median = float(np.median(values))

    actions: dict[str, str] = {}
    for url, c, v in zip(urls, clicks, values):
        is_high_clicks = c > clicks_median
        is_high_value = v > value_median
        if is_high_clicks and is_high_value:
            actions[url] = "keep"
        elif not is_high_clicks and is_high_value:
            actions[url] = "grow"
        elif is_high_clicks and not is_high_value:
            actions[url] = "relocate"
        else:
            actions[url] = "prune"
    return actions


def aggregate_clicks_by_cluster(
    urls: list[str],
    cluster_labels: np.ndarray,
    gsc: Optional[pd.DataFrame],
) -> dict[int, dict]:
    """Sum clicks/impressions per cluster id (including -1)."""
    df = pd.DataFrame({"url": urls, "cluster": cluster_labels})
    if gsc is None:
        return {
            int(c): {
                "clicks": 0,
                "impressions": 0,
                "urls": int((cluster_labels == c).sum()),
            }
            for c in set(cluster_labels)
        }

    merged = df.merge(
        gsc[["url", "clicks", "impressions"]], on="url", how="left"
    )
    merged[["clicks", "impressions"]] = merged[
        ["clicks", "impressions"]
    ].fillna(0)
    grouped = merged.groupby("cluster").agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        urls=("url", "count"),
    )
    return {
        int(c): {
            "clicks": int(r["clicks"]),
            "impressions": int(r["impressions"]),
            "urls": int(r["urls"]),
        }
        for c, r in grouped.iterrows()
    }


def classify_into_rings(
    urls: list[str],
    cluster_labels: np.ndarray,
    radii: np.ndarray,
    outlier_threshold: float = OUTLIER_RADIUS_THRESHOLD,
) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    """Split URLs into 4 ring quartiles + outliers + unclustered.

    Outliers are defined by SITERADIUS (cosine distance to site center
    >= outlier_threshold), not by HDBSCAN's -1 noise label. A page can
    be HDBSCAN-unclustered while sitting close to the topical center -
    it's "topologically isolated in embedding space" but not "off-topic
    for the site." Conflating those two concepts (as v0 did) produced
    false-positive outlier findings.

    Returns:
        rings:      4 quartile buckets keyed by RING_NAMES, computed
                    over ALL non-outlier pages.
        outliers:   pages with siteRadius >= outlier_threshold (the
                    leak's actual concept; goes to the auditor).
        unclustered: pages HDBSCAN couldn't fit into a cluster AND
                    whose siteRadius is below the outlier threshold.
                    Surfaced for analyst review but NOT treated as
                    off-topic.
    """
    radii = np.asarray(radii)
    cluster_labels = np.asarray(cluster_labels)

    rings: dict[str, list[dict]] = {n: [] for n in RING_NAMES}

    outlier_mask = radii >= outlier_threshold
    on_topic_mask = ~outlier_mask
    unclustered_on_topic_mask = on_topic_mask & (cluster_labels == -1)

    outliers = [
        {"url": u, "site_radius": float(r)}
        for u, r, m in zip(urls, radii, outlier_mask) if m
    ]
    unclustered = [
        {"url": u, "site_radius": float(r)}
        for u, r, m in zip(urls, radii, unclustered_on_topic_mask) if m
    ]

    on_topic_urls = [u for u, m in zip(urls, on_topic_mask) if m]
    on_topic_radii = radii[on_topic_mask]
    if len(on_topic_radii) == 0:
        return rings, outliers, unclustered

    quartiles = np.quantile(on_topic_radii, [0.25, 0.5, 0.75])
    for u, r in zip(on_topic_urls, on_topic_radii):
        if r <= quartiles[0]:
            rings["core"].append({"url": u, "site_radius": float(r)})
        elif r <= quartiles[1]:
            rings["focus"].append({"url": u, "site_radius": float(r)})
        elif r <= quartiles[2]:
            rings["expansion"].append(
                {"url": u, "site_radius": float(r)}
            )
        else:
            rings["peripheral"].append(
                {"url": u, "site_radius": float(r)}
            )

    return rings, outliers, unclustered


def pick_central_entity(
    cluster_labels: np.ndarray,
    cluster_name_by_id: dict[int, str],
) -> str:
    """The largest non-outlier cluster's human label."""
    counts = pd.Series(cluster_labels).value_counts()
    counts = counts[counts.index != -1]
    if counts.empty:
        return "Unknown"
    top_cluster = int(counts.idxmax())
    return cluster_name_by_id.get(top_cluster, f"Cluster {top_cluster}")


def find_high_click_off_topic_clusters(
    clicks_by_cluster: dict[int, dict],
    cluster_labels: np.ndarray,
    radii: np.ndarray,
    cluster_name_by_id: dict[int, str],
) -> list[dict]:
    """Clusters above the 75th pct in clicks AND median siteRadius > 0.6."""
    clusters_only = {
        c: d for c, d in clicks_by_cluster.items() if c != -1
    }
    if not clusters_only:
        return []

    click_values = [d["clicks"] for d in clusters_only.values()]
    if not click_values or max(click_values) == 0:
        return []
    click_threshold = float(
        np.quantile(click_values, HIGH_CLICK_QUANTILE)
    )

    flagged = []
    for cid, data in clusters_only.items():
        mask = cluster_labels == cid
        if not mask.any():
            continue
        median_radius = float(np.median(radii[mask]))
        if (
            data["clicks"] >= click_threshold
            and median_radius > HIGH_RADIUS_THRESHOLD
        ):
            flagged.append({
                "cluster_id": cid,
                "cluster_name": cluster_name_by_id.get(
                    cid, f"Cluster {cid}"
                ),
                "clicks": data["clicks"],
                "median_site_radius": median_radius,
                "page_count": int(mask.sum()),
            })
    return sorted(flagged, key=lambda x: -x["clicks"])


def _render_scatter(
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    radii: np.ndarray,
    clicks_by_url: dict[str, int],
    urls: list[str],
    out_path: Path,
    client_name: str,
    site_center: Optional[np.ndarray] = None,
) -> None:
    """2D scatter via PCA. Rings = real siteRadius quartiles.

    The site-center marker is placed at the PCA-projection of the
    actual site_center vector (the mean embedding) - NOT at the
    arbitrary origin of PCA space.

    Rings are computed from the real cosine-distance siteRadius
    quartiles, then converted into PCA-space radii via a linear
    regression of (cosine distance to center) vs. (PCA distance to
    projected center). This makes the visual rings actually match
    the ring-bucket assignment used by classify_into_rings.
    """
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(embeddings)

    # Project the actual site center into PCA space.
    if site_center is None:
        center_2d = np.array([0.0, 0.0])
    else:
        center_2d = pca.transform(
            site_center.reshape(1, -1)
        )[0]

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect("equal")

    # PCA distance to the projected center, per point.
    pc_dists_to_center = np.linalg.norm(
        coords - center_2d, axis=1
    )

    # Use PCA-distance quartiles directly. Mapping cosine-distance
    # quartiles into PCA space via np.interp produces non-monotonic
    # results (PCA is a lossy 2D projection of a 1536D space, so
    # the relationship is noisy). PCA-distance quartiles are
    # guaranteed monotonic and visually intuitive - they show how
    # the page population is spread out in the 2D embedding view.
    if len(pc_dists_to_center) > 1:
        ring_pca_radii = list(np.quantile(
            pc_dists_to_center, [0.25, 0.5, 0.75, 0.95]
        ))
    else:
        ring_pca_radii = [0.1, 0.2, 0.3, 0.4]

    ring_colors = ["#3aa676", "#3a7da6", "#d4a017", "#c75450"]
    ring_labels = ["Core", "Focus", "Expansion", "Peripheral"]
    # Place each label at a distinct angle so they don't overlap.
    # Core at top, Focus right, Expansion bottom, Peripheral left.
    label_angles_deg = [90, 0, 270, 180]
    for r, color, label, angle in zip(
        ring_pca_radii, ring_colors, ring_labels, label_angles_deg
    ):
        circle = plt.Circle(
            tuple(center_2d),
            r,
            fill=False,
            linestyle="--",
            linewidth=1.4,
            color=color,
            alpha=0.75,
        )
        ax.add_patch(circle)
        rad = np.deg2rad(angle)
        offset_x = center_2d[0] + r * np.cos(rad)
        offset_y = center_2d[1] + r * np.sin(rad)
        ax.text(
            offset_x,
            offset_y,
            f" {label} ",
            fontsize=10,
            color=color,
            alpha=0.95,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                edgecolor=color,
                alpha=0.85,
            ),
        )

    unique = sorted(set(cluster_labels))
    cmap = plt.colormaps.get_cmap("tab20")
    color_map = {
        c: cmap(i / max(1, len(unique)))
        for i, c in enumerate(unique)
    }
    color_map[-1] = (0.7, 0.7, 0.7, 0.4)

    # Point size: floor 25 (always visible), scale by clicks if
    # GSC data is present, otherwise everything sits at the floor.
    has_clicks = any(clicks_by_url.get(u, 0) > 0 for u in urls)
    if has_clicks:
        max_clicks = max(clicks_by_url.values()) or 1
        sizes = np.array([
            max(25, min(600, 25 + clicks_by_url.get(u, 0) * 500
                        / max_clicks))
            for u in urls
        ])
    else:
        sizes = np.full(len(urls), 35)

    colors = [color_map[c] for c in cluster_labels]
    ax.scatter(
        coords[:, 0],
        coords[:, 1],
        s=sizes,
        c=colors,
        alpha=0.65,
        edgecolors="white",
        linewidths=0.4,
    )
    # Site Center marker.
    ax.scatter(
        [center_2d[0]],
        [center_2d[1]],
        marker="*",
        s=600,
        color="black",
        zorder=5,
        label="Site Center",
        edgecolors="white",
        linewidths=1.5,
    )
    ax.annotate(
        "Site Center",
        xy=(center_2d[0], center_2d[1]),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
        zorder=6,
    )

    title_suffix = " (point size = GSC clicks)" if has_clicks else ""
    ax.set_title(
        f"Semantic Site Map - {client_name}{title_suffix}",
        fontsize=15,
        pad=14,
    )
    ax.set_xlabel("Topical axis 1 (PCA)")
    ax.set_ylabel("Topical axis 2 (PCA)")
    ax.grid(True, linestyle="--", alpha=0.25)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _render_markdown_report(
    cluster_result: dict,
    clicks_by_cluster: dict,
    high_click_off_topic: list[dict],
    central_entity: str,
    client_name: str,
    has_gsc: bool,
    n_outliers: int,
    n_unclustered: int,
    page_actions: Optional[dict[str, str]] = None,
    clicks_per_url: Optional[dict[str, float]] = None,
    value_per_url: Optional[dict[str, float]] = None,
    drift: Optional[dict] = None,
) -> str:
    cluster_labels = cluster_result["cluster_labels"]
    cluster_name_by_id = cluster_result["cluster_name_by_id"]
    ngrams_by_cluster = cluster_result["ngrams_by_cluster"]
    n_total = len(cluster_labels)

    lines = [
        f"# Semantic Site Map - {client_name}",
        "",
        f"- **Central entity (largest cluster):** {central_entity}",
        f"- **URLs analyzed:** {n_total}",
        (
            "- **Outliers (siteRadius >= "
            f"{OUTLIER_RADIUS_THRESHOLD}):** {n_outliers} "
            "(genuinely off-topic for the site)"
        ),
        (
            f"- **Unclustered on-topic:** {n_unclustered} "
            "(close to site center but not in a dense cluster - "
            "long-tail blog posts, edge cases)"
        ),
        (
            "- **Click overlay:** "
            f"{'present' if has_gsc else 'click data unavailable'}"
        ),
        "",
        "## Clusters",
        "",
    ]
    clusters_only = {
        c: d for c, d in clicks_by_cluster.items() if c != -1
    }
    sorted_clusters = sorted(
        clusters_only.items(), key=lambda kv: -kv[1]["clicks"],
    )
    for cid, data in sorted_clusters:
        label = cluster_name_by_id.get(cid, f"Cluster {cid}")
        ngrams = ngrams_by_cluster.get(cid, [])
        lines.append(f"### {label} (cluster {cid})")
        lines.append(f"- Pages: {data['urls']}")
        if has_gsc:
            lines.append(f"- Clicks (90d): {data['clicks']}")
            lines.append(f"- Impressions (90d): {data['impressions']}")
        if ngrams:
            lines.append(f"- Top terms: {', '.join(ngrams[:8])}")
        lines.append("")

    if high_click_off_topic:
        lines.append(
            "## Dilution-driving clusters (high traffic, off-topic)"
        )
        lines.append("")
        lines.append(
            "These clusters earn meaningful traffic but sit far from "
            "the site's topical center. They are the highest-leverage "
            "prune-or-relocate candidates."
        )
        lines.append("")
        for entry in high_click_off_topic:
            lines.append(
                f"- **{entry['cluster_name']}** - "
                f"{entry['clicks']} clicks across "
                f"{entry['page_count']} pages, "
                f"median siteRadius "
                f"{entry['median_site_radius']:.2f}"
            )
        lines.append("")

    # Click-weighted centroid drift callout.
    if drift is not None:
        sim = drift.get("cosine_similarity", 1.0)
        lines.append("## Click-weighted centroid drift")
        lines.append("")
        lines.append(
            f"- **Cosine similarity (unweighted vs. click-weighted "
            f"centroid):** {sim:.3f}"
        )
        if sim >= CENTROID_DRIFT_SIMILARITY_THRESHOLD:
            lines.append(
                "- **Verdict:** Traffic and content are aligned. The "
                "site's most-visited pages sit near the topical center."
            )
        else:
            lines.append(
                "- **Verdict:** Traffic is concentrated in a part of "
                "the embedding space that is NOT the site's topical "
                "center. The site's stated topic and the topic people "
                "actually visit it for are diverging."
            )
            top_drift = drift.get("top_drift_clusters", [])
            if top_drift:
                lines.append("")
                lines.append("**Clusters most responsible for the drift:**")
                for c in top_drift:
                    lines.append(
                        f"- **{c['cluster_name']}** - "
                        f"{c['clicks']} clicks across "
                        f"{c['page_count']} pages"
                    )
        lines.append("")

    # Keep / Grow / Relocate / Prune per-page action matrix.
    if page_actions:
        from collections import Counter
        counts = Counter(page_actions.values())
        lines.append("## Page-action matrix (Keep / Grow / Relocate / Prune)")
        lines.append("")
        lines.append(
            "Each page is classified by median-split on **clicks** "
            "(GSC) and **business value** (auto-derived from URL "
            "pattern + GSC commercial intent + GA4 conversions when "
            "available)."
        )
        lines.append("")
        lines.append("| Action | Pages | Meaning |")
        lines.append("|---|---|---|")
        lines.append(
            f"| Keep | {counts.get('keep', 0)} | "
            "High clicks + high value. Protect; refresh; expand. |"
        )
        lines.append(
            f"| Grow | {counts.get('grow', 0)} | "
            "Low clicks + high value. The opportunity - "
            "money pages people are not finding. |"
        )
        lines.append(
            f"| Relocate | {counts.get('relocate', 0)} | "
            "High clicks + low value. The dilution - moving these to a "
            "subdomain preserves the traffic and reclaims topical focus. |"
        )
        lines.append(
            f"| Prune | {counts.get('prune', 0)} | "
            "Low clicks + low value. Consolidate, noindex, or 410. |"
        )
        lines.append("")

        # Top URLs per action bucket, ranked by clicks * value for
        # the actionable buckets, or just clicks for prune.
        clicks = clicks_per_url or {}
        values = value_per_url or {}
        for action in ("grow", "relocate", "keep", "prune"):
            urls_in_bucket = [
                u for u, a in page_actions.items() if a == action
            ]
            if not urls_in_bucket:
                continue
            if action == "prune":
                urls_in_bucket.sort(key=lambda u: -clicks.get(u, 0))
            else:
                urls_in_bucket.sort(
                    key=lambda u: -(
                        clicks.get(u, 0) * (values.get(u, 0) + 1)
                    )
                )
            lines.append(f"### Top {action.capitalize()} URLs (up to 10)")
            for u in urls_in_bucket[:10]:
                lines.append(
                    f"- `{u}`  (clicks={int(clicks.get(u, 0))}, "
                    f"value={values.get(u, 0):.0f})"
                )
            lines.append("")

    return "\n".join(lines)


def compute_click_weighted_centroid_drift(
    urls: list[str],
    embeddings: np.ndarray,
    site_center: np.ndarray,
    clicks_per_url: dict[str, float],
    cluster_labels: np.ndarray,
    cluster_name_by_id: dict[int, str],
) -> dict:
    """Compare the unweighted vs click-weighted topical centroid.

    The unweighted centroid is the site's mean embedding (already passed
    in as ``site_center``). The click-weighted centroid is the same mean
    but with each page weighted by its click count - the place in
    embedding space where the site's traffic actually lives.

    When the two centroids point in the same direction (cosine similarity
    >= CENTROID_DRIFT_SIMILARITY_THRESHOLD), traffic and content align.
    When they diverge, the site's traffic is concentrated in a part of
    the embedding space that's NOT the site's stated topical focus -
    the auditor surfaces this as a HIGH finding.

    Returns a dict with:
        cosine_similarity:    float in [-1, 1]
        click_weighted_centroid: list[float] - the weighted mean
        top_drift_clusters:   list of cluster dicts most responsible
                              for the drift, sorted by click contribution
                              (empty when similarity is above threshold)
    """
    if len(urls) == 0 or len(embeddings) == 0:
        return {
            "cosine_similarity": 1.0,
            "click_weighted_centroid": [float(x) for x in site_center],
            "top_drift_clusters": [],
        }

    weights = np.array(
        [float(clicks_per_url.get(u, 0)) for u in urls],
        dtype=np.float64,
    )
    total_clicks = weights.sum()
    if total_clicks <= 0:
        # No click data - can't compute a weighted centroid.
        return {
            "cosine_similarity": 1.0,
            "click_weighted_centroid": [float(x) for x in site_center],
            "top_drift_clusters": [],
        }

    weighted_centroid = (embeddings * weights[:, None]).sum(axis=0) / total_clicks
    # Cosine similarity between the two centroids.
    norm_a = np.linalg.norm(site_center)
    norm_b = np.linalg.norm(weighted_centroid)
    if norm_a == 0 or norm_b == 0:
        cosine_sim = 1.0
    else:
        cosine_sim = float(
            np.dot(site_center, weighted_centroid) / (norm_a * norm_b)
        )

    # When the centroids diverge, identify which clusters are pulling
    # the click-weighted centroid away from the unweighted one. Approach:
    # for each cluster, compute its share of total clicks AND its
    # distance from the unweighted centroid; clusters that combine
    # large click share + large distance are the drift drivers.
    top_drift_clusters: list[dict] = []
    if cosine_sim < CENTROID_DRIFT_SIMILARITY_THRESHOLD:
        unique_clusters = sorted({int(c) for c in cluster_labels if c != -1})
        cluster_drift_scores: list[tuple[int, float, int, float]] = []
        for cid in unique_clusters:
            mask = cluster_labels == cid
            if not mask.any():
                continue
            cluster_clicks = float(weights[mask].sum())
            if cluster_clicks <= 0:
                continue
            cluster_mean = embeddings[mask].mean(axis=0)
            distance_from_center = float(
                np.linalg.norm(cluster_mean - site_center)
            )
            # Drift score = click share * distance. Bigger = more guilty.
            click_share = cluster_clicks / total_clicks
            drift_score = click_share * distance_from_center
            cluster_drift_scores.append(
                (cid, drift_score, int(mask.sum()), cluster_clicks)
            )
        cluster_drift_scores.sort(key=lambda t: -t[1])
        for cid, _drift, page_count, clicks_n in cluster_drift_scores[:5]:
            top_drift_clusters.append({
                "cluster_id": cid,
                "cluster_name": cluster_name_by_id.get(
                    cid, f"Cluster {cid}"
                ),
                "clicks": int(clicks_n),
                "page_count": page_count,
            })

    return {
        "cosine_similarity": cosine_sim,
        "click_weighted_centroid": [float(x) for x in weighted_centroid],
        "top_drift_clusters": top_drift_clusters,
    }


def build_outputs(
    out_dir: Path,
    text_df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_result: dict,
    gsc: Optional[pd.DataFrame],
    client_name: str,
    model_name: str,
    ga4: Optional[pd.DataFrame] = None,
) -> dict[str, Path]:
    """Emit the four output files; return their paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = text_df["url"].tolist()
    cluster_labels = cluster_result["cluster_labels"]
    radii = cluster_result["site_radius"]
    cluster_name_by_id = cluster_result["cluster_name_by_id"]

    clicks_by_cluster = aggregate_clicks_by_cluster(
        urls, cluster_labels, gsc
    )
    rings, outliers, unclustered = classify_into_rings(
        urls, cluster_labels, radii
    )
    central_entity = pick_central_entity(
        cluster_labels, cluster_name_by_id
    )
    high_click_off_topic = find_high_click_off_topic_clusters(
        clicks_by_cluster,
        cluster_labels,
        radii,
        cluster_name_by_id,
    )

    # Per-URL click count (used by both action classifier and drift calc).
    clicks_per_url: dict[str, float] = {}
    if gsc is not None and "url" in gsc.columns and "clicks" in gsc.columns:
        per_url_clicks = gsc.groupby("url")["clicks"].sum()
        clicks_per_url = {
            str(u): float(c) for u, c in per_url_clicks.items()
        }

    # Business value per URL (auto-derived from URL pattern + optional
    # GSC commercial-intent + optional GA4 conversions).
    from Skills.semantic_site_map.value import derive_business_value
    value_per_url = derive_business_value(urls, gsc_df=gsc, ga4_df=ga4)

    # Keep / Grow / Relocate / Prune classifier.
    page_actions = classify_pages_by_action(
        urls, clicks_per_url, value_per_url
    )

    # Click-weighted centroid drift (the leak-grounded "is traffic
    # aligned with content?" check).
    site_center = cluster_result["site_center"]
    drift = compute_click_weighted_centroid_drift(
        urls,
        embeddings,
        site_center,
        clicks_per_url,
        cluster_labels,
        cluster_name_by_id,
    )

    # 1) Koray-compatible JSON
    koray = {
        "central_entity": central_entity,
        "rings": rings,
        "outliers": [o["url"] for o in outliers],
        "generated_from": "semantic-site-map skill",
    }
    topical_map_json = out_dir / "topical_map.json"
    topical_map_json.write_text(
        json.dumps(koray, indent=2), encoding="utf-8"
    )

    # 2) Rich JSON
    full = {
        "central_entity": central_entity,
        "client_name": client_name,
        "embedding_model_used": model_name,
        "rings": rings,
        "outliers": outliers,
        "unclustered_on_topic": unclustered,
        "outlier_radius_threshold": OUTLIER_RADIUS_THRESHOLD,
        "clicks_by_cluster": (
            clicks_by_cluster if gsc is not None else {}
        ),
        "site_radius_per_url": {
            u: float(r) for u, r in zip(urls, radii)
        },
        "cluster_labels_per_url": {
            u: int(c) for u, c in zip(urls, cluster_labels)
        },
        "cluster_name_by_id": {
            str(k): v for k, v in cluster_name_by_id.items()
        },
        "high_click_off_topic_clusters": high_click_off_topic,
        "value_per_url": value_per_url,
        "page_action_per_url": page_actions,
        "click_weighted_centroid_drift": drift,
    }
    full_json = out_dir / "semantic_map_full.json"
    full_json.write_text(
        json.dumps(full, indent=2), encoding="utf-8"
    )

    # 3) Markdown report
    md = _render_markdown_report(
        cluster_result,
        clicks_by_cluster,
        high_click_off_topic,
        central_entity,
        client_name,
        has_gsc=(gsc is not None),
        n_outliers=len(outliers),
        n_unclustered=len(unclustered),
        page_actions=page_actions,
        clicks_per_url=clicks_per_url,
        value_per_url=value_per_url,
        drift=drift,
    )
    report_md = out_dir / "semantic_map_report.md"
    report_md.write_text(md, encoding="utf-8")

    # 4) Scatter PNG
    clicks_by_url: dict[str, int] = {}
    if gsc is not None:
        per_url = gsc.groupby("url")["clicks"].sum()
        clicks_by_url = {str(u): int(c) for u, c in per_url.items()}
    png = out_dir / "semantic_map.png"
    _render_scatter(
        embeddings,
        cluster_labels,
        radii,
        clicks_by_url,
        urls,
        png,
        client_name,
        site_center=cluster_result.get("site_center"),
    )

    return {
        "topical_map_json": topical_map_json,
        "full_json": full_json,
        "report_md": report_md,
        "png": png,
    }
