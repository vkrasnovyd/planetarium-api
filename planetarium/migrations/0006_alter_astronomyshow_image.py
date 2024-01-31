# Generated by Django 4.2 on 2024-01-31 19:16

from django.db import migrations, models
import planetarium.models


class Migration(migrations.Migration):
    dependencies = [
        ("planetarium", "0005_alter_astronomyshow_show_theme"),
    ]

    operations = [
        migrations.AlterField(
            model_name="astronomyshow",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=planetarium.models.astronomy_show_image_file_path,
            ),
        ),
    ]
