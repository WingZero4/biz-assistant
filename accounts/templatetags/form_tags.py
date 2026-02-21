from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class to a form field widget."""
    existing = field.field.widget.attrs.get('class', '')
    classes = f'{existing} {css_class}'.strip()
    return field.as_widget(attrs={'class': classes})


@register.filter(name='bs')
def bootstrap_field(field):
    """Auto-apply Bootstrap classes based on widget type."""
    widget = field.field.widget
    widget_type = widget.__class__.__name__

    if widget_type in ('Select', 'SelectMultiple'):
        css_class = 'form-select'
    elif widget_type in ('CheckboxInput',):
        css_class = 'form-check-input'
    elif widget_type in ('FileInput', 'ClearableFileInput'):
        css_class = 'form-control'
    else:
        css_class = 'form-control'

    existing = widget.attrs.get('class', '')
    classes = f'{existing} {css_class}'.strip()
    return field.as_widget(attrs={'class': classes})
