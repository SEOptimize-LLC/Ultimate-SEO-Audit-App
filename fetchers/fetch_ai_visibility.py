"""
AI Visibility Tracker
Checks AI Overview presence, competitor share-of-voice, and LLM brand mentions
for a client's target keywords. Uses DataForSEO API directly (same credentials
as the DFS MCP).

Saves to Clients/{client}/data/ai-visibility/:
  - ai_overviews.json    per-keyword AI Overview presence + cited URLs
  - share_of_voice.json  client-vs-competitor citation share across the keyword set
  - llm_mentions.json    multi-model LLM mention probe (sampled, with disclosure)

Usage:
  python fetchers/fetch_ai_visibility.py --client educationwalkthrough.com
  (or called by run_fetch.py via fetch_ai_visibility.run(client))

IMPORTANT caveat on LLM-citation data (logged project lesson):
  LLM-citation tools run browse-forced harnesses that OVER-REPORT relative to a
  real end-user session. A single pull that shows "brand recommended" is NOT
  truth. This module therefore samples each model multiple times, records
  browse-on vs browse-off separately, and reports a *rate* with sample size and
  a validation instruction — never a single-pull boolean presented as fact.
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_ROOT = Path(__file__).parent.parent

logger = logging.getLogger(__name__)

# Hard cap on paid LLM probe calls per fetch so a wide keyword set / high sample
# count can never silently rack up cost. models x keywords x samples x browse
# variants is clamped to this many total requests.
MAX_LLM_PROBE_CALLS = 60


def get_auth(login: str, password: str) -> dict:
    import base64
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def _registered_domain(url: str) -> str:
    """Extract a normalized host (lowercased, leading 'www.' stripped) from a URL.

    Returns '' when the URL has no parseable host. Kept intentionally simple —
    it does not consult the public-suffix list, so 'blog.example.co.uk' stays
    'blog.example.co.uk' rather than collapsing to 'example.co.uk'. Matching in
    :func:`compute_share_of_voice` accounts for subdomains explicitly.
    """
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"//{url}", scheme="")
    host = (parsed.netloc or parsed.path).split("/")[0].split("@")[-1].split(":")[0]
    host = host.strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _host_matches(cited_host: str, target: str) -> bool:
    """True when a cited host is the target domain or a subdomain of it.

    'home.2gno.me' (a competitor listed as a subdomain in config) matches a
    cited host of 'home.2gno.me' exactly; 'blog.example.com' matches target
    'example.com'. Directionality: the cited host may be equal to or deeper
    than the target, not shallower.
    """
    target = target.strip().lower()
    if target.startswith("www."):
        target = target[4:]
    if not cited_host or not target:
        return False
    return cited_host == target or cited_host.endswith("." + target)


def _classify_host(cited_host: str, client_domain: str, competitors: list) -> tuple:
    """Return (role, matched_label) for a cited host.

    role is one of 'client', 'competitor', 'other'. matched_label is the
    client/competitor domain it matched (or the cited host itself for 'other').
    Client wins ties over a competitor that is coincidentally a subdomain.
    """
    if _host_matches(cited_host, client_domain):
        return "client", _registered_domain(client_domain)
    for comp in competitors:
        if _host_matches(cited_host, comp):
            return "competitor", _registered_domain(comp)
    return "other", cited_host


def compute_share_of_voice(
    ai_results: list,
    client_domain: str,
    competitors: list,
    top_other_limit: int = 10,
) -> dict:
    """Roll AI Overview citations up into a client-vs-competitor share of voice.

    Pure aggregation over the data :func:`check_ai_overviews` already captures —
    no network calls, so it is directly unit-testable with mocked citation data.

    Args:
        ai_results: list of per-keyword dicts, each with keys 'keyword',
            'ai_overview_present' (bool), and 'ai_overview_citations'
            (list of cited URLs).
        client_domain: the client's domain (e.g. 'educationwalkthrough.com').
        competitors: list of competitor domains (subdomains allowed, e.g.
            'home.2gno.me').
        top_other_limit: how many non-tracked ('other') domains to surface in
            the ranked context list.

    Returns:
        A structured SoV summary. 'share_of_voice_pct' is citation-share:
        an entity's citation count divided by total citations across all AI
        Overviews in the set. 'keywords_cited' counts distinct keywords in
        whose AI Overview the entity appears at least once.
    """
    competitors = competitors or []
    keywords_with_ai_overview = 0
    total_citations = 0

    # domain -> {"role", "label", "citations", "keywords": set()}
    tally: dict = {}

    def _bump(label: str, role: str, keyword: str) -> None:
        entry = tally.setdefault(
            label, {"role": role, "citations": 0, "keywords": set()}
        )
        entry["citations"] += 1
        if keyword:
            entry["keywords"].add(keyword)

    for row in ai_results:
        if not row.get("ai_overview_present"):
            continue
        citations = row.get("ai_overview_citations") or []
        if not citations:
            continue
        keywords_with_ai_overview += 1
        keyword = row.get("keyword", "")
        for url in citations:
            host = _registered_domain(url)
            if not host:
                continue
            total_citations += 1
            role, label = _classify_host(host, client_domain, competitors)
            _bump(label, role, keyword)

    def _pct(n: int) -> float:
        return round(n / total_citations * 100, 2) if total_citations else 0.0

    tracked_entities = []
    other_entities = []
    for label, entry in tally.items():
        record = {
            "domain": label,
            "role": entry["role"],
            "citations": entry["citations"],
            "keywords_cited": len(entry["keywords"]),
            "share_of_voice_pct": _pct(entry["citations"]),
        }
        if entry["role"] == "other":
            other_entities.append(record)
        else:
            tracked_entities.append(record)

    tracked_entities.sort(key=lambda r: r["citations"], reverse=True)
    other_entities.sort(key=lambda r: r["citations"], reverse=True)

    # Ensure the client and every named competitor appear even at zero citations,
    # so a "we are absent" finding is explicit rather than a silent omission.
    seen_labels = {e["domain"] for e in tracked_entities}
    for domain, role in [(client_domain, "client")] + [(c, "competitor") for c in competitors]:
        label = _registered_domain(domain)
        if label and label not in seen_labels:
            tracked_entities.append({
                "domain": label,
                "role": role,
                "citations": 0,
                "keywords_cited": 0,
                "share_of_voice_pct": 0.0,
            })
            seen_labels.add(label)

    client_label = _registered_domain(client_domain)
    client_record = next(
        (e for e in tracked_entities if e["domain"] == client_label), None
    )
    other_total = sum(e["citations"] for e in other_entities)

    return {
        "client_domain": client_label,
        "competitors": [_registered_domain(c) for c in competitors],
        "keywords_analyzed": len(ai_results),
        "keywords_with_ai_overview": keywords_with_ai_overview,
        "total_citations": total_citations,
        "client_citations": client_record["citations"] if client_record else 0,
        "client_share_of_voice_pct": client_record["share_of_voice_pct"] if client_record else 0.0,
        "tracked_entities": tracked_entities,
        "other_citations_total": other_total,
        "other_share_of_voice_pct": _pct(other_total),
        "top_other_domains": other_entities[:top_other_limit],
        "computed_at": datetime.now().isoformat(),
    }


def check_ai_overviews(keywords: list, location_code: int, language_code: str, headers: dict) -> list:
    """Check which keywords trigger AI Overviews and who is cited."""
    payload = [
        {
            "keyword": kw,
            "location_code": location_code,
            "language_code": language_code,
        }
        for kw in keywords
    ]
    response = requests.post(
        "https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for task in data.get("tasks", []):
        if task.get("status_code") != 20000:
            continue
        for result in task.get("result", []):
            keyword = result.get("keyword", "")
            items = result.get("items", [])

            ai_overview = next((i for i in items if i.get("type") == "ai_overview"), None)
            organic_results = [i for i in items if i.get("type") == "organic"]

            results.append({
                "keyword": keyword,
                "ai_overview_present": ai_overview is not None,
                "ai_overview_citations": (
                    [ref.get("url") for ref in ai_overview.get("references", [])]
                    if ai_overview else []
                ),
                "organic_position_1": organic_results[0].get("url") if organic_results else None,
                "serp_features": list({i.get("type") for i in items if i.get("type") not in ("organic", "ai_overview")}),
                "checked_at": datetime.now().isoformat(),
            })

    return results


def _brand_mentioned_in(payload: object, brand: str) -> bool:
    """Heuristic brand-mention detector over an arbitrary JSON response.

    Serializes the response and does a case-insensitive substring search for the
    brand string. Deliberately conservative and transparent — it flags presence
    of the brand token in the model's answer, which is what the caller then
    aggregates into a RATE (never presented as a standalone truth claim).
    """
    if not brand:
        return False
    return brand.lower() in json.dumps(payload, default=str).lower()


def _probe_llm_once(
    brand: str,
    keyword: str,
    model: str,
    browse: bool,
    headers: dict,
    endpoint: str,
) -> dict:
    """Run a single LLM probe and return a probe record.

    Returns a dict with keys: model, keyword, browse, brand_mentioned
    (bool | None — None means the sample could not be evaluated), error.
    Network / plan errors degrade gracefully to brand_mentioned=None so the
    aggregate rate is computed only over samples that actually returned an answer.
    """
    record = {
        "model": model,
        "keyword": keyword,
        "browse": browse,
        "brand_mentioned": None,
        "error": None,
    }
    payload = [{
        "keyword": keyword,
        "model": model,
        "web_search": browse,
    }]
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=90)
    except requests.RequestException as exc:
        record["error"] = f"request failed: {exc}"
        logger.warning("LLM probe request failed (%s/%s): %s", model, keyword, exc)
        return record

    if response.status_code in (403, 404):
        record["error"] = "LLM endpoint not available on current DataForSEO plan"
        return record
    if response.status_code >= 400:
        record["error"] = f"HTTP {response.status_code}"
        logger.warning("LLM probe HTTP %s (%s/%s)", response.status_code, model, keyword)
        return record

    try:
        body = response.json()
    except ValueError as exc:
        record["error"] = f"non-JSON response: {exc}"
        return record

    record["brand_mentioned"] = _brand_mentioned_in(body, brand)
    return record


def aggregate_llm_probes(probes: list) -> dict:
    """Aggregate raw LLM probe records into per-(model, browse) mention rates.

    Pure aggregation — unit-testable with mocked probe records. Groups by
    (model, browse) so browse-on vs browse-off can be compared directly, and
    reports a mention RATE over the samples that actually returned an answer
    (brand_mentioned is not None). Never emits a standalone "recommended=true".

    Each probe record: {model, keyword, browse, brand_mentioned: bool|None, error}.
    """
    groups: dict = {}
    for p in probes:
        key = (p.get("model", "unknown"), bool(p.get("browse")))
        g = groups.setdefault(key, {"samples": 0, "valid": 0, "mentions": 0, "errors": 0})
        g["samples"] += 1
        if p.get("error"):
            g["errors"] += 1
        if p.get("brand_mentioned") is None:
            continue
        g["valid"] += 1
        if p.get("brand_mentioned"):
            g["mentions"] += 1

    model_rows = []
    total_valid = 0
    total_mentions = 0
    for (model, browse), g in sorted(groups.items()):
        rate = round(g["mentions"] / g["valid"], 3) if g["valid"] else None
        total_valid += g["valid"]
        total_mentions += g["mentions"]
        model_rows.append({
            "model": model,
            "browse": browse,
            "samples": g["samples"],
            "valid_samples": g["valid"],
            "brand_mentions": g["mentions"],
            "mention_rate": rate,
            "errors": g["errors"],
        })

    overall_rate = round(total_mentions / total_valid, 3) if total_valid else None

    return {
        "models": model_rows,
        "total_samples": len(probes),
        "total_valid_samples": total_valid,
        "total_brand_mentions": total_mentions,
        "overall_mention_rate": overall_rate,
        "caveat": (
            "Mention rates are from a browse-forced probe harness that "
            "over-reports relative to real end-user sessions. A single pull is "
            "not truth; rates are only meaningful with the sample size shown."
        ),
        "validation_method": (
            "Before reporting any rate to a client, reproduce the highest-rate "
            "(model, keyword) in a real logged-in session with browsing in its "
            "default state, and compare browse-on vs browse-off rows below. "
            "Report the browse mode and sample size alongside every rate."
        ),
        "computed_at": datetime.now().isoformat(),
    }


def check_llm_mentions(
    brand: str,
    keywords: list,
    headers: dict,
    models: list | None = None,
    samples: int = 2,
    browse_modes: list | None = None,
    endpoint: str = "https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live",
    max_keywords: int = 10,
) -> dict:
    """Multi-model, sampled LLM brand-mention probe with explicit disclosure.

    Backward compatible: still callable as ``check_llm_mentions(brand, keywords,
    headers)``. New behavior and optional params layer on top.

    Sampling / browse / validation protocol (why this is not a single pull):
      * LLM-citation harnesses OVER-REPORT vs real user sessions, so we never
        treat one response as truth. We sample each (model, keyword, browse)
        combination ``samples`` times and report a mention RATE with sample size.
      * We probe both browse-on and browse-off (``browse_modes``) so the caller
        can see how much of any "brand recommended" signal depends on forced
        web browsing — the main driver of over-reporting.
      * The returned ``validation_method`` instructs the analyst to reproduce
        the top result in a real session before reporting it to a client.
      * Total request volume is clamped to MAX_LLM_PROBE_CALLS to bound cost.

    Args:
        brand: brand string to detect in model answers.
        keywords: target queries (capped at ``max_keywords``).
        headers: DataForSEO auth headers.
        models: LLM model identifiers to probe (default ['chatgpt']).
        samples: repeats per (model, keyword, browse) cell (default 2).
        browse_modes: which browse states to probe (default [True, False]).
        endpoint: DFS LLM-response endpoint. Availability is plan-gated; the
            probe degrades gracefully (returns disclosed, empty aggregate) on
            403/404 rather than raising.
        max_keywords: hard cap on keywords probed (paid endpoint).

    Returns:
        dict with 'aggregate' (see :func:`aggregate_llm_probes`), 'probes'
        (raw records), and probe configuration for traceability.
    """
    models = models or ["chatgpt"]
    browse_modes = browse_modes if browse_modes is not None else [True, False]
    samples = max(1, samples)
    probe_keywords = keywords[:max_keywords]

    planned = len(models) * len(probe_keywords) * len(browse_modes) * samples
    if planned > MAX_LLM_PROBE_CALLS:
        logger.warning(
            "LLM probe plan (%d calls) exceeds cap %d — trimming keyword set.",
            planned, MAX_LLM_PROBE_CALLS,
        )
        per_kw = max(1, len(models) * len(browse_modes) * samples)
        probe_keywords = probe_keywords[: max(1, MAX_LLM_PROBE_CALLS // per_kw)]

    probes: list = []
    plan_unavailable = False
    for model in models:
        for keyword in probe_keywords:
            for browse in browse_modes:
                if plan_unavailable:
                    break
                for _ in range(samples):
                    record = _probe_llm_once(brand, keyword, model, browse, headers, endpoint)
                    probes.append(record)
                    # If the plan doesn't expose the endpoint, stop hammering it
                    # after the first sample — one disclosed error is enough.
                    if record["error"] and "not available" in record["error"]:
                        plan_unavailable = True
                        break

    aggregate = aggregate_llm_probes(probes)
    if plan_unavailable:
        aggregate["error"] = "LLM Mentions/Response API not available on current DataForSEO plan"

    return {
        "brand": brand,
        "config": {
            "models": models,
            "samples_per_cell": samples,
            "browse_modes": browse_modes,
            "keywords_probed": probe_keywords,
            "endpoint": endpoint,
        },
        "aggregate": aggregate,
        "probes": probes,
    }


def run(client_name: str) -> dict:
    config_path = PROJECT_ROOT / "Clients" / client_name / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    dfs_login = os.environ.get("DATAFORSEO_LOGIN")
    dfs_password = os.environ.get("DATAFORSEO_PASSWORD")
    if not dfs_login or not dfs_password:
        raise EnvironmentError("DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD must be set in .env")

    headers = get_auth(dfs_login, dfs_password)
    keywords = config.get("target_keywords", [])
    location_code = config.get("location_code", 2840)
    language_code = config.get("language_code", "en")
    domain = config["domain"]
    competitors = config.get("competitors", [])
    brand = config["brand_terms"][0] if config.get("brand_terms") else domain.split(".")[0]

    output_dir = PROJECT_ROOT / "Clients" / client_name / "data" / "ai-visibility"
    output_dir.mkdir(parents=True, exist_ok=True)

    # AI Overview check
    print(f"  Checking AI Overviews for {len(keywords)} keywords...")
    ai_results = check_ai_overviews(keywords, location_code, language_code, headers)
    ai_file = output_dir / "ai_overviews.json"
    with open(ai_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "domain": domain, "results": ai_results}, f, indent=2)
    ai_count = sum(1 for r in ai_results if r["ai_overview_present"])
    print(f"    {ai_count}/{len(ai_results)} keywords have AI Overviews → {ai_file.name}")

    # Competitor share of voice (pure aggregation over the citation data above)
    print(f"  Computing share of voice vs {len(competitors)} competitors...")
    sov = compute_share_of_voice(ai_results, domain, competitors)
    sov_file = output_dir / "share_of_voice.json"
    with open(sov_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "domain": domain, "share_of_voice": sov}, f, indent=2)
    print(
        f"    Client cited in {sov['client_citations']}/{sov['total_citations']} AI citations "
        f"({sov['client_share_of_voice_pct']}% SoV) → {sov_file.name}"
    )

    # LLM mentions check (sampled, multi-model, browse-disclosed)
    print(f"  Probing LLM mentions for brand '{brand}' (sampled)...")
    llm_results = check_llm_mentions(brand, keywords, headers)
    llm_file = output_dir / "llm_mentions.json"
    with open(llm_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "brand": brand, "data": llm_results}, f, indent=2)
    overall_rate = llm_results["aggregate"]["overall_mention_rate"]
    print(f"    LLM mention rate {overall_rate} over {llm_results['aggregate']['total_valid_samples']} valid samples → {llm_file.name}")

    return {
        "ai_overviews_checked": len(ai_results),
        "ai_overviews_found": ai_count,
        "client_share_of_voice_pct": sov["client_share_of_voice_pct"],
        "competitors_tracked": len(competitors),
        "llm_overall_mention_rate": overall_rate,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check AI visibility for a client")
    parser.add_argument("--client", required=True, help="Client folder name (e.g. educationwalkthrough.com)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    result = run(args.client)
    print(f"\nAI visibility fetch complete: {result}")
