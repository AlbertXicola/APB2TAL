# Generated by Django 4.1.13 on 2024-05-14 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archivos', '0004_remove_compartido_group_remove_compartido_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='archivo',
            name='tamaño',
            field=models.CharField(default=False, max_length=255),
        ),
    ]
