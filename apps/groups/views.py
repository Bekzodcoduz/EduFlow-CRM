import calendar
from datetime import date, datetime, time, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date, parse_time

from .models import Group, Course, Room
from apps.accounts.models import User
from apps.students.models import Attendance


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


def _align_end_time(start: time, end: time) -> time:
    s = datetime.combine(date.today(), start)
    e = datetime.combine(date.today(), end)
    if e <= s:
        return (s + timedelta(hours=1)).time()
    return end


def _normalize_subject_label(value):
    return ' '.join((value or '').strip().lower().split())


def _build_course_options():
    courses_qs = Course.objects.all().order_by('name')
    course_options = []
    seen_course_labels = set()
    for c in courses_qs:
        norm = _normalize_subject_label(c.name)
        if not norm or norm in seen_course_labels:
            continue
        seen_course_labels.add(norm)
        course_options.append({'value': str(c.pk), 'label': c.name.strip()})
    teacher_subjects = (
        User.teachers_for_select()
        .exclude(subject='')
        .values_list('subject', flat=True)
        .distinct()
    )
    for subject in teacher_subjects:
        label = (subject or '').strip()
        norm = _normalize_subject_label(label)
        if not norm:
            continue
        if norm in seen_course_labels:
            continue
        seen_course_labels.add(norm)
        course_options.append({'value': f"subject:{label}", 'label': label})
    return course_options


@login_required
def group_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', 'all')

    qs = Group.objects.select_related('course', 'teacher', 'room')
    if not request.user.is_admin:
        qs = qs.filter(teacher=request.user)
    base_qs = qs
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(course__name__icontains=q)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    total_students = sum(g.student_count for g in qs)

    courses_qs = Course.objects.all().order_by('name')
    course_options = _build_course_options()

    ctx = {
        'groups':        qs,
        'courses':       courses_qs,
        'course_options':course_options,
        'teachers':      User.teachers_for_select(),
        'q':             q,
        'status':        status,
        'total_students':total_students,
        'inactive_groups': base_qs.filter(is_active=False).count(),
    }
    return render(request, 'groups/list.html', ctx)


@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if not request.user.is_admin and group.teacher != request.user:
        return redirect('groups')

    month_str = request.GET.get('month', date.today().strftime('%Y-%m'))
    year, mon = map(int, month_str.split('-'))

    import calendar
    days_count = calendar.monthrange(year, mon)[1]
    dates = [date(year, mon, d) for d in range(1, days_count + 1)]

    students = group.students.filter(is_active=True)
    att_qs = Attendance.objects.filter(student__in=students, date__year=year, date__month=mon)
    att_map = {(a.student_id, str(a.date)): a for a in att_qs}

    def _cell_kind(att):
        if not att:
            return 'empty'
        if att.is_present:
            return 'present'
        if att.excused_absence:
            return 'excused'
        return 'absent'

    matrix = []
    for s in students:
        row = []
        present = 0
        for d in dates:
            att = att_map.get((s.id, str(d)))
            kind = _cell_kind(att)
            p = att.is_present if att else False
            if p:
                present += 1
            row.append({
                'date': d,
                'present': p,
                'excused': bool(att and att.excused_absence),
                'cell_kind': kind,
                'date_str': str(d),
            })
        pct = round(present / len(dates) * 100) if dates else 0
        matrix.append({'student': s, 'days': row, 'pct': pct, 'present': present})

    ctx = {
        'group':     group,
        'matrix':    matrix,
        'dates':     dates,
        'students':  students,
        'month_str': month_str,
    }
    return render(request, 'groups/detail.html', ctx)


