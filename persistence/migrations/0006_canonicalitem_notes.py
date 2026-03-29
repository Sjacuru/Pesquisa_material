from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("persistence", "0005_jobqueueentry_jobexecutionlog_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="canonicalitem",
            name="notes",
            field=models.TextField(blank=True, default=""),
        ),
    ]
