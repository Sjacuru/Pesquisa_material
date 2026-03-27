# Generated seed migration — adds Amazon BR and Magazine Luiza source sites.
from django.db import migrations


def seed_new_sites(apps, schema_editor):
    SourceSite = apps.get_model("persistence", "SourceSite")
    sites = [
        {
            "site_id": "amazon_br",
            "label": "Amazon Brasil",
            "trust_status": "allowed",
            "integration_type": "scraping",
            "categories": ["book", "dictionary", "apostila", "notebook", "general supplies"],
            "is_search_eligible": True,
        },
        {
            "site_id": "magalu_br",
            "label": "Magazine Luiza",
            "trust_status": "allowed",
            "integration_type": "scraping",
            "categories": ["notebook", "general supplies", "book"],
            "is_search_eligible": True,
        },
    ]
    for site_data in sites:
        SourceSite.objects.update_or_create(
            site_id=site_data["site_id"],
            defaults=site_data,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("persistence", "0003_seed_source_sites"),
    ]

    operations = [
        migrations.RunPython(seed_new_sites, migrations.RunPython.noop),
    ]
