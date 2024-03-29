import sys
import kinterbasdb as Database

from django.db.backends.creation import BaseDatabaseCreation

TEST_MODE = 0

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated Firebird column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    #
    # Any format strings starting with "qn_" are quoted before being used in the
    # output (the "qn_" prefix is stripped before the lookup is performed.

    data_types = {
        'AutoField':         'integer',
        'BooleanField':      'smallint',
        'CharField':         'varchar(%(max_length)s)',
        'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
        'DateField':         'date',
        'DateTimeField':     'timestamp',
        'DecimalField':      'decimal(%(max_digits)s, %(decimal_places)s)',
        'FileField':         'varchar(%(max_length)s)',
        'FilePathField':     'varchar(%(max_length)s)',
        'FloatField':        'double precision',
        'IntegerField':      'integer',
        'BigIntegerField':   'bigint',
        'IPAddressField':    'char(15)',
        'NullBooleanField':  'integer',
        'OneToOneField':     'integer',
        'PositiveIntegerField': 'integer CHECK (%(qn_column)s >= 0)',
        'PositiveSmallIntegerField': 'smallint CHECK (%(qn_column)s >= 0)',
        'SlugField':         'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField':         'blob sub_type 1',
        'TimeField':         'time',
    }

    def sql_for_inline_foreign_key_references(self, field, known_models, style):
        # Always pending
        return [], TEST_MODE < 2

    def sql_for_pending_references(self, model, style, pending_references):
        if TEST_MODE < 2:
            final_output = super(DatabaseCreation, self).sql_for_pending_references(model, style, pending_references)
            return ['%s ON DELETE CASCADE;' % s[:-1] for s in final_output]
        return []

    def sql_remove_table_constraints(self, model, references_to_delete, style):
        if TEST_MODE < 2:
            return super(DatabaseCreation, self).sql_remove_table_constraints(model, references_to_delete, style)
        return []

    def _get_connection_params(self, **overrides):
        settings_dict = self.connection.settings_dict
        conn_params = {
            'charset': 'UNICODE_FSS'
        }
        conn_params['database'] = settings_dict['NAME']
        if settings_dict['HOST']:
            conn_params['host'] = settings_dict['HOST']
        if settings_dict['PORT']:
            conn_params['port'] = settings_dict['PORT']
        if settings_dict['USER']:
            conn_params['user'] = settings_dict['USER']
        if settings_dict['PASSWORD']:
            conn_params['password'] = settings_dict['PASSWORD']
        conn_params.update(settings_dict['OPTIONS'])
        conn_params.update(overrides)
        return conn_params

    def _rollback_works(self):
        cursor = self.connection.cursor()
        cursor.execute('CREATE TABLE ROLLBACK_TEST (X INT)')
        self.connection._commit()

        cursor.execute('INSERT INTO ROLLBACK_TEST (X) VALUES (8)')
        self.connection._rollback()

        cursor.execute('SELECT COUNT(X) FROM ROLLBACK_TEST')
        count, = cursor.fetchone()

        cursor.execute('DROP TABLE ROLLBACK_TEST')
        #self.connection._commit()

        return count == 0

    def _create_database(self, test_database_name):
        params = self._get_connection_params(database=test_database_name)
        connection = Database.create_database("""
                        CREATE DATABASE '%(database)s'
                        USER '%(user)s'
                        PASSWORD '%(password)s'
                        DEFAULT CHARACTER SET %(charset)s;""" % params
        )
        connection.execute_immediate("CREATE EXCEPTION teste '';")
        connection.commit()
        #connection.close()

    def _create_test_db(self, verbosity, autoclobber):
        "Internal implementation - creates the test db tables."
        suffix = self.sql_table_creation_suffix()
        test_database_name = self._get_test_db_name()
        qn = self.connection.ops.quote_name

        try:
            self._create_database(test_database_name)
            if verbosity >= 1:
                print "Database %s created..." % test_database_name
        except Exception, e:
            sys.stderr.write("Got an error creating the test database: %s\n" % e)
            if not autoclobber:
                confirm = raw_input("Type 'yes' if you would like to try deleting the test database '%s', or 'no' to cancel: " % test_database_name)
            if autoclobber or confirm == 'yes':
                try:
                    if verbosity >= 1:
                        print "Destroying old test database..."
                    self._destroy_test_db(test_database_name, verbosity)
                    if verbosity >= 1:
                        print "Creating test database..."
                    self._create_database(test_database_name)
                    if verbosity >= 1:
                        print "Database %s created..." % test_database_name

                except Exception, e:
                    sys.stderr.write("Got an error recreating the test database: %s\n" % e)
                    sys.exit(2)
            else:
                print "Tests cancelled."
                sys.exit(1)

        return test_database_name


    def _destroy_test_db(self, test_database_name, verbosity):
        connection = Database.connect(**self._get_connection_params(database=test_database_name))
        connection.drop_database()
        #connection.close()

