"""Semantic Site Map skill — embeds pages, clusters them, overlays GSC clicks."""

from Skills.semantic_site_map.text_loader import load_page_text
from Skills.semantic_site_map.embedder import embed_pages
from Skills.semantic_site_map.cluster import cluster_pages
from Skills.semantic_site_map.report import build_outputs

__all__ = ["load_page_text", "embed_pages", "cluster_pages", "build_outputs"]
