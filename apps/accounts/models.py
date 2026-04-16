from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN   = 'admin'
    TEACHER = 'teacher'
    ROLES = [(ADMIN, 'Administrator'), (TEACHER, "O'qituvchi")]

    role    = models.CharField(max_length=20, choices=ROLES, default=ADMIN)
    phone   = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    salary  = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    experience = models.PositiveIntegerField(default=0, help_text="Yillar")
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @classmethod
    def teachers_for_select(cls):
        """Guruh / forma tanlovi: barcha o'qituvchi rolli foydalanuvchilar (tartiblangan)."""
        return cls.objects.filter(role=cls.TEACHER).order_by('last_name', 'first_name', 'username')

    @property
    def initials(self):
        name = self.get_full_name() or self.username
        return ''.join(p[0].upper() for p in name.split()[:2])

    @property
    def full_name(self):
        return self.get_full_name() or self.username
