from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Student, Attendance
from apps.groups.models import Group
from apps.groups.models import Course
from apps.accounts.models import User
from apps.finance.models import Payment
from django.db.models import Sum
import calendar
from datetime import date
from django.utils import timezone


REGIONS = [
    'Toshkent shahar', 'Toshkent viloyati', 'Samarqand viloyati',
    "Farg'ona viloyati", 'Andijon viloyati', 'Namangan viloyati',
    'Buxoro viloyati', 'Xorazm viloyati', 'Qashqadaryo viloyati',
    'Surxondaryo viloyati', 'Sirdaryo viloyati', 'Jizzax viloyati',
    'Navoiy viloyati', "Qoraqalpog'iston Respublikasi",
]


def _groups_for_user(user):
    if user.is_admin:
        return Group.objects.all()
    return Group.objects.filter(teacher=user)


def _students_for_user(user):
    if user.is_admin:
        return Student.objects.all()
    return Student.objects.filter(group__teacher=user)


def _courses_for_user(user):
    """Admin: barcha kurslar (yangi fanlar ham). O'qituvchi: o'z guruhlaridagi kurslar."""
    if user.is_admin:
        return Course.objects.all().order_by('name')
    return Course.objects.filter(groups__teacher=user).distinct().order_by('name')


def _normalize_subject_label(value):
    return ' '.join((value or '').strip().lower().split())


def _current_month_bounds():
    today = timezone.localdate()
    return today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1]), today


def _paid_student_ids_in_month(student_ids):
    if not student_ids:
        return set()
    m_start, m_end, _ = _current_month_bounds()
    rows = (
        Payment.objects.filter(
            payment_type=Payment.INCOME,
            student_id__in=student_ids,
            created_at__date__gte=m_start,
            created_at__date__lte=m_end,
        )
        .values('student_id')
        .annotate(total=Sum('amount'))
    )
    return {r['student_id'] for r in rows if int(r['total'] or 0) > 0}


@login_required
def student_list(request):
    q      = request.GET.get('q', '')
    gid    = request.GET.get('group', '')
    status = request.GET.get('status', '')

    if request.user.is_admin:
        qs = Student.objects.select_related('group__teacher', 'group__course')
    else:
        my_groups = Group.objects.filter(teacher=request.user)
        qs = Student.objects.filter(group__in=my_groups).select_related('group__teacher', 'group__course')

    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(parent_phone__icontains=q)
        )
    if gid:
        qs = qs.filter(group_id=gid)
    ids = list(qs.values_list('pk', flat=True))
    paid_ids = _paid_student_ids_in_month(ids)
    if status == 'debtor':
        qs = qs.filter(pk__in=[sid for sid in ids if sid not in paid_ids])
    elif status == 'paid':
        qs = qs.filter(pk__in=list(paid_ids))

    students_out = list(qs.order_by('last_name', 'first_name'))
    paid_ids_visible = _paid_student_ids_in_month([s.pk for s in students_out])
    for s in students_out:
        s.paid_this_month = s.pk in paid_ids_visible

    groups_all_qs = _groups_for_user(request.user).select_related('course', 'teacher')
    groups_qs = groups_all_qs.filter(is_active=True)
    course_filters = []
    seen_labels = set()
    group_options = []
    for g in groups_all_qs:
        course_name = g.course.name if g.course_id else ''
        teacher_subject = g.teacher.subject if g.teacher_id and g.teacher and g.teacher.subject else ''
        label = course_name or teacher_subject
        if not label:
            continue
        norm = _normalize_subject_label(label)
        if norm:
            group_options.append({'id': g.pk, 'name': g.name, 'course_key': f"n:{norm}"})
            if norm not in seen_labels:
                seen_labels.add(norm)
                course_filters.append({'key': f"n:{norm}", 'label': label.strip()})
        else:
            group_options.append({'id': g.pk, 'name': g.name, 'course_key': ''})

    courses_qs = _courses_for_user(request.user)
    for c in courses_qs:
        norm = _normalize_subject_label(c.name)
        if not norm or norm in seen_labels:
            continue
        seen_labels.add(norm)
        course_filters.append({'key': f"n:{norm}", 'label': c.name.strip()})

    teacher_subjects_qs = User.teachers_for_select().exclude(subject='').values_list('subject', flat=True)
    for subject in teacher_subjects_qs:
        label = (subject or '').strip()
        norm = _normalize_subject_label(label)
        if not norm:
            continue
        if norm in seen_labels:
            continue
        seen_labels.add(norm)
        course_filters.append({'key': f"n:{norm}", 'label': label})

    course_filters.sort(key=lambda x: x['label'].lower())

    ctx = {
        'students': students_out,
        'groups':   groups_qs,
        'group_options': group_options,
        'course_filters': course_filters,
        'regions':  REGIONS,
        'status_month_label': f"{_current_month_bounds()[2].month:02d}.{_current_month_bounds()[2].year}",
        'q': q, 'gid': gid, 'status': status,
    }
    return render(request, 'students/list.html', ctx)


