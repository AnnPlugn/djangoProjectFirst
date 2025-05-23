from django import template
import re

register = template.Library()

@register.filter
def remove_markdown(value):
    """Remove ** Markdown symbols from text."""
    return re.sub(r'\*\*', '', value)