import calendar
import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from apps.students.models import Student, Attendance
from apps.groups.models import Group
from apps.finance.models import Payment


def _income_method_breakdown(qs):
    return {
        'cash': int(qs.filter(payment_method=Payment.METHOD_CASH).aggregate(s=Sum('amount'))['s'] or 0),
        'transfer': int(qs.filter(payment_method=Payment.METHOD_TRANSFER).aggregate(s=Sum('amount'))['s'] or 0),
        'terminal': int(qs.filter(payment_method=Payment.METHOD_TERMINAL).aggregate(s=Sum('amount'))['s'] or 0),
    }


@login_required
def reports_view(request):
    user = request.user
    if user.is_admin:
        q_groups = Group.objects.filter(is_active=True).select_related('course', 'teacher')
        q_students = Student.objects.filter(is_active=True)
    else:
        q_groups = Group.objects.filter(teacher=user, is_active=True).select_related('course', 'teacher')
        q_students = Student.objects.filter(group__in=q_groups, is_active=True)

    income_qs = Payment.objects.filter(payment_type='income')
    if not user.is_admin:
        income_qs = income_qs.filter(student__group__in=q_groups)
    total_income = int(income_qs.aggregate(s=Sum('amount'))['s'] or 0)

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    daily_income = int(income_qs.filter(created_at__date=today).aggregate(s=Sum('amount'))['s'] or 0)
    weekly_income = int(
        income_qs.filter(created_at__date__gte=week_start, created_at__date__lte=week_end).aggregate(s=Sum('amount'))['s']
        or 0
    )
    monthly_income = int(
        income_qs.filter(created_at__date__gte=month_start, created_at__date__lte=month_end).aggregate(s=Sum('amount'))['s']
        or 0
    )
    week_iso = today.isocalendar()
    daily_income_methods = _income_method_breakdown(income_qs.filter(created_at__date=today))
    weekly_income_methods = _income_method_breakdown(
        income_qs.filter(created_at__date__gte=week_start, created_at__date__lte=week_end)
    )
    monthly_income_methods = _income_method_breakdown(
        income_qs.filter(created_at__date__gte=month_start, created_at__date__lte=month_end)
    )

    # Mavjud qarzdorlik kartasi: butun markaz bo'yicha — bu oy to'lanmaganlar summasi
    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    all_active_students = Student.objects.filter(is_active=True).select_related('group')
    paid_ids = set(
        Payment.objects.filter(
            payment_type=Payment.INCOME,
            student__is_active=True,
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
        ).values_list('student_id', flat=True).distinct()
    )
    unpaid_students_qs = all_active_students.exclude(pk__in=paid_ids)
    debtors_total = int(unpaid_students_qs.aggregate(s=Sum('group__price'))['s'] or 0)
    debtors_count = unpaid_students_qs.count()

    group_data = []
    for g in q_groups:
        sc = g.students.filter(is_active=True).count()
        att_tot = Attendance.objects.filter(student__group=g).count()
        att_pres = Attendance.objects.filter(student__group=g, is_present=True).count()
        att_pct = round(att_pres / att_tot * 100) if att_tot else 0
        revenue = int(
            Payment.objects.filter(student__group=g, payment_type='income').aggregate(s=Sum('amount'))['s'] or 0
        )
        group_data.append({
            'group': g,
            'student_count': sc,
            'attendance': att_pct,
            'revenue': revenue,
        })

    monthly = (
        Payment.objects.filter(
            payment_type='income',
            created_at__gte=date.today().replace(day=1) - timedelta(days=360),
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    if not user.is_admin:
        monthly = (
            Payment.objects.filter(
                payment_type='income',
                student__group__in=q_groups,
                created_at__gte=date.today().replace(day=1) - timedelta(days=360),
            )
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

    monthly_data = [{'label': d['month'].strftime('%b'), 'total': int(d['total'])} for d in monthly]

    att_data = []
    for g in q_groups[:6]:
        tot = Attendance.objects.filter(student__group=g).count()
        pres = Attendance.objects.filter(student__group=g, is_present=True).count()
        att_data.append({'name': g.name, 'pct': round(pres / tot * 100) if tot else 0})

    avg_att = round(sum(a['pct'] for a in att_data) / len(att_data)) if att_data else 0

    export_groups = []
    export_students = []
    if user.is_admin:
        export_groups = list(Group.objects.filter(is_active=True).order_by('name'))
        export_students = list(
            Student.objects.filter(is_active=True).select_related('group').order_by('last_name', 'first_name')
        )

    ctx = {
        'total_students': q_students.count(),
        'active_groups': q_groups.count(),
        'total_income': total_income,
        'debtors_total': debtors_total,
        'debtors_count': debtors_count,
        'avg_att': avg_att,
        'daily_income': daily_income,
        'weekly_income': weekly_income,
        'monthly_income': monthly_income,
        'daily_income_methods': daily_income_methods,
        'weekly_income_methods': weekly_income_methods,
        'monthly_income_methods': monthly_income_methods,
        'today_date': today,
        'week_start': week_start,
        'week_end': week_end,
        'month_start': month_start,
        'month_end': month_end,
        'today_iso': today.isoformat(),
        'week_input_value': f'{week_iso.year}-W{week_iso.week:02d}',
        'month_input_value': today.strftime('%Y-%m'),
        'group_data': group_data,
        'monthly_data_json': json.dumps(monthly_data, ensure_ascii=False),
        'att_data': att_data,
        'export_groups': export_groups,
        'export_students': export_students,
    }
    return render(request, 'reports/index.html', ctx)
