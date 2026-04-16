from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from datetime import date
import json
import calendar

from apps.groups.models import Group
from apps.students.models import Student, Attendance


def _groups_for_user(user):
    if user.is_admin:
        return Group.objects.all()
    return Group.objects.filter(teacher=user)


def _cell_kind(att: Attendance | None) -> str:
    if not att:
        return 'empty'
    if att.is_present:
        return 'present'
    if att.excused_absence:
        return 'excused'
    return 'absent'


def _toggle_payload(att: Attendance | None, date_str: str) -> dict:
    kind = _cell_kind(att)
    return {
        'date': date_str,
        'cell_state': kind,
        'is_present': bool(att and att.is_present),
        'excused_absence': bool(att and att.excused_absence),
    }


def _build_matrix_rows(students, dates, att_map: dict):
    """att_map: (student_id, date_str) -> Attendance instance"""
    matrix = []
    for s in students:
        row = []
        present_count = 0
        billable_count = 0
        no_pay_absent_count = 0
        for d in dates:
            att = att_map.get((s.id, str(d)))
            kind = _cell_kind(att)
            if kind == 'present':
                present_count += 1
            if att and att.counts_for_payment:
                billable_count += 1
            if att and (not att.is_present) and (not att.excused_absence):
                no_pay_absent_count += 1
            row.append({
                'date': d,
                'date_str': str(d),
                'present': att.is_present if att else False,
                'excused': bool(att and att.excused_absence),
                'cell_kind': kind,
                'att_id': att.id if att else None,
            })
        pct = round(present_count / len(dates) * 100) if dates else 0
        matrix.append({
            'student': s,
            'days': row,
            'pct': pct,
            'present_count': present_count,
            'absent_count': len(dates) - present_count,
            'billable_count': billable_count,
            'no_pay_absent_count': no_pay_absent_count,
            'sababli_count': billable_count - present_count,
        })
    return matrix


@login_required
def attendance_home(request):
    """Davomat bosh sahifasi — guruh tanlash va kunlik belgilash."""
    groups = _groups_for_user(request.user).filter(is_active=True).select_related('course', 'teacher')

    selected_gid = request.GET.get('group')
    selected_group = None
    matrix = []
    dates = []
    month_str = request.GET.get('month', date.today().strftime('%Y-%m'))

    try:
        year, mon = map(int, month_str.split('-'))
    except Exception:
        year, mon = date.today().year, date.today().month
        month_str = f"{year}-{mon:02d}"

    days_count = calendar.monthrange(year, mon)[1]
    dates = [date(year, mon, d) for d in range(1, days_count + 1)]

    if selected_gid:
        selected_group = groups.filter(pk=selected_gid).first()

    if selected_group:
        students = Student.objects.filter(group=selected_group, is_active=True)
        att_qs = Attendance.objects.filter(
            student__in=students,
            date__year=year,
            date__month=mon,
        )
        att_map = {(a.student_id, str(a.date)): a for a in att_qs}
        matrix = _build_matrix_rows(students, dates, att_map)

    group_stats = None
    if selected_group and matrix:
        total_pct = sum(r['pct'] for r in matrix) / len(matrix) if matrix else 0
        total_present = sum(r['present_count'] for r in matrix)
        total_possible = len(matrix) * len(dates)
        total_absent = total_possible - total_present
        total_billable = sum(r['billable_count'] for r in matrix)
        total_no_pay = sum(r['no_pay_absent_count'] for r in matrix)
        total_excused = total_billable - total_present
        group_stats = {
            'avg_pct': round(total_pct),
            'total_present': total_present,
            'total_absent': total_absent,
            'total_possible': total_possible,
            'student_count': len(matrix),
            'total_billable': total_billable,
            'total_no_pay_absent': total_no_pay,
            'total_excused': total_excused,
        }

    today_d = date.today()
    today_in_month = (year, mon) == (today_d.year, today_d.month)

    ctx = {
        'groups': groups,
        'selected_group': selected_group,
        'selected_gid': selected_gid,
        'matrix': matrix,
        'dates': dates,
        'month_str': month_str,
        'today': today_d,
        'today_in_month': today_in_month,
        'group_stats': group_stats,
    }
    return render(request, 'attendance/index.html', ctx)


