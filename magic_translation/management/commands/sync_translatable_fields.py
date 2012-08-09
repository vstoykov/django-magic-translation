# -*- coding: utf-8 -*-
"""
Detect new translatable fields in all models and sync database structure.

You will need to execute this command in two cases:

    1. When you add new languages to settings.LANGUAGES.
    2. When you add new translatable fields to your models.

Credits: Heavily inspired by django-transmeta's sync_transmeta_db command.
"""
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.db.models.loading import get_models


AVAILABLE_LANGUAGES = [code for code, name in settings.LANGUAGES]


class Command(NoArgsCommand):
    help = ("This command must be run after adding new field for translation\n"
            "or after adding new translatabale language")

    option_list = NoArgsCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to '
                'sync.  Defaults to using the "default" database.'),
    )

    def handle(self, *args, **options):
        self.connection = connections[options.get('database')]

        for model in get_models():
            self.sync_model(model)

    def sync_model(self, model):
        """
        Check if model has translatable fields and if some of this
        fields are not in the database then execute SQL to put it there
        """
        opts = model._meta
        if not getattr(opts, 'translatable_fields', ()):
            return
        introspection = self.connection.introspection
        cursor = self.connection.cursor()
        db_columns = [f[0] for f in introspection.get_table_description(cursor, opts.db_table)]
        for field in self.get_translatable_fields(opts):
            for lang in AVAILABLE_LANGUAGES:
                field_name = "%s_%s" % (field.name, lang)
                if field_name not in db_columns:
                    self.add_field(model, field_name)

    def get_translatable_fields(self, opts):
        return [field for field, model in opts.get_fields_with_model() if not model and field.name in opts.translatable_fields]

    def add_field(self, model, field_name):
        """
        Generete ALTER SQL for given field and execute it
        """
        opts = model._meta
        field = opts.get_field(field_name)
        style = no_style()
        qn = self.connection.ops.quote_name
        col_type = field.db_type(self.connection)

        field_output = [style.SQL_FIELD(qn(field.column)),
                     style.SQL_COLTYPE(col_type)]
        if not field.null:
                field_output.append(style.SQL_KEYWORD('NOT NULL'))

        sql_output = "ALTER TABLE %s ADD COLUMN %s;" % (
                    qn(opts.db_table), ' '.join(field_output))

        # This is for debuging purpose only but for now I will not remove it
        # Let's stay for informatvity
        print "%s.%s.%s\n\t%s\n" % (opts.app_label, model.__name__, field.name, sql_output)
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_output)
        except Exception:
            transaction.rollback_unless_managed()
            raise
        else:
            transaction.commit_unless_managed()
