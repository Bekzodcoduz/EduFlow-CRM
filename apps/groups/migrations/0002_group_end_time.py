import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='end_time',
            field=models.TimeField(default=datetime.time(10, 0)),
        ),
    ]
