"""Semantic Site Map skill.

Embeds pages, clusters them, overlays GSC clicks.

Public API:
    load_page_text  - hybrid SF/Crawl4AI text source (text_loader)
    embed_pages     - OpenRouter embeddings + parquet cache (embedder)
    cluster_pages   - HDBSCAN + LLM cluster labels (cluster)
    build_outputs   - 4 output files + scatter PNG (report)

Imports are done lazily inside each accessor so a partial install
(e.g. during TDD scaffolding, or when only one module is needed)
does not eagerly fail.
"""

__all__ = [
    "load_page_text",
    "embed_pages",
    "cluster_pages",
    "build_outputs",
]


def __getattr__(name: str):
    if name == "load_page_text":
        from Skills.semantic_site_map.text_loader import load_page_text
        return load_page_text
    if name == "embed_pages":
        from Skills.semantic_site_map.embedder import embed_pages
        return embed_pages
    if name == "cluster_pages":
        from Skills.semantic_site_map.cluster import cluster_pages
        return cluster_pages
    if name == "build_outputs":
        from Skills.semantic_site_map.report import build_outputs
        return build_outputs
    raise AttributeError(
        f"module 'Skills.semantic_site_map' has no attribute {name!r}"
    )
