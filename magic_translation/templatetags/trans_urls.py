from django.template import Library
from django.conf import settings
from django.utils.translation import get_language

register = Library()


def has_language_prefix(url):
    for lang_code in dict(settings.LANGUAGES):
        if url.startswith('/%s/' % lang_code):
            return True
    return False


@register.simple_tag()
def language_url(item, language=None):
    """
    Template tag that return localized url from item.
    item can be model or other object that have get_absolute_url attribute.
    There is an optional argument language to force localisation
    of the returned url to that language
    """
    try:
        url = item.get_absolute_url()
    except AttributeError:
        if isinstance(item, basestring):
            url = item
        else:
            return None
    if not settings.USE_I18N:
        return url
    language = language or get_language()
    if has_language_prefix(url):
        bits = url.split('/', 2)
        bits[1] = language
        return '/'.join(bits)
    return '/%s%s' % (language, url)
