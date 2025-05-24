from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """
    Divide el valor por el argumento.
    Uso: {{ value|div:arg }}
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return value / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """
    Multiplica el valor por el argumento.
    Uso: {{ value|mul:arg }}
    """
    try:
        value = float(value)
        arg = float(arg)
        return value * arg
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """
    Calcula el porcentaje de value con respecto a arg.
    Uso: {{ value|percentage:arg }}
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return (value / arg) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """
    Resta el argumento del valor.
    Uso: {{ value|subtract:arg }}
    """
    try:
        value = float(value)
        arg = float(arg)
        return value - arg
    except (ValueError, TypeError):
        return 0

@register.filter
def add_float(value, arg):
    """
    Suma el argumento al valor (versión float).
    Uso: {{ value|add_float:arg }}
    """
    try:
        value = float(value)
        arg = float(arg)
        return value + arg
    except (ValueError, TypeError):
        return 0 