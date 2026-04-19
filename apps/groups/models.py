from datetime import date, time

from django.db import models
from apps.accounts.models import User


class Course(models.Model):
    name  = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=0, default=300000)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Room(models.Model):
    name     = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=20)

    class Meta:
        verbose_name = 'Xona'
        verbose_name_plural = 'Xonalar'

    def __str__(self):
        return self.name


class Group(models.Model):
    EVEN  = 'even'
    ODD   = 'odd'
    DAILY = 'daily'
    DAYS_CHOICES = [
        (EVEN,  'Juft kunlar (Sesh, Pay, Shan)'),
        (ODD,   'Toq kunlar (Dush, Chor, Jum)'),
        (DAILY, 'Har kuni'),
    ]

    name       = models.CharField(max_length=150)
    course     = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='groups')
    teacher    = models.ForeignKey(User,   on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_groups')
    room       = models.ForeignKey(Room,   on_delete=models.SET_NULL, null=True, blank=True, related_name='groups')
    days       = models.CharField(max_length=10, choices=DAYS_CHOICES, default=EVEN)
    start_time = models.TimeField()
    end_time   = models.TimeField(default=time(10, 0))
    start_date = models.DateField()
    end_date   = models.DateField()
    price      = models.DecimalField(max_digits=12, decimal_places=0, default=300000)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Guruh'
        verbose_name_plural = 'Guruhlar'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()

    @property
    def days_label(self):
        return dict(self.DAYS_CHOICES).get(self.days, self.days)

    def is_scheduled_calendar_day(self, d: date) -> bool:
        """Kalendar sanasi guruhning hafta jadvaliga tushadimi (juft / toq / har kuni)."""
        if self.days == self.DAILY:
            return True
        wd = d.weekday()
        if self.days == self.ODD:
            return wd in (0, 2, 4)
        if self.days == self.EVEN:
            return wd in (1, 3, 5)
        return True
