from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_student_single_parent_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='excused_absence',
        ),
    ]
