"""
Locale middleware for django-magic-translation
"""
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.shortcuts import redirect


AVAILABLE_LANGUAGES = dict(settings.LANGUAGES)
NOT_LOCALIZED_URLS = set(
    tuple(getattr(settings, 'NOT_LOCALIZED_URLS', ())) + (
            settings.STATIC_URL, settings.MEDIA_URL)
)


def get_language_from_request(request):
    return translation.get_language_from_request(request, check_path=True)


def has_language_prefix(request):
    prefix = "/%s/" % get_language_from_request(request)
    return request.path_info.startswith(prefix)


def set_language_to_request(request, language):
    translation.activate(language)
    request.LANGUAGE_CODE = language
    if not request.session.get(settings.LANGUAGE_COOKIE_NAME) == language:
        request.session[settings.LANGUAGE_COOKIE_NAME] = language


def must_localize_path(path):
    for url in NOT_LOCALIZED_URLS:
        if path.startswith(url):
            return False
    return True


class LocaleMiddleware(object):
    """
    Simple middleware that overwrites functionality
    of default Django Locale Middleware
    """
    def __init__(self):
        if not settings.USE_I18N:
            raise MiddlewareNotUsed

    def process_request(self, request):
        language = get_language_from_request(request)
        must_localize = must_localize_path(request.path_info)
        if not has_language_prefix(request) and must_localize:
            if request.method == 'POST':
                return
            return redirect('/%s%s' % (language, request.get_full_path()))

        language = get_language_from_request(request)
        set_language_to_request(request, language)
        if must_localize:
            request.path_info = '/' + request.path_info.split('/', 2)[2]
            request.path = '/' + request.path.split('/', 2)[2]

    def process_response(self, request, response):
        language = translation.get_language()
        translation.deactivate()
        patch_vary_headers(response, ('Accept-Language',))
        if 'Content-Language' not in response:
            response['Content-Language'] = language

        if request.COOKIES.get('django_language') != language:
            response.set_cookie("django_language", language)
        return response
