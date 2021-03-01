# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-12-08 21:06
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    # FIXME: Ummmm, maybe come up with a better way to handle the dependency below?
    dependencies = [
            ('db', '0002_auto_20201209_1934'),
            ]

    operations = [
            migrations.RunSQL(
        """
create table aoi_timepoints_indexed as
select aoi_timepoints.*,
	(row_number() over (partition by administration_id, trial_id order by t_norm) -
	 row_number() over (partition by administration_id, trial_id, aoi order by t_norm)
	) as grp
from aoi_timepoints;
create table aoi_timepoints_rle as
select administration_id, trial_id, min(t_norm) as t_norm, aoi, count(*) as length
from aoi_timepoints_indexed
group by administration_id, trial_id, aoi, grp
order by administration_id, trial_id, t_norm;
                """
        ),
            ]


