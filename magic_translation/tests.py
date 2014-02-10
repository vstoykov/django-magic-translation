"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.db import models
from django.conf import settings
from django.utils import translation

from magic_translation import make_model_translatable


class TranslationTest(TestCase):
    def setUp(self):
        class Model(models.Model):
            """
            Class that will be marked for translations
            """
            title = models.CharField(max_length=64)
            description = models.TextField()

            translatable_fields = ('title', 'description',)

        make_model_translatable(Model)

        self.model = Model
        self.instance = Model()

    def test_add_translated_fields(self):
        model = self.model

        for code, name in settings.LANGUAGES:
            localized_title_attr = 'title_%s' % code
            localized_description_attr = 'description_%s' % code

            # Check for LocalizedFieldDescriptor in the model
            self.assertTrue(hasattr(model, localized_title_attr))
            self.assertTrue(hasattr(model, localized_description_attr))

    def test_asigment_logc(self):
        instance = self.instance

        for code, name in settings.LANGUAGES:
            localized_title_attr = 'title_%s' % code
            localized_description_attr = 'description_%s' % code

            test_string = 'TeSt %s language' % code
            instance.title = test_string
            setattr(instance, localized_description_attr, test_string)

            self.assertEquals(test_string, getattr(instance, localized_title_attr))
            if code == translation.get_language():
                self.assertEqual(test_string, instance.description)
            else:
                self.assertNotEqual(test_string, instance.description)
