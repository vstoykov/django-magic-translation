"""
When this application is imported then it will attach a handler to
class_prepared signal. Then handler mark models as translatable
if they has a translatable_fields attribute or was described in
settings.TRANSLATABLE_MODELS or some of the model parents are marked
for translation

Describing in settings.py is for models that can not be touched
(from system installed app), but we want to have translatable feature.
Syntax for that is:

    TRANSLATABLE_MODELS = (
        ('app_label.module_name': ('field1', 'field2', 'field3')),
        ...
    )

Syntax for in model definition is:

    class MyModel(models.Model):
        field1 = models.SomeField()
        field2 = models.SomeField()
        field3 = models.SomeField()

        translatable_fields = ('field1', 'field2', 'field3')

For everything to work you must set USE_I18N = True in your settings
"""
from django.conf import settings
from django.db.models.signals import class_prepared
from django.db.models.fields import NOT_PROVIDED, FieldDoesNotExist
from django.utils.encoding import force_unicode
from django.utils import translation

__version__ = '0.1.1'

FIELD_ATTRIBUTES = ['verbose_name', 'help_text', 'choices', 'max_length', 'default', 'blank', 'null']
AVAILABLE_LANGUAGES = [code for code, name in settings.LANGUAGES]

TRANSLATABLE_MODELS = dict([key.lower(), tuple(value)] for key, value in getattr(settings, 'TRANSLATABLE_MODELS', []))


def get_language():
    lang = translation.get_language()
    return lang if lang in AVAILABLE_LANGUAGES else settings.LANGUAGE_CODE


class LocalizedFieldDescriptor(object):
    """
    Special descriptor object used for localized fields
    and their localazied versions
    """
    def __init__(self, language=None):
        self.language = language

    def __get__(self, instance, owner):
        val = instance.__dict__.get(self._get_field_name())
        return val or instance.__dict__.get(self.field_name)

    def __set__(self, instance, val):
        if self._is_default() and not val:
            val = getattr(instance, self.field_name)
        instance.__dict__[self._get_field_name()] = val
        if self._is_main():
            instance.__dict__[self.field_name] = val

    def _get_field_name(self):
        return "%s_%s" % (self.field_name, self._get_language())

    def _get_language(self):
        return self.language or get_language()

    def _is_main(self):
        return not bool(self.language)

    def _is_default(self):
        return self.language == get_language()

    def contribute_to_class(self, cls, name):
        self.model = cls
        self.field_name = name
        setattr(cls, name, self)


def localize_field(field):
    """
    Create localized fields of given field for AVAILABLE_LANGUAGES
    contribute it to the field.model and create localized property
    only if this is not done yet.
    """
    model = field.model

    def get_attr(name, default=NOT_PROVIDED):
        # May be this function will be used in the future
        attr = attrs.get(name, NOT_PROVIDED)
        return force_unicode(attr) if attr != NOT_PROVIDED else default

    attrs = dict([attr_name, getattr(field, attr_name)] for attr_name in FIELD_ATTRIBUTES if getattr(field, attr_name, NOT_PROVIDED) != NOT_PROVIDED)
    #verbose_name = get_attr('verbose_name', '')
    #help_text = get_attr('help_text', '')
    attrs['editable'] = False
    for lang_code in AVAILABLE_LANGUAGES:
        new_field_name = "%s_%s" % (field.name, lang_code)
        try:
            model._meta.get_field(new_field_name)
        except FieldDoesNotExist:
            pass
        else:
            continue

        if not attrs.get('null') and attrs.get('default', NOT_PROVIDED) == NOT_PROVIDED:
            attrs['default'] = ''

        #attrs['verbose_name'] = '%s_%s' % (verbose_name, lang_code)
        #attrs['help_text'] = "%s (%s version)" % (help_text, lang_code)

        new_field = field.__class__(**attrs)
        new_field.creation_counter = field.creation_counter  # preserve default ordering of fields
        new_field.contribute_to_class(model, new_field_name)

        model.add_to_class(field.name, LocalizedFieldDescriptor(lang_code))

    model.add_to_class(field.name, LocalizedFieldDescriptor())


def get_translatable_fields_names(model, force=False):
    """
    Return list of field names that was marked for translation
    in this model or some of his parents
    """
    try:
        opts = model._meta
    except AttributeError:
        return ()
    module_name = "%s.%s" % (opts.app_label, opts.module_name)

    def get_fields_from_parents():
        fields = ()
        for parent in model.mro()[1:]:
            fields += get_translatable_fields_names(parent, force)
        return fields

    if not hasattr(opts, 'translatable_fields') or force:
        fields = getattr(opts, 'translatable_fields', ())
        fields += TRANSLATABLE_MODELS.get(module_name, ())
        try:
            fields += tuple(model.translatable_fields)
            del model.translatable_fields
        except AttributeError:
            pass
        opts.translatable_fields = tuple(set(fields + get_fields_from_parents()))
    return opts.translatable_fields


def make_model_translatable(model):
    """
    Add localized fields to model if they was defined in the model
    or some of his parents
    """
    opts = model._meta
    trans_fields = get_translatable_fields_names(model, force=True)
    for field_name in trans_fields:
        field = opts.get_field(field_name)
        localize_field(field)


def translate_prepared_models(sender, **kwargs):
    """
    Introspect all Parents of the current sender, and make it translatable.
    Django will automaticaly add fields to his children
    """
    for model in reversed(sender.mro()):
        if not hasattr(model, '_meta'):
            continue
        make_model_translatable(model)

if settings.USE_I18N:
    class_prepared.connect(translate_prepared_models, dispatch_uid="tr@ns#mod3ls")