@login_required
@require_POST
def toggle_attendance(request):
    """AJAX: keldi <-> kelmadi (ketma-ket). Sababli alohida set_excused_absence orqali."""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        date_str = data.get('date')
        d = date.fromisoformat(date_str)

        student = get_object_or_404(
            Student.objects.select_related('group'),
            pk=student_id,
            is_active=True,
        )
        if not request.user.is_admin and student.group and student.group.teacher_id != request.user.id:
            return JsonResponse({'error': "Ruxsat yo'q"}, status=403)
        if not request.user.is_admin and student.group is None:
            return JsonResponse({'error': "Guruhsiz talaba uchun ruxsat yo'q"}, status=403)

        att = Attendance.objects.filter(student_id=student_id, date=d).first()
        if not att:
            att = Attendance.objects.create(
                student_id=student_id,
                date=d,
                is_present=True,
                excused_absence=False,
            )
        elif att.is_present:
            att.is_present = False
            att.excused_absence = False
            att.save()
        else:
            att.is_present = True
            att.excused_absence = False
            att.save()

        out = _toggle_payload(att, date_str)
        return JsonResponse(out)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def set_excused_absence(request):
    """AJAX: faqat kelmagan kun uchun — sababli (to'lov bor) / sababsiz."""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        date_str = data.get('date')
        excused = bool(data.get('excused_absence'))
        d = date.fromisoformat(date_str)

        student = get_object_or_404(
            Student.objects.select_related('group'),
            pk=student_id,
            is_active=True,
        )
        if not request.user.is_admin and student.group and student.group.teacher_id != request.user.id:
            return JsonResponse({'error': "Ruxsat yo'q"}, status=403)
        if not request.user.is_admin and student.group is None:
            return JsonResponse({'error': "Guruhsiz talaba uchun ruxsat yo'q"}, status=403)

        att = Attendance.objects.filter(student_id=student_id, date=d).first()
        if not att:
            return JsonResponse({'error': 'Avval kelmadi deb belgilang'}, status=400)
        if att.is_present:
            return JsonResponse({'error': "Kelgan kun uchun sababli bo'lmaydi"}, status=400)

        att.excused_absence = excused
        att.save()
        return JsonResponse(_toggle_payload(att, date_str))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mark_all(request):
    """AJAX: guruh talabalarini barchasini belgilash."""
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        date_str = data.get('date')
        is_present = data.get('is_present', True)
        d = date.fromisoformat(date_str)

        group = get_object_or_404(_groups_for_user(request.user), pk=group_id, is_active=True)
        students = Student.objects.filter(group=group, is_active=True)
        for s in students:
            att, created = Attendance.objects.get_or_create(
                student=s,
                date=d,
                defaults={
                    'is_present': is_present,
                    'excused_absence': False,
                },
            )
            if not created:
                att.is_present = is_present
                att.excused_absence = False
                att.save()

        present_count = Attendance.objects.filter(
            student__in=students, date=d, is_present=True
        ).count()

        return JsonResponse({
            'ok': True,
            'present_count': present_count,
            'total': students.count(),
            'is_present': is_present,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def attendance_report(request, group_id):
    """Guruh bo'yicha davomat hisoboti."""
    group = get_object_or_404(Group, pk=group_id)
    if not request.user.is_admin and group.teacher != request.user:
        return redirect('attendance')

    month_str = request.GET.get('month', date.today().strftime('%Y-%m'))
    try:
        year, mon = map(int, month_str.split('-'))
    except Exception:
        year, mon = date.today().year, date.today().month

    days_count = calendar.monthrange(year, mon)[1]
    dates = [date(year, mon, d) for d in range(1, days_count + 1)]

    students = Student.objects.filter(group=group, is_active=True)
    att_qs = Attendance.objects.filter(
        student__in=students,
        date__year=year,
        date__month=mon,
    )
    att_map = {(a.student_id, str(a.date)): a for a in att_qs}
    matrix = _build_matrix_rows(students, dates, att_map)

    ctx = {
        'group': group,
        'matrix': matrix,
        'dates': dates,
        'month_str': month_str,
        'today': date.today(),
    }
    return render(request, 'attendance/report.html', ctx)
