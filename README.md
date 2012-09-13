django-magic-translation
========================

Another application that try to make django translatable to different langues easier.

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


Migrating the database can be done by two ways:

1. Using South for your apps
2. Using sync_translatable_fields managemend command from this app to all
models that are in third party application


For everything to work you must set USE_I18N = True in your settings