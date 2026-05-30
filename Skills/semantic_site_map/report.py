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
) -> None:
    """2D scatter via PCA. Rings = radius quartiles. Point size = clicks."""
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(embeddings)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect("equal")

    pc_dists = np.linalg.norm(coords, axis=1)
    if len(pc_dists):
        ring_radii = np.quantile(pc_dists, [0.25, 0.5, 0.75, 0.95])
        ring_colors = ["#3aa676", "#3a7da6", "#d4a017", "#c75450"]
        ring_labels = ["Core", "Focus", "Expansion", "Peripheral"]
        for r, color, label in zip(
            ring_radii, ring_colors, ring_labels
        ):
            circle = plt.Circle(
                (0, 0),
                r,
                fill=False,
                linestyle="--",
                linewidth=1.2,
                color=color,
                alpha=0.7,
            )
            ax.add_patch(circle)
            ax.text(
                r * 0.71,
                r * 0.71,
                label,
                fontsize=8,
                color=color,
                alpha=0.85,
            )

    unique = sorted(set(cluster_labels))
    cmap = plt.colormaps.get_cmap("tab20")
    color_map = {
        c: cmap(i / max(1, len(unique)))
        for i, c in enumerate(unique)
    }
    color_map[-1] = (0.7, 0.7, 0.7, 0.4)

    sizes = np.array([
        max(10, min(400, clicks_by_url.get(u, 0) * 4)) for u in urls
    ])
    colors = [color_map[c] for c in cluster_labels]
    ax.scatter(
        coords[:, 0],
        coords[:, 1],
        s=sizes,
        c=colors,
        alpha=0.7,
        edgecolors="none",
    )
    ax.scatter(
        [0],
        [0],
        marker="*",
        s=300,
        color="black",
        zorder=5,
        label="Site Center",
    )

    ax.set_title(f"Semantic Site Map - {client_name}", fontsize=14)
    ax.set_xlabel("Topical axis 1 (PCA)")
    ax.set_ylabel("Topical axis 2 (PCA)")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
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

    return "\n".join(lines)


def build_outputs(
    out_dir: Path,
    text_df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_result: dict,
    gsc: Optional[pd.DataFrame],
    client_name: str,
    model_name: str,
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
    )

    return {
        "topical_map_json": topical_map_json,
        "full_json": full_json,
        "report_md": report_md,
        "png": png,
    }
