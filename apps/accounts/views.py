import calendar
import json
import re
import secrets

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import User


_MONTH_UZ = {
    1: 'Yan', 2: 'Fev', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Iyun',
    7: 'Iyul', 8: 'Avg', 9: 'Sen', 10: 'Okt', 11: 'Noy', 12: 'Dek',
}


def _rolling_12_month_keys(today):
    """Eng yangi oy oxirida — 12 ta (yil, oy), eng eski birinchi."""
    keys = []
    y, m = today.year, today.month
    for _ in range(12):
        keys.insert(0, (y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return keys


def _monthly_income_chart(payment_qs):
    """Kirim to'lovlarini oyma-oy (so'm) — grafik uchun JSON."""
    from datetime import date
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth

    today = date.today()
    keys_order = _rolling_12_month_keys(today)

    agg = (
        payment_qs.filter(payment_type='income')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    by_ym = {}
    for row in agg:
        d = row['month']
        if d:
            by_ym[(d.year, d.month)] = int(row['total'] or 0)

    chart = []
    for y, m in keys_order:
        chart.append({
            'l': _MONTH_UZ[m],
            'v': by_ym.get((y, m), 0),
        })
    return json.dumps(chart, ensure_ascii=False)


def _unique_teacher_username(first_name: str, last_name: str) -> str:
    raw = f"{first_name.strip()}_{last_name.strip()}".lower().replace(' ', '_')
    base = re.sub(r'[^\w.-]', '', raw, flags=re.UNICODE).strip('._') or 'teacher'
    base = base[:80]
    username = base
    while User.objects.filter(username=username).exists():
        username = f"{base}_{secrets.token_hex(3)}"[:150]
    return username


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', '').strip(),
            password=request.POST.get('password', '')
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        error = "Login yoki parol noto'g'ri!"
    return render(request, 'registration/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def account_settings(request):
    """Profil (ism, telefon) va parolni o'zgartirish."""
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')
        if action == 'profile':
            fn = request.POST.get('first_name', '').strip()
            ln = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            if not fn or not ln:
                messages.error(request, "Ism va familiya majburiy.")
            else:
                user.first_name = fn[:150]
                user.last_name = ln[:150]
                user.phone = phone[:20]
                if user.role == User.TEACHER:
                    user.subject = request.POST.get('subject', '').strip()[:100]
                user.save()
                messages.success(request, "Profil saqlandi.")
                return redirect('settings')
        elif action == 'password' and user.has_usable_password():
            old_password = (request.POST.get('old_password') or '').strip()
            new_password1 = (request.POST.get('new_password1') or '').strip()
            new_password2 = (request.POST.get('new_password2') or '').strip()

            if not user.check_password(old_password):
                messages.error(request, "Joriy parol noto'g'ri kiritildi.")
            elif len(new_password1) < 4:
                messages.error(request, "Yangi parol kamida 4 ta belgidan iborat bo'lishi kerak.")
            elif new_password1 != new_password2:
                messages.error(request, "Yangi parollar bir-biriga mos emas.")
            else:
                user.set_password(new_password1)
                user.save(update_fields=['password'])
                update_session_auth_hash(request, user)
                messages.success(request, "Parol muvaffaqiyatli yangilandi.")
                return redirect('settings')

    ctx = {
        'can_change_password': user.has_usable_password(),
    }
    return render(request, 'accounts/settings.html', ctx)


@login_required
def dashboard_view(request):
    from apps.students.models import Student
    from apps.groups.models import Group
    from apps.finance.models import Payment
    from django.db.models import Sum

    user = request.user
    groups   = Group.objects.filter(is_active=True) if user.is_admin else Group.objects.filter(teacher=user, is_active=True)
    students = Student.objects.filter(is_active=True) if user.is_admin else Student.objects.filter(group__in=groups, is_active=True)

    income_payments = Payment.objects.filter(payment_type='income')
    if not user.is_admin:
        income_payments = income_payments.filter(student__group__in=groups)

    total_income = int(income_payments.aggregate(s=Sum('amount'))['s'] or 0)

    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    scope_students = Student.objects.filter(is_active=True) if user.is_admin else Student.objects.filter(group__in=groups, is_active=True)
    scope_ids = list(scope_students.values_list('pk', flat=True))
    paid_ids = set(
        Payment.objects.filter(
            payment_type=Payment.INCOME,
            student_id__in=scope_ids,
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
        ).values_list('student_id', flat=True).distinct()
    )
    debtors_count = max(0, len(scope_ids) - len(paid_ids))

    recent_qs = Payment.objects.select_related('student').order_by('-created_at')
    if not user.is_admin:
        recent_qs = recent_qs.filter(student__group__in=groups)
    recent_payments = recent_qs[:5]

    monthly_chart_json = _monthly_income_chart(income_payments)

    ctx = {
        'active_students': students.count(),
        'active_groups':   groups.count(),
        'total_income':    total_income,
        'debtors_count':   debtors_count,
        'status_month_label': f"{_MONTH_UZ[today.month]} {today.year}",
        'my_groups':       groups[:6],
        'recent_payments': recent_payments,
        'monthly_chart_json': monthly_chart_json,
    }
    return render(request, 'dashboard/index.html', ctx)


@login_required
def teachers_list(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    q = (request.GET.get('q') or '').strip()
    subject = (request.GET.get('subject') or '').strip()
    group_id = (request.GET.get('group') or '').strip()

    from django.db.models import Q
    from apps.groups.models import Group
    teachers_qs = User.teachers_for_select().prefetch_related('teacher_groups')

    if q:
        teachers_qs = teachers_qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q)
        )
    if subject == '__filled__':
        teachers_qs = teachers_qs.exclude(subject='')
    elif subject:
        teachers_qs = teachers_qs.filter(subject=subject)
    if group_id.isdigit():
        teachers_qs = teachers_qs.filter(teacher_groups__pk=int(group_id))

    teachers_qs = teachers_qs.distinct().order_by('last_name', 'first_name', 'username')
    total = teachers_qs.count()
    all_teachers = User.teachers_for_select()
    departments_count = all_teachers.exclude(subject='').values('subject').distinct().count()
    subject_options = list(
        all_teachers.exclude(subject='').values_list('subject', flat=True).distinct().order_by('subject')
    )
    group_options = Group.objects.filter(teacher__role=User.TEACHER).distinct().order_by('name')

    paginator = Paginator(teachers_qs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = {
        'teachers': page_obj,
        'total':    total,
        'page_obj': page_obj,
        'departments_count': departments_count,
        'subject_options': subject_options,
        'group_options': group_options,
        'q': q,
        'subject': subject,
        'group_id': group_id,
    }
    return render(request, 'teachers/list.html', ctx)


@login_required
@require_POST
def teacher_create(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    fn = request.POST.get('first_name', '').strip()
    ln = request.POST.get('last_name', '').strip()

    if not fn or not ln:
        messages.error(request, "Ism va familiya majburiy!")
        return redirect('teachers')

    username = (request.POST.get('username') or '').strip()
    if not username:
        messages.error(request, "Login majburiy.")
        return redirect('teachers')
    if User.objects.filter(username=username).exists():
        messages.error(request, "Bu login allaqachon band.")
        return redirect('teachers')

    password = (request.POST.get('password') or '').strip()
    if len(password) < 4:
        messages.error(request, "Parol kamida 4 ta belgidan iborat bo'lishi kerak.")
        return redirect('teachers')

    user = User(
        username=username,
        first_name=fn,
        last_name=ln,
        role=User.TEACHER,
        subject=request.POST.get('subject', '').strip(),
        phone=request.POST.get('phone', '').strip(),
    )
    user.set_password(password)
    user.save()
    messages.success(
        request,
        f"✓ {fn} {ln} qo'shildi. Login: {username}. Parol: {password}",
    )
    return redirect('teachers')


@login_required
@require_POST
def teacher_delete(request, pk):
    if not request.user.is_admin:
        return redirect('dashboard')
    User.objects.filter(pk=pk, role=User.TEACHER).delete()
    messages.success(request, "O'chirildi!")
    return redirect('teachers')


@login_required
@require_POST
def teacher_update_credentials(request, pk):
    if not request.user.is_admin:
        return redirect('dashboard')
    teacher = get_object_or_404(User, pk=pk, role=User.TEACHER)
    username = (request.POST.get('username') or '').strip()
    new_password = (request.POST.get('password') or '').strip()

    if not username:
        messages.error(request, "Login bo'sh bo'lmasligi kerak.")
        return redirect('teachers')
    if User.objects.exclude(pk=teacher.pk).filter(username=username).exists():
        messages.error(request, "Bu login allaqachon band.")
        return redirect('teachers')

    teacher.username = username
    updated_fields = ['username']
    if new_password:
        if len(new_password) < 4:
            messages.error(request, "Parol kamida 4 ta belgidan iborat bo'lishi kerak.")
            return redirect('teachers')
        teacher.set_password(new_password)
        updated_fields.append('password')
    teacher.save(update_fields=updated_fields)
    messages.success(
        request,
        f"{teacher.full_name} ma'lumotlari yangilandi."
        + (f" Yangi parol: {new_password}" if new_password else "")
    )
    return redirect('teachers')


@login_required
def teacher_detail(request, pk):
    """O'qituvchi profili — guruhlar, talabalar, daromad."""
    from apps.groups.models import Group
    from apps.finance.models import Payment
    from apps.students.models import Student
    from django.db.models import Sum

    teacher = get_object_or_404(User, pk=pk, role=User.TEACHER)
    if not request.user.is_admin and request.user.pk != teacher.pk:
        messages.error(request, "Faqat o'zingizga tegishli profilni ko'ra olasiz.")
        return redirect('dashboard')

    # O'qituvchining guruhlari
    groups = Group.objects.filter(teacher=teacher).select_related('course', 'room').prefetch_related('students')

    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    all_students = list(
        Student.objects.filter(group__teacher=teacher, is_active=True)
        .select_related('group')
        .order_by('last_name', 'first_name')
    )
    paid_this_month_rows = (
        Payment.objects.filter(
            payment_type='income',
            student__in=all_students,
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
        )
        .values('student_id')
        .annotate(total=Sum('amount'))
    )
    paid_this_month_ids = {row['student_id'] for row in paid_this_month_rows if int(row['total'] or 0) > 0}
    for st in all_students:
        st.paid_this_month = st.pk in paid_this_month_ids
    paid_students = [st for st in all_students if st.paid_this_month]
    paid_students_count = len(paid_students)
    unpaid_students = [st for st in all_students if not st.paid_this_month]

    # Har bir guruh uchun statistika
    group_stats = []
    total_revenue = 0
    total_students = len(all_students)

    for g in groups:
        students = [st for st in all_students if st.group_id == g.pk]
        sc = len(students)
        paid_count = sum(1 for st in students if st.paid_this_month)
        unpaid_count = sc - paid_count
        # Guruh bo'yicha to'lovlar
        revenue = int(
            Payment.objects.filter(
                student__group=g, payment_type='income'
            ).aggregate(s=Sum('amount'))['s'] or 0
        )
        total_revenue += revenue
        group_stats.append({
            'group':    g,
            'students': sc,
            'paid_count': paid_count,
            'debtors':  unpaid_count,
            'revenue':  revenue,
        })

    # Umumiy davomat
    from apps.students.models import Attendance
    att_total   = Attendance.objects.filter(student__group__teacher=teacher).count()
    att_present = Attendance.objects.filter(student__group__teacher=teacher, is_present=True).count()
    att_pct = round(att_present / att_total * 100) if att_total else 0

    ctx = {
        'teacher':        teacher,
        'group_stats':    group_stats,
        'total_revenue':  total_revenue,
        'total_students': total_students,
        'paid_students_count': paid_students_count,
        'unpaid_students_count': total_students - paid_students_count,
        'paid_students': paid_students,
        'unpaid_students': unpaid_students,
        'month_label': f"{_MONTH_UZ[today.month]} {today.year}",
        'att_pct':        att_pct,
        'groups_count':   groups.count(),
        'all_students': all_students,
    }
    return render(request, 'teachers/detail.html', ctx)


@login_required
@require_POST
def teacher_set_password(request, pk):
    if not request.user.is_admin:
        return redirect('dashboard')
    teacher = get_object_or_404(User, pk=pk, role=User.TEACHER)
    new_password = (request.POST.get('new_password') or '').strip()
    if len(new_password) < 4:
        messages.error(request, "Yangi parol kamida 4 ta belgidan iborat bo'lishi kerak.")
        return redirect('teachers')
    teacher.set_password(new_password)
    teacher.save(update_fields=['password'])
    messages.success(request, f"{teacher.full_name} uchun parol yangilandi.")
    return redirect('teachers')
