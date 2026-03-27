# Generated seed migration — inserts the 3 primary source sites.
from django.db import migrations


def seed_source_sites(apps, schema_editor):
	SourceSite = apps.get_model("persistence", "SourceSite")
	sites = [
		{
			"site_id": "ml_br",
			"label": "Mercado Livre",
			"trust_status": "allowed",
			"integration_type": "api",
			"categories": ["book", "dictionary", "apostila", "notebook", "general supplies"],
			"is_search_eligible": True,
		},
		{
			"site_id": "ev_br",
			"label": "Estante Virtual",
			"trust_status": "allowed",
			"integration_type": "scraping",
			"categories": ["book", "dictionary"],
			"is_search_eligible": True,
		},
		{
			"site_id": "kalunga_br",
			"label": "Kalunga",
			"trust_status": "allowed",
			"integration_type": "scraping",
			"categories": ["notebook", "general supplies", "apostila"],
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
		(
			"persistence",
			"0002_offer_searchexecution_workflowstate_sourcesite_fields",
		),
	]

	operations = [
		migrations.RunPython(seed_source_sites, migrations.RunPython.noop),
	]