@login_required
@require_POST
def student_create(request):
    if not request.user.is_admin:
        messages.error(request, "Talaba qo'shish faqat administrator uchun.")
        return redirect('students')

    fn = request.POST.get('first_name', '').strip()
    ln = request.POST.get('last_name', '').strip()
    if not fn:
        messages.error(request, "Ism majburiy!")
        return redirect('students')

    group_id = request.POST.get('group') or None
    if group_id:
        can_use_group = _groups_for_user(request.user).filter(pk=group_id).exists()
        if not can_use_group:
            messages.error(request, "Bu guruhga talaba biriktirishga ruxsat yo'q.")
            return redirect('students')

    Student.objects.create(
        first_name   = fn,
        last_name    = ln,
        phone        = request.POST.get('phone', '').strip(),
        parent_phone = request.POST.get('parent_phone', '').strip(),
        birth_date   = request.POST.get('birth_date') or None,
        gender       = request.POST.get('gender', ''),
        email        = '',
        region       = '',
        district     = '',
        mahalla      = '',
        street       = '',
        house        = '',
        address_note = '',
        group_id     = group_id,
        enrolled_at  = request.POST.get('enrolled_at') or None,
    )
    messages.success(request, f"✓ {fn} {ln} ro'yxatga olindi!")
    return redirect('students')


@login_required
@require_POST
def student_update_contact(request, pk):
    """Talaba va ota yoki ona telefonini yangilash."""
    student = get_object_or_404(_students_for_user(request.user), pk=pk)
    phone = (request.POST.get('phone') or '').strip()
    if not phone:
        messages.error(request, "Talaba telefon raqami bo'sh bo'lmasligi kerak.")
        return redirect('student-detail', pk=pk)
    student.phone = phone
    student.parent_phone = (request.POST.get('parent_phone') or '').strip()
    student.save()
    messages.success(request, "Telefon raqamlari yangilandi.")
    return redirect('student-detail', pk=pk)


@login_required
@require_POST
def student_delete(request, pk):
    s = get_object_or_404(_students_for_user(request.user), pk=pk)
    name = s.full_name
    s.delete()
    messages.success(request, f"'{name}' o'chirildi!")
    return redirect('students')


def _payment_course_options(user, student):
    """To'lov formasi: talaba guruhi fani + foydalanuvchi ko'radigan kurslar."""
    seen = set()
    out = []

    def add_course(c):
        if c is not None and c.pk not in seen:
            seen.add(c.pk)
            out.append(c)

    if student.group_id and student.group.course_id:
        add_course(student.group.course)
    for c in _courses_for_user(user):
        add_course(c)
    return out


def _payment_group_options(user, student):
    """To'lov formasi: talaba guruhi + foydalanuvchi ko'ra oladigan faol guruhlar."""
    seen = set()
    out = []

    def add_group(g):
        if g is not None and g.pk not in seen:
            seen.add(g.pk)
            out.append(g)

    if student.group_id:
        add_group(student.group)
    for g in _groups_for_user(user).select_related('course', 'teacher').filter(is_active=True):
        add_group(g)
    return out


@login_required
def student_detail(request, pk):
    """Talaba to'liq profili — ma'lumotlar, to'lovlar, davomat."""
    student = get_object_or_404(
        _students_for_user(request.user).select_related('group__teacher', 'group__course'),
        pk=pk,
    )

    # To'lovlar
    payments = Payment.objects.filter(student=student).select_related('received_by', 'course', 'group').order_by(
        '-created_at'
    )
    total_paid     = int(payments.filter(payment_type='income').aggregate(s=Sum('amount'))['s'] or 0)
    total_discount = int(payments.filter(payment_type='discount').aggregate(s=Sum('amount'))['s'] or 0)
    total_refund   = int(payments.filter(payment_type='refund').aggregate(s=Sum('amount'))['s'] or 0)

    # Davomat (oxirgi 3 oy)
    today = date.today()
    att_all     = Attendance.objects.filter(student=student)
    att_total   = att_all.count()
    att_present = att_all.filter(is_present=True).count()
    att_pct     = round(att_present / att_total * 100) if att_total else 0

    # Bu oy davomati
    this_month_att  = att_all.filter(date__year=today.year, date__month=today.month)
    month_days      = calendar.monthrange(today.year, today.month)[1]
    month_present   = this_month_att.filter(is_present=True).count()
    month_pct       = round(month_present / month_days * 100) if month_days else 0

    # Oxirgi 5 to'lov
    recent_payments = payments[:5]

    ctx = {
        'student':         student,
        'regions':         REGIONS,
        'groups':          _groups_for_user(request.user).filter(is_active=True),
        'payments':        recent_payments,
        'all_payments':    payments,
        'total_paid':      total_paid,
        'total_discount':  total_discount,
        'total_refund':    total_refund,
        'att_total':       att_total,
        'att_present':     att_present,
        'att_pct':         att_pct,
        'month_present':   month_present,
        'month_days':      month_days,
        'month_pct':       month_pct,
        'payment_courses': _payment_course_options(request.user, student),
        'payment_groups':  _payment_group_options(request.user, student),
    }
    return render(request, 'students/detail.html', ctx)
