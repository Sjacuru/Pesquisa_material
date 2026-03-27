from __future__ import annotations

import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from persistence.models import SourceSite  # noqa: E402


SITES = [
    {
        "site_id": "amazon_br",
        "label": "Amazon Brasil",
        "trust_status": SourceSite.TrustStatus.ALLOWED,
        "integration_type": SourceSite.IntegrationType.SCRAPING,
        "categories": ["book", "dictionary", "apostila", "notebook", "general supplies"],
        "is_search_eligible": True,
    },
    {
        "site_id": "magalu_br",
        "label": "Magazine Luiza",
        "trust_status": SourceSite.TrustStatus.ALLOWED,
        "integration_type": SourceSite.IntegrationType.SCRAPING,
        "categories": ["book", "dictionary", "apostila", "notebook", "general supplies"],
        "is_search_eligible": True,
    },
    {
        "site_id": "ev_br",
        "label": "Estante Virtual",
        "trust_status": SourceSite.TrustStatus.ALLOWED,
        "integration_type": SourceSite.IntegrationType.SCRAPING,
        "categories": ["book", "dictionary", "apostila"],
        "is_search_eligible": True,
    },
    {
        "site_id": "kalunga_br",
        "label": "Kalunga",
        "trust_status": SourceSite.TrustStatus.ALLOWED,
        "integration_type": SourceSite.IntegrationType.SCRAPING,
        "categories": ["apostila", "notebook", "general supplies"],
        "is_search_eligible": True,
    },
    {
        "site_id": "ml_br",
        "label": "Mercado Livre",
        "trust_status": SourceSite.TrustStatus.ALLOWED,
        "integration_type": SourceSite.IntegrationType.SCRAPING,
        "categories": ["book", "dictionary", "apostila", "notebook", "general supplies"],
        "is_search_eligible": True,
    },
]


def seed() -> None:
    for site in SITES:
        SourceSite.objects.update_or_create(site_id=site["site_id"], defaults=site)
    print(f"Seeded {len(SITES)} staging source sites.")


if __name__ == "__main__":
    seed()