@login_required
def group_edit(request, pk):
    group = get_object_or_404(
        Group.objects.select_related('course', 'teacher', 'room'),
        pk=pk,
    )
    if not request.user.is_admin:
        messages.error(request, "Guruhni tahrirlash faqat administrator uchun.")
        return redirect('group-detail', pk=pk)

    course_options = _build_course_options()
    option_values = {o['value'] for o in course_options}
    if group.course_id and str(group.course_id) not in option_values:
        course_options.insert(
            0,
            {'value': str(group.course_id), 'label': group.course.name},
        )

    teachers = User.teachers_for_select()
    rooms = Room.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, "Guruh nomi majburiy!")
            return redirect('group-edit', pk=pk)

        st = parse_time(request.POST.get('start_time') or '') or group.start_time
        et = parse_time(request.POST.get('end_time') or '') or group.end_time
        et = _align_end_time(st, et)

        sd = parse_date(request.POST.get('start_date') or '') or group.start_date
        ed = parse_date(request.POST.get('end_date') or '') or group.end_date

        if ed < sd:
            messages.error(request, "Tugash sanasi boshlanishdan oldin bo'lishi mumkin emas!")
            return redirect('group-edit', pk=pk)

        course_raw = (request.POST.get('course') or '').strip()
        course_id = None
        if course_raw.startswith('subject:'):
            course_name = course_raw.split('subject:', 1)[1].strip()
            if course_name:
                course, _ = Course.objects.get_or_create(name=course_name)
                course_id = course.id
        elif course_raw:
            course_id = course_raw

        room_raw = (request.POST.get('room') or '').strip()
        room_id = room_raw if room_raw else None

        group.name = name
        group.course_id = course_id
        group.teacher_id = request.POST.get('teacher') or None
        group.room_id = room_id
        group.days = request.POST.get('days', group.days)
        group.start_time = st
        group.end_time = et
        group.start_date = sd
        group.end_date = ed
        group.price = request.POST.get('price') or group.price
        group.save()
        messages.success(request, "Guruh saqlandi!")
        return redirect('group-detail', pk=pk)

    current_course = ''
    if group.course_id:
        current_course = str(group.course_id)

    ctx = {
        'group': group,
        'course_options': course_options,
        'teachers': teachers,
        'rooms': rooms,
        'current_course': current_course,
    }
    return render(request, 'groups/edit.html', ctx)


@login_required
@require_POST
def group_create(request):
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, "Guruh nomi majburiy!")
        return redirect('groups')

    st = parse_time(request.POST.get('start_time') or '') or time(9, 0)
    et = parse_time(request.POST.get('end_time') or '') or time(10, 30)
    et = _align_end_time(st, et)

    sd = parse_date(request.POST.get('start_date') or '') or date.today()
    ed = _add_months(sd, 6)

    if ed < sd:
        messages.error(request, "Tugash sanasi boshlanishdan oldin bo'lishi mumkin emas!")
        return redirect('groups')

    course_raw = (request.POST.get('course') or '').strip()
    course_id = None
    if course_raw.startswith('subject:'):
        course_name = course_raw.split('subject:', 1)[1].strip()
        if course_name:
            course, _ = Course.objects.get_or_create(name=course_name)
            course_id = course.id
    elif course_raw:
        course_id = course_raw

    Group.objects.create(
        name       = name,
        course_id  = course_id,
        teacher_id = request.POST.get('teacher') or None,
        days       = request.POST.get('days', 'even'),
        start_time = st,
        end_time   = et,
        start_date = sd,
        end_date   = ed,
        price      = request.POST.get('price') or 300000,
    )
    messages.success(request, f"✓ '{name}' guruhi qo'shildi!")
    return redirect('groups')


@login_required
@require_POST
def group_toggle(request, pk):
    g = get_object_or_404(Group, pk=pk)
    g.is_active = not g.is_active
    g.save()
    status = 'Faollashtirildi' if g.is_active else "To'xtatildi"
    messages.success(request, status + '!')
    return redirect('groups')


@login_required
@require_POST
def group_delete(request, pk):
    if not request.user.is_admin:
        return redirect('groups')
    get_object_or_404(Group, pk=pk).delete()
    messages.success(request, "Guruh o'chirildi!")
    return redirect('groups')

