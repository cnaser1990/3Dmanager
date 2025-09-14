# calculator/templatetags/querystring.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    request = context.get('request')
    params = request.GET.copy() if request else {}
    for k, v in kwargs.items():
        if v is None or v == '':
            params.pop(k, None)
        else:
            params[k] = v
    # If params is a dict (no request), handle gracefully
    try:
        return params.urlencode()
    except AttributeError:
        from urllib.parse import urlencode
        return urlencode(params)