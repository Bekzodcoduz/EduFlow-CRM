from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='excused_absence',
            field=models.BooleanField(
                default=False,
                help_text=(
                    "True bo'lsa: o'quvchi kelmagan, lekin asosli sabab + ustoz roziligi bor — "
                    "shu kun uchun to'lov hisoblanadi. False va kelmagan bo'lsa — to'lov tortilmaydi."
                ),
                verbose_name="Uzr bilan kelmagan (ustoz tasdig'i)",
            ),
        ),
    ]
