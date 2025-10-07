# calculator/templatetags/jalali.py
from django import template
from django.utils import timezone
import jdatetime

register = template.Library()

def _localize(dt):
    if timezone.is_aware(dt):
        return timezone.localtime(dt)
    return dt

@register.filter
def jalali(dt, fmt='%Y/%m/%d'):
    """Convert a datetime to Jalali with optional format."""
    if not dt:
        return ''
    dt = _localize(dt)
    jdt = jdatetime.datetime.fromgregorian(datetime=dt)
    return jdt.strftime(fmt)

@register.filter
def jalali_date(d, fmt='%Y/%m/%d'):
    """Convert a date to Jalali with optional format."""
    if not d:
        return ''
    jd = jdatetime.date.fromgregorian(date=d)
    return jd.strftime(fmt)

@register.filter
def fa_digits(value):
    """Convert English digits to Persian digits."""
    return str(value).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))