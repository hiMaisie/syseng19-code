# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-13 16:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('match', '0002_auto_20170213_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='tags',
            field=models.ManyToManyField(related_name='UserTag', to='match.Tag'),
        ),
    ]