from django import template

register = template.Library()


@register.filter
def divide(value, arg):
    return value / arg
