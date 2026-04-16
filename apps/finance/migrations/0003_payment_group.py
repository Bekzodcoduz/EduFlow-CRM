from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_payment_course'),
        ('groups', '0002_group_end_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='group',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments',
                to='groups.group',
                verbose_name='Yo`nalish / guruh',
            ),
        ),
    ]
