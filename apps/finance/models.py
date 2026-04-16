from django.db import models
from django.db import transaction
from apps.students.models import Student
from apps.accounts.models import User
from apps.groups.models import Course, Group


class Payment(models.Model):
    INCOME   = 'income'
    REFUND   = 'refund'
    DISCOUNT = 'discount'
    TYPES = [
        (INCOME,   'Kirim'),
        (REFUND,   'Qaytarish'),
        (DISCOUNT, 'Chegirma'),
    ]
    METHOD_CASH = 'cash'
    METHOD_TRANSFER = 'transfer'
    METHOD_TERMINAL = 'terminal'
    METHODS = [
        (METHOD_CASH, "Naqd pul"),
        (METHOD_TRANSFER, "O'tkazish"),
        (METHOD_TERMINAL, "Terminal / karta"),
    ]

    student      = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    course       = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Fan / kurs',
    )
    group        = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Yo`nalish / guruh',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=METHODS,
        default=METHOD_CASH,
        verbose_name="To'lov usuli",
    )
    payment_type = models.CharField(max_length=20, choices=TYPES, default=INCOME)
    amount       = models.DecimalField(max_digits=14, decimal_places=0)
    note         = models.CharField(max_length=300, blank=True)
    received_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_payments')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} | {self.get_payment_type_display()} | {self.amount}"

    @staticmethod
    def _apply_balance(student_id, payment_type, amount, reverse=False):
        """Balance delta: income +amount, refund/discount -amount."""
        sign = 1 if payment_type == Payment.INCOME else -1
        if reverse:
            sign *= -1
        Student.objects.filter(pk=student_id).update(
            balance=models.F('balance') + (sign * amount)
        )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            old = None
            if self.pk:
                old = Payment.objects.select_for_update().get(pk=self.pk)
            super().save(*args, **kwargs)
            if old:
                self._apply_balance(old.student_id, old.payment_type, old.amount, reverse=True)
            self._apply_balance(self.student_id, self.payment_type, self.amount)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self._apply_balance(self.student_id, self.payment_type, self.amount, reverse=True)
            super().delete(*args, **kwargs)
