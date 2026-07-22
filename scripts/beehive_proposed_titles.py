"""Proposed title rewrites for the 17 Beehive local pages.

Rules applied:
- Brand suffix is " | Beehive Plumbing" — excluded from 65-char count.
- City named once. Service root ("plumb") named once in visible portion.
  Brand suffix carries the second "plumbing" — that's structurally allowed
  because the visible title ends before the pipe, but the visible portion
  itself must NOT contain "plumber" or "plumbing".
- Lead with primary user query, follow with services + city.
- Use headroom to add ONE differentiating service or trust signal.
- Read aloud before submitting.
"""
from typing import NamedTuple


class TitleProposal(NamedTuple):
    city: str
    url: str
    visible_title: str
    brand_suffix: str = " | Beehive Plumbing"

    @property
    def full_title(self) -> str:
        return self.visible_title + self.brand_suffix

    @property
    def visible_chars(self) -> int:
        return len(self.visible_title)

    @property
    def full_chars(self) -> int:
        return len(self.full_title)


# Visible-portion patterns lead with the city + primary service noun
# alternative ("Drain, Water Heater & Sewer Repair" instead of "Plumbing").
# Service emphasis is per-city per the differentiation framework.
PROPOSALS = [
    # Tier A
    TitleProposal(
        "Park City",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-park-city/",
        "Park City, UT Drain, Water Heater & Emergency Repair",
    ),
    TitleProposal(
        "Murray",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-murray/",
        "Murray, UT Sewer, Repipe & Drain Repair Services",
    ),
    TitleProposal(
        "Bountiful",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-bountiful/",
        "Bountiful, UT Water Heater, Softener & Drain Services",
    ),
    TitleProposal(
        "Lehi",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-lehi/",
        "Lehi, UT New Construction, Water Heater & Drain Services",
    ),
    TitleProposal(
        "Orem",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-orem/",
        "Orem, UT Water Heater, Repipe & Drain Repair Services",
    ),
    # Tier B
    TitleProposal(
        "Sugar House",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-sugar-house/",
        "Sugar House, UT Repipe, Leak Detection & Drain Repair",
    ),
    TitleProposal(
        "Draper",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-draper/",
        "Draper, UT Tankless Water Heater & Softener Services",
    ),
    TitleProposal(
        "West Jordan",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-west-jordan/",
        "West Jordan, UT Drain, Water Heater & Sewer Repair",
    ),
    TitleProposal(
        "Kaysville",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-kaysville/",
        "Kaysville, UT Water Heater, Softener & Drain Services",
    ),
    TitleProposal(
        "Midvale",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-midvale/",
        "Midvale, UT Drain, Repipe & Leak Detection Services",
    ),
    TitleProposal(
        "Bluffdale",
        "https://www.beehiveplumbing.com/locations/bluffdale/",
        "Bluffdale, UT New Construction, Softener & Water Heater",
    ),
    TitleProposal(
        "West Valley City",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-west-valley-city/",
        "West Valley, UT Drain, Sewer & Commercial Repair Services",
    ),
    TitleProposal(
        "Salt Lake City - Sugar House",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-salt-lake-city-sugar-house/",
        "REDIRECT - duplicate of Sugar House (do not rewrite)",
    ),
    TitleProposal(
        "Millcreek",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-millcreek/",
        "Millcreek, UT Repipe, Water Heater & Drain Services",
    ),
    TitleProposal(
        "Sandy",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-sandy/",
        "Sandy, UT Water Heater, Softener & Drain Repair Services",
    ),
    TitleProposal(
        "Salt Lake City (root)",
        "https://www.beehiveplumbing.com/locations/salt-lake-city/",
        "Salt Lake City, UT Drain, Sewer & Water Heater Services",
    ),
    TitleProposal(
        "South Jordan",
        "https://www.beehiveplumbing.com/locations/beehive-plumbing-south-jordan/",
        "South Jordan, UT New Construction, Water Heater & Softener",
    ),
]


def report() -> None:
    print(f"{'City':<32} {'Vis chars':>9} {'Full chars':>10}  Visible Title  ||  Brand Suffix")
    print("-" * 140)
    for p in PROPOSALS:
        flag = ""
        if "REDIRECT" in p.visible_title:
            flag = "  [SKIP - 301 redirect candidate]"
        elif p.visible_chars > 65:
            flag = "  [OVER 65]"
        print(f"{p.city:<32} {p.visible_chars:>9} {p.full_chars:>10}  {p.visible_title}{flag}")


if __name__ == "__main__":
    report()
