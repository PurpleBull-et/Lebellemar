from django.template.defaultfilters import register

@register.filter
def clp(value):
    """Convierte un número a formato de Pesos Chilenos."""
    try:
        return f"${value:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return value