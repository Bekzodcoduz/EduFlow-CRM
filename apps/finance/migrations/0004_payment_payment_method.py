from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_payment_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('cash', "Naqd pul"),
                    ('transfer', "O'tkazish"),
                    ('terminal', 'Terminal / karta'),
                ],
                default='cash',
                max_length=20,
                verbose_name="To'lov usuli",
            ),
        ),
    ]
