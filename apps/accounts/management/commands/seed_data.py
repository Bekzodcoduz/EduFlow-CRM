from django.core.management.base import BaseCommand
from datetime import date, datetime, time, timedelta


class Command(BaseCommand):
    help = "EduFlow demo ma'lumotlar"

    def handle(self, *args, **kwargs):
        from apps.accounts.models import User
        from apps.groups.models import Course, Room, Group
        from apps.students.models import Student
        from apps.finance.models import Payment

        self.stdout.write("🌱 Demo ma'lumotlar yuklanmoqda...")

        admin, _ = User.objects.get_or_create(username='admin', defaults={
            'first_name':'Admin','last_name':'Foydalanuvchi',
            'role':'admin','is_staff':True,'is_superuser':True,
        })
        admin.set_password('admin123'); admin.save()
        self.stdout.write(self.style.SUCCESS("  ✓ admin / admin123"))

        t1, _ = User.objects.get_or_create(username='sardor', defaults={
            'first_name':'Sardor','last_name':'Qodirov',
            'role':'teacher','subject':'Ingliz tili','salary':8400000,'experience':3,
        })
        t1.set_password('teach123'); t1.save()
        self.stdout.write(self.style.SUCCESS("  ✓ sardor / teach123"))

        t2, _ = User.objects.get_or_create(username='dilnoza', defaults={
            'first_name':'Dilnoza','last_name':'Yusupova',
            'role':'teacher','subject':'Matematika','salary':7200000,'experience':5,
        })
        t2.set_password('teach123'); t2.save()
        self.stdout.write(self.style.SUCCESS("  ✓ dilnoza / teach123"))

        courses = {}
        for name, price in [('Ingliz tili',300000),('Matematika',280000),
                              ('Arab tili',320000),('Koreys tili',350000),
                              ('Mental arifmetika',400000),('Fizika',300000)]:
            c,_ = Course.objects.get_or_create(name=name, defaults={'price':price})
            courses[name] = c

        rooms = {}
        for name in ['N1','N2','London','New York','Zoom','Big Room']:
            r,_ = Room.objects.get_or_create(name=name, defaults={'capacity':15})
            rooms[name] = r

        groups = {}
        gdata = [
            ('English A1','Ingliz tili',t1,'N1','even',time(9,0),date(2024,1,1),date(2024,7,1)),
            ('English B2','Ingliz tili',t1,'London','odd',time(11,0),date(2024,2,1),date(2024,8,1)),
            ('Matematika 7-sinf','Matematika',t2,'N2','even',time(14,0),date(2024,1,15),date(2024,7,15)),
            ('Arab tili A','Arab tili',None,'New York','odd',time(16,0),date(2024,3,1),date(2024,9,1)),
            ('Mental A12','Mental arifmetika',None,'N1','even',time(10,0),date(2024,2,1),date(2024,8,1)),
        ]
        for name,course,teacher,room,days,stime,sdate,edate in gdata:
            etime = (datetime.combine(sdate, stime) + timedelta(hours=1)).time()
            g,cr = Group.objects.get_or_create(name=name, defaults={
                'course':courses[course],'teacher':teacher,
                'room':rooms[room],'days':days,
                'start_time':stime,'end_time':etime,'start_date':sdate,'end_date':edate,
                'price':courses[course].price,
            })
            groups[name] = g
            if cr: self.stdout.write(f"  ✓ Guruh: {name}")

        sdata = [
            ('Islom','Karimov','+998 90 100 00 01','English A1',-320000,
             'Toshkent shahar','Yunusobod tumani','9-mavze',"Navruz ko'chasi",'12','4','2','100093'),
            ('Zulfiya','Toshmatova','+998 90 100 00 02','English A1',0,
             'Toshkent viloyati','Chirchiq shahri','Tinchlik',"Mustaqillik ko'chasi",'45','','','111700'),
            ('Jasur','Ergashev','+998 90 100 00 03','English B2',300000,
             'Toshkent shahar',"Mirzo Ulug'bek tumani",'Olmazar',"Amir Temur shoh ko'chasi",'88','12','4','100140'),
            ('Malika','Yuldosheva','+998 90 100 00 04','English B2',0,
             'Toshkent shahar','Chilonzor tumani','Qorasaroy',"Ko'lmas ko'chasi",'3','7','3','100021'),
            ('Sardor','Mirzayev','+998 90 100 00 05','Matematika 7-sinf',0,
             'Samarqand viloyati','Samarqand shahri','Registon',"Registon ko'chasi",'21','','','140100'),
            ('Nodira','Hasanova','+998 90 100 00 06','Matematika 7-sinf',-150000,
             'Toshkent shahar','Shayxontohur tumani','Eski shahar',"Hamza ko'chasi",'7','2','1','100017'),
            ('Bobur','Rahimov','+998 90 100 00 07','Arab tili A',0,
             "Farg'ona viloyati","Farg'ona shahri","Navro'z","Al-Farg'oniy ko'chasi",'55','','','150100'),
            ('Kamola','Nazarova','+998 90 100 00 08','Arab tili A',0,
             'Andijon viloyati','Andijon shahri','Yangi hayot',"Navoi ko'chasi",'19','3','2','170100'),
            ('Ulugbek','Sotvoldiev','+998 90 100 00 09','Mental A12',0,
             'Namangan viloyati','Namangan shahri','Shark',"Hamid Olimjon ko'chasi",'33','','','160100'),
            ('Feruza','Qosimova','+998 90 100 00 10','Mental A12',-50000,
             'Toshkent shahar','Bektemir tumani','Yangi hayot',"Yangi ko'cha",'8','5','2','100201'),
        ]
        for fn,ln,phone,grp,bal,reg,dist,mah,str_,house,apt,flr,postal in sdata:
            s,cr = Student.objects.get_or_create(first_name=fn, last_name=ln, defaults={
                'phone':phone,'group':groups.get(grp),'balance':bal,
                'region':reg,'district':dist,'mahalla':mah,'street':str_,
                'house':house,'apartment':apt,'floor':flr,'postal_code':postal,
            })
            if cr: self.stdout.write(f"  ✓ Talaba: {fn} {ln}")

        if Payment.objects.count() == 0:
            for s in Student.objects.all()[:6]:
                Payment.objects.create(
                    student=s, payment_type='income',
                    amount=300000, note="Demo to'lov", received_by=admin
                )
            self.stdout.write(self.style.SUCCESS("  ✓ Demo to'lovlar"))

        self.stdout.write(self.style.SUCCESS("\n✅ Tayyor!"))
        self.stdout.write("  admin / admin123\n  sardor / teach123\n  dilnoza / teach123")
