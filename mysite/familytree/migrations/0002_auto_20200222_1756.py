# Generated by Django 3.0.3 on 2020-02-22 17:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('familytree', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='family',
            name='partner1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partner1', to='familytree.Person'),
        ),
        migrations.AlterField(
            model_name='family',
            name='partner2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partner2', to='familytree.Person'),
        ),
        migrations.AlterField(
            model_name='person',
            name='origin_family',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='familytree.Family'),
        ),
    ]
