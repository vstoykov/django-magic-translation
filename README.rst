django-magic-translation
========================

Another application that try to make django translatable to different
languages easier.

How it's work
-------------

When this application is imported then it will attach a handler to
``class_prepared`` signal. Then handler mark models as translatable
if they has a ``translatable_fields`` attribute or was described in
``settings.TRANSLATABLE_MODELS`` or some of the model's parents are
marked for translation.

Describing in ``settings.py`` is for models that can't be touched
(from system installed app), but we want to have translatable feature.

Install
--------

You can use ``pip`` to installit directly from GitHub::

    pip install git+https://github.com/vstoykov/django-magic-translation.git


Configure
---------

To enable translations in your settings set::

    USE_I18N = True


Then you can configure models by two ways. In your ``settings`` you can
use this kind of configuration (mostly for external models)::

    TRANSLATABLE_MODELS = (
        ('app_label.module_name': ('field1', 'field2', 'field3')),
        ...
    )


And in your models you can use ``translatable_fields`` attribute::

    class MyModel(models.Model):
        field1 = models.SomeField()
        field2 = models.SomeField()
        field3 = models.SomeField()

        translatable_fields = ('field1', 'field2', 'field3')


Migrating the database
-----------------------
Migrating the database can be done by two ways\:

1. Using South (prefered) - for your apps and optionally for external apps with  ``SOUTH_MIGRATION_MODULES`` configuration in your settings.py

2. Using ``sync_translatable_fields`` managemend command from this app. - This can be used if you don't use South or for external apps if you don't want to mess with ``SOUTH_MIGRATION_MODULES``.


If you use Mezzanine
====================

Because Mezzanine doesn't have multilingual support you can put this in your
settings to enable transltion for Mezzanine models::

    TRANSLATABLE_MODELS = (
        ('core.Displayable', ['title', '_meta_title', 'description']),
        ('core.RichText', ['content']),
        ('galleries.GalleryImage', ['description']),
        ('forms.Form', ['button_text', 'response', 'email_subject', 'email_message']),
        ('forms.Field', ['label', 'choices', 'default', 'placeholder_text', 'help_text'])
    )


Also if you are using old Django (<1.4) you can use
``magic_translation.middleware.LocaleMiddleware`` to enable language prefixes in
your urls. If you have URLs that you don't want to localize, then you need to
add ``NOT_LOCALIZED_URLS`` in your setings like this::

    NOT_LOCALIZED_URLS = (
        '/edit',
        '/sitemap.xml',
    )
