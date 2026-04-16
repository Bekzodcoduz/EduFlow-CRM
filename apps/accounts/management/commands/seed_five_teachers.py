"""5 ta o'qituvchi va har biriga 5 tadan turli talaba (guruh + Course)."""

from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.groups.models import Course, Group, Room
from apps.students.models import Student


TEACHERS = [
    ('Zaynab', 'Karimova', 'Matematika'),
    ('Timur', 'Abdullayev', 'Fizika'),
    ('Madina', 'Rahimova', 'Ingliz tili'),
    ('Bekzod', 'Mirzayev', 'Kimyo'),
    ('Shahlo', 'Tursunova', 'Ona tili'),
]

# Har bir o'qituvchi uchun 5 tadan, jami 25 ta boshqa-boshqa talaba
STUDENTS_PER_TEACHER = [
    [
        ('Aziz', 'Norboyev'),
        ('Sarvinoz', 'Otajonova'),
        ('Jasurbek', 'Qo\'chqorov'),
        ('Nilufar', 'Yuldasheva'),
        ('Otabek', 'Rahimjonov'),
    ],
    [
        ('Dilshod', 'Toshmatov'),
        ('Gulnora', 'Abduraxmonova'),
        ('Shohjahon', 'Ergashev'),
        ('Madina', 'Karimova'),
        ('Behzod', 'Saidov'),
    ],
    [
        ('Laziza', 'Hamidova'),
        ('Doniyor', 'Mirzayev'),
        ('Shirin', 'Po\'latova'),
        ('Ulug\'bek', 'Nazarov'),
        ('Feruza', 'Tursunova'),
    ],
    [
        ('Kamron', 'Yusupov'),
        ('Nargiza', 'Ismoilova'),
        ('Bunyod', 'Xolmatov'),
        ('Zilola', 'Raximova'),
        ('Javlon', 'Sobirov'),
    ],
    [
        ('Sevinch', 'Alimova'),
        ('Mirjalol', 'Qodirov'),
        ('Ruxsora', 'Ergasheva'),
        ('Temur', 'Hamroyev'),
        ('Dilorom', 'Nabiyeva'),
    ],
]

MAHALLALAR = [
    '9-mavze',
    'Olmazar',
    'Chilonzor',
    'Qorasaroy',
    'Yangi hayot',
    'Sharx',
    'Mustaqillik',
    'Navro\'z',
    'Bog\'ishamol',
    'Yunusobod',
]


class Command(BaseCommand):
    help = "5 ta o'qituvchi va har biriga 5 tadan turli talaba (get_or_create, takrorlash xavfsiz)."

    def handle(self, *args, **options):
        # Eski seed: "Demo:" prefiksini olib tashlash
        for g in Group.objects.filter(name__startswith='Demo: '):
            g.name = g.name[6:].lstrip()
            g.save(update_fields=['name'])

        room = Room.objects.order_by('pk').first()
        if not room:
            room = Room.objects.create(name='A1', capacity=25)
            self.stdout.write(self.style.WARNING('  Yangi xona yaratildi: A1'))

        st = time(9, 0)
        et = time(10, 30)
        sd = date.today()
        ed = sd + timedelta(days=200)
        reg, dist = 'Toshkent shahar', 'Yunusobod tumani'

        phone_n = 0
        for idx, (fn, ln, subject) in enumerate(TEACHERS, start=1):
            uname = f"eduflow_oq_{idx}"
            teacher, t_created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'first_name': fn,
                    'last_name': ln,
                    'role': User.TEACHER,
                    'subject': subject,
                    'salary': 5_000_000,
                    'experience': 2,
                },
            )
            if not t_created:
                teacher.first_name = fn
                teacher.last_name = ln
                teacher.role = User.TEACHER
                teacher.subject = subject
                teacher.save()
            teacher.set_password('teach123')
            teacher.save()

            course, _ = Course.objects.get_or_create(
                name=subject,
                defaults={'price': 300_000},
            )
            gname = f"{subject} - {ln} guruhi"
            group, g_created = Group.objects.get_or_create(
                name=gname,
                defaults={
                    'course': course,
                    'teacher': teacher,
                    'room': room,
                    'days': Group.EVEN,
                    'start_time': st,
                    'end_time': et,
                    'start_date': sd,
                    'end_date': ed,
                    'price': course.price,
                    'is_active': True,
                },
            )
            if not g_created:
                group.course = course
                group.teacher = teacher
                group.room = room
                group.save()

            self.stdout.write(self.style.SUCCESS(f"  [OK] O'qituvchi: {teacher.full_name} ({uname} / teach123)"))
            self.stdout.write(f"      Guruh: {group.name}")

            names_for_teacher = STUDENTS_PER_TEACHER[idx - 1]
            for s_i, (sfn, sln) in enumerate(names_for_teacher, start=1):
                phone_n += 1
                phone = f"+9989013{phone_n:04d}"
                mahalla = MAHALLALAR[(phone_n - 1) % len(MAHALLALAR)]
                s, s_created = Student.objects.get_or_create(
                    phone=phone,
                    defaults={
                        'first_name': sfn,
                        'last_name': sln,
                        'group': group,
                        'balance': 0,
                        'region': reg,
                        'district': dist,
                        'mahalla': mahalla,
                        'street': f"{s_i}-ko'cha",
                        'house': str(s_i + idx),
                    },
                )
                if s_created:
                    self.stdout.write(f"      + Talaba: {s.full_name} ({phone})")
                else:
                    s.first_name = sfn
                    s.last_name = sln
                    s.group = group
                    s.mahalla = mahalla
                    s.save()

        # Eski talabalarda "Demo mahalla" qolgan bo'lsa
        Student.objects.filter(mahalla__startswith='Demo mahalla').update(mahalla='Yunusobod')

        self.stdout.write(self.style.SUCCESS("\nTayyor: 5 o'qituvchi, har biriga 5 turli talaba (jami 25)."))
        self.stdout.write("  Barcha o'qituvchilar paroli: teach123")
        self.stdout.write("  Loginlar: eduflow_oq_1 ... eduflow_oq_5")
