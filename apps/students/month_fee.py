"""Joriy oy uchun oylik to'lov (guruh narxi) va kirimlar solishtirish."""

from __future__ import annotations

import calendar

from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import Payment


def current_calendar_month_bounds(today=None):
    if today is None:
        today = timezone.localdate()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    return month_start, month_end, today


def month_bounds_for_calendar_month(year: int, month: int):
    """Berilgan yil/oy uchun (birinchi va oxirgi sana)."""
    from datetime import date

    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def month_income_totals_by_student(student_ids, month_start, month_end):
    """Talaba ID -> shu oy ichidagi kirim (income) summasi."""
    if not student_ids:
        return {}
    rows = (
        Payment.objects.filter(
            payment_type=Payment.INCOME,
            student_id__in=list(student_ids),
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
        )
        .values('student_id')
        .annotate(total=Sum('amount'))
    )
    return {int(r['student_id']): int(r['total'] or 0) for r in rows}


def expected_monthly_from_student(student) -> int:
    if not getattr(student, 'group_id', None):
        return 0
    g = getattr(student, 'group', None)
    if g is None:
        return 0
    return int(g.price or 0)


def apply_month_fee_status(student, paid_map: dict) -> None:
    e = expected_monthly_from_student(student)
    p = int(paid_map.get(student.pk, 0))
    rem = max(0, e - p) if e > 0 else 0
    if e <= 0:
        status = 'na'
    elif p >= e:
        status = 'full'
    elif p > 0:
        status = 'partial'
    else:
        status = 'none'
    student.month_fee_expected = e
    student.month_fee_paid = p
    student.month_fee_remaining = rem
    student.month_fee_status = status
    student.paid_this_month = status == 'full'


def attach_month_fee_for_students(students, paid_map: dict | None = None, month_start=None, month_end=None):
    if not students:
        return
    if month_start is None or month_end is None:
        month_start, month_end, _ = current_calendar_month_bounds()
    if paid_map is None:
        ids = [s.pk for s in students]
        paid_map = month_income_totals_by_student(ids, month_start, month_end)
    for s in students:
        apply_month_fee_status(s, paid_map)
