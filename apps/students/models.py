from django.db import models
from apps.groups.models import Group


class Student(models.Model):
    # Shaxsiy
    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name  = models.CharField(max_length=100, verbose_name='Familiya')
    phone      = models.CharField(max_length=20,  verbose_name='Telefon')
    parent_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Ota yoki ona telefoni (SMS)",
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Tug'ilgan sana")
    gender     = models.CharField(max_length=10, blank=True, choices=[('male','Erkak'),('female','Ayol')])
    email      = models.EmailField(blank=True)

    # Manzil — to'liq
    region     = models.CharField(max_length=100, blank=True, verbose_name='Viloyat')
    district   = models.CharField(max_length=100, blank=True, verbose_name='Tuman/Shahar')
    mahalla    = models.CharField(max_length=100, blank=True, verbose_name='Mahalla')
    street     = models.CharField(max_length=150, blank=True, verbose_name="Ko'cha")
    house      = models.CharField(max_length=20,  blank=True, verbose_name='Uy raqami')
    apartment  = models.CharField(max_length=20,  blank=True, verbose_name='Kvartira')
    floor      = models.CharField(max_length=10,  blank=True, verbose_name='Qavat')
    postal_code= models.CharField(max_length=10,  blank=True, verbose_name='Pochta indeksi')
    address_note = models.TextField(blank=True,   verbose_name="Qo'shimcha yo'nalish")

    # O'quv
    group      = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='students', verbose_name='Guruh')
    balance    = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Balans')
    is_active  = models.BooleanField(default=True, verbose_name='Faol')
    note       = models.TextField(blank=True, verbose_name='Izoh')
    enrolled_at = models.DateField(null=True, blank=True, verbose_name='Qabul sanasi')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Talaba'
        verbose_name_plural = 'Talabalar'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        parts = [self.region, self.district, self.mahalla, self.street,
                 f"uy {self.house}" if self.house else '',
                 f"kv. {self.apartment}" if self.apartment else '']
        return ', '.join(p for p in parts if p)

    @property
    def short_address(self):
        parts = [self.region, self.district]
        return ', '.join(p for p in parts if p) or 'Manzil kiritilmagan'

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()


class Attendance(models.Model):
    student         = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date            = models.DateField()
    is_present      = models.BooleanField(default=False)
    note            = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Davomat'
        verbose_name_plural = 'Davomat'
        unique_together = ['student', 'date']
        ordering = ['-date']

    def __str__(self):
        tag = 'keldi' if self.is_present else 'kelmadi'
        return f'{self.student} | {self.date} | {tag}'
