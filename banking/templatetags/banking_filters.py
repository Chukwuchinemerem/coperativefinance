from django import template
register = template.Library()

@register.filter
def get_currency_symbol(currency):
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£'}
    return symbols.get(currency, '$')
