from django import template

register = template.Library()


@register.simple_tag()
def increase(option, institution):
    return option.increase(institution)
