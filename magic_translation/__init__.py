"""
When this application is imported then it will attach a handler to
class_prepared signal. Then handler mark models as translatable
if they has a `translatable_fields` attribute or was described in
`settings.TRANSLATABLE_MODELS` or some of the model parents are marked
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
from django.utils import translation

__version__ = '0.2.0'
__all__ = ['localize_field', 'get_translatable_fields_names', 'make_model_translatable']

FIELD_ATTRIBUTES = [
    'verbose_name', 'help_text', 'choices',
    'max_length', 'default', 'blank', 'null',
]
AVAILABLE_LANGUAGES = [code for code, name in settings.LANGUAGES]

TRANSLATABLE_MODELS = dict(
    (model.lower(), tuple(fields))
    for model, fields in getattr(settings, 'TRANSLATABLE_MODELS', [])
)


def get_language():
    lang = translation.get_language()
    return lang if lang in AVAILABLE_LANGUAGES else settings.LANGUAGE_CODE


class LocalizedFieldDescriptor(object):
    """
    Special descriptor object used for localized fields
    and their localazied versions

    """
    def __init__(self, language=None):
        self._language = language

    def __get__(self, instance, owner):
        if not instance:
            return self
        val = instance.__dict__.get(self.localized_field_name)
        return val or instance.__dict__.get(self.field_name)

    def __set__(self, instance, val):
        if self.is_default and not val:
            val = getattr(instance, self.field_name)
        instance.__dict__[self.localized_field_name] = val
        if self.is_main:
            instance.__dict__[self.field_name] = val

    @property
    def language(self):
        return self._language or get_language()

    @property
    def localized_field_name(self):
        return "%s_%s" % (self.field_name, self.language)

    @property
    def is_main(self):
        return not bool(self._language)

    @property
    def is_default(self):
        return self._language == get_language()

    def contribute_to_class(self, cls, name):
        self.model = cls

        if self._language is None:
            self.field_name = attr_name = name
        else:
            if name.endswith('_%s' % self._language):
                name = name[:-(len(self._language) + 1)]
            self.field_name = name
            attr_name = "%s_%s" % (name, self._language)

        setattr(cls, attr_name, self)


def localize_field(field):
    """
    Create localized fields of given field for AVAILABLE_LANGUAGES
    contribute it to the field.model and create localized property
    only if this is not done yet.

    """
    model = field.model

    attrs = dict(
        (attr_name, getattr(field, attr_name))
        for attr_name in FIELD_ATTRIBUTES
        if getattr(field, attr_name, NOT_PROVIDED) != NOT_PROVIDED
    )
    attrs['editable'] = False

    for lang_code in AVAILABLE_LANGUAGES:
        new_field_name = "%s_%s" % (field.name, lang_code)
        try:
            model._meta.get_field(new_field_name)
        except FieldDoesNotExist:
            pass
        else:
            continue

        if not attrs.get('null'):
            if attrs.get('default', NOT_PROVIDED) == NOT_PROVIDED:
                attrs['default'] = ''

        # Create new field with the same class as original one
        new_field = field.__class__(**attrs)
        # Preserve default ordering of fields
        new_field.creation_counter = field.creation_counter
        # Add the new field into the model
        new_field.contribute_to_class(model, new_field_name)

        # Add Localized descriptor for the new localized field
        model.add_to_class(new_field_name, LocalizedFieldDescriptor(lang_code))

    # Add magic descriptor for the original field name
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
    Introspect all parents of the current sender, and make them translatable.
    Django will automaticaly add fields to theirs children

    """
    for model in reversed(sender.mro()):
        if not hasattr(model, '_meta'):
            continue
        make_model_translatable(model)


if settings.USE_I18N:
    class_prepared.connect(translate_prepared_models, dispatch_uid="tr@ns#mod3ls")
