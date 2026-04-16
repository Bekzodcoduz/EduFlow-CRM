from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_attendance_excused_absence'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='father_phone',
            field=models.CharField(blank=True, max_length=20, verbose_name="Otasining telefoni (SMS)"),
        ),
        migrations.AddField(
            model_name='student',
            name='mother_phone',
            field=models.CharField(blank=True, max_length=20, verbose_name="Onasining telefoni (SMS)"),
        ),
    ]
