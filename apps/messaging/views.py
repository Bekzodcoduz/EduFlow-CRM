import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.students.models import Student

from .sms_backends import send_bulk


@login_required
@require_http_methods(['GET', 'POST'])
def sms_compose(request):
    """SMS yuborish formasi (SMS_BACKEND: dry_run / console / webhook)."""
    if not request.user.is_admin:
        messages.error(request, "SMS bo'limi faqat administrator uchun.")
        return redirect('dashboard')

    def _normalize_phone(raw: str) -> str:
        raw = (raw or '').strip()
        if not raw:
            return ''
        has_plus = raw.startswith('+')
        digits = re.sub(r'\D', '', raw)
        if not digits:
            return ''
        # SMS provayderlar odatda 9-15 xonali (country code bilan)
        if len(digits) < 9 or len(digits) > 15:
            return ''
        return ('+' if has_plus else '') + digits

    def _parse_manual_phones(phones_raw: str) -> list[str]:
        parts = re.split(r'[\n,;]+', phones_raw or '')
        out: list[str] = []
        for p in parts:
            n = _normalize_phone(p)
            if n:
                out.append(n)
        return sorted(set(out))

    def _phones_from_db(audience: str) -> list[str]:
        qs = Student.objects.filter(is_active=True).only('phone', 'parent_phone')
        if audience == 'debtors':
            qs = qs.filter(balance__lt=0)

        out: list[str] = []
        for s in qs:
            for raw in (s.phone, s.parent_phone):
                n = _normalize_phone(raw)
                if n:
                    out.append(n)
        return sorted(set(out))

    if request.method == 'POST':
        text = (request.POST.get('message') or '').strip()
        audience = (request.POST.get('audience') or '').strip()
        phones_raw = (request.POST.get('phones') or '').strip()

        if not text:
            messages.error(request, "Xabar matnini kiriting.")
            return redirect('messaging-sms')

        # Qabul qiluvchilarni DB dan olamiz (manual faqat ixtiyoriy holat)
        if audience == 'manual':
            phones = _parse_manual_phones(phones_raw)
        else:
            phones = _phones_from_db(audience if audience in {'all_students', 'debtors'} else 'all_students')

        if not phones:
            messages.error(
                request,
                "Yuboriladigan raqamlar topilmadi. Talaba yoki ota/ona telefoni bo‘sh yoki noto‘g‘ri bo‘lishi mumkin.",
            )
            return redirect('messaging-sms')

        result = send_bulk(phones, text)
        phones_count = len(phones)
        preview = ', '.join(phones[:5]) + ('...' if phones_count > 5 else '')
        prefix = (
            f"Matn: {len(text)} belgi. Auditoriya: {audience or 'all_students'}. "
            f"Raqamlar: {phones_count} ta ({preview}). "
        )
        if result.get('ok'):
            if result.get('mode') == 'dry_run':
                messages.warning(request, prefix + (result.get('detail') or ''))
            else:
                messages.success(
                    request,
                    prefix + (result.get('detail') or f"Yuborildi: {result.get('sent', 0)} ta."),
                )
        else:
            messages.error(request, prefix + (result.get('detail') or "SMS yuborilmadi."))
        return redirect('messaging-sms')

    return render(request, 'messaging/sms.html')
