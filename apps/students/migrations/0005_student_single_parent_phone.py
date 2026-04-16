from django.db import migrations, models


def merge_parent_phones(apps, schema_editor):
    Student = apps.get_model('students', 'Student')
    for s in Student.objects.all():
        father = (getattr(s, 'father_phone', None) or '').strip()
        mother = (getattr(s, 'mother_phone', None) or '').strip()
        s.parent_phone = father or mother
        s.save(update_fields=['parent_phone'])


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0004_alter_attendance_excused_absence'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='parent_phone',
            field=models.CharField(blank=True, max_length=20, verbose_name='Ota yoki ona telefoni (SMS)'),
        ),
        migrations.RunPython(merge_parent_phones, migrations.RunPython.noop),
        migrations.RemoveField(model_name='student', name='father_phone'),
        migrations.RemoveField(model_name='student', name='mother_phone'),
    ]
