from django.db.models.sql import compiler
from django.db.models.fields import AutoField
from django.db.utils import DatabaseError


class SQLCompiler(compiler.SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False):
        sql, params = super(SQLCompiler, self).as_sql(with_limits=False, with_col_aliases=with_col_aliases)

        if with_limits:
            limits = []
            if self.query.high_mark is not None:
                limits.append('FIRST %d' % (self.query.high_mark - self.query.low_mark))
            if self.query.low_mark:
                if self.query.high_mark is None:
                    val = self.connection.ops.no_limit_value()
                    if val:
                        limits.append('FIRST %d' % val)
                limits.append('SKIP %d' % self.query.low_mark)
            sql = 'SELECT %s %s' % (' '.join(limits), sql[6:].strip())
        return sql, params


class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):
    def _get_seq_name(self, db_table):
        return db_table.upper() + '_SQ'

    def _get_seq_next_value(self, db_table):
        seq_name = self._get_seq_name(db_table)
        if self.connection.ops.firebird_version[0] >= 2:
            seq_txt = 'NEXT VALUE FOR %s' % seq_name
        else:
            seq_txt = 'GEN_ID(%s, 1)' % seq_name
        cursor = self.connection.cursor()
        cursor.execute('SELECT %s FROM rdb$database' % seq_txt)
        id = cursor.fetchone()[0]
        return str(id)

    def _get_pk_next_value(self, db_table, pk_column):
        try:
            return self._get_seq_next_value(db_table)
        except DatabaseError:
            cursor = self.connection.cursor()
            cursor.execute('SELECT MAX(%s) FROM %s' % (pk_column, db_table))
            id = cursor.fetchone()[0]
            if not id:
                id = 0
            return id + 1

    def _last_insert_id(self, cursor, model):
        seq_name = self._get_seq_name(model._meta.db_table)
        cursor.execute('SELECT GEN_ID(%s, 0) FROM rdb$database' % seq_name)
        return cursor.fetchone()[0]

    def _get_sql(self):
        # We don't need quote_name_unless_alias() here, since these are all
        # going to be column names (so we can avoid the extra overhead).
        qn = self.connection.ops.quote_name
        opts = self.query.model._meta
        sql = ['INSERT INTO %s' % qn(opts.db_table)]

        # If primary key field is assigned explicity when a new models instance
        # is created, we don't need to generate a new value (sequece) for pk
        # field and also the pk column will be include en self.query.columns.
        pk_auto = opts.pk and isinstance(opts.pk, AutoField)
        if pk_auto:
            pk_col = opts.pk.column
        pk_include = pk_auto and (pk_col.lower() in self.query.columns)

        # Build columns names
        cols = []
        for c in self.query.columns:
            cols.append(qn(c))
        if not pk_include:
            cols.insert(0, qn(pk_col))
        sql.append('(%s)' % ', '.join(cols))

        # Build values placeholders
        vals = []
        if not pk_include:
            self._pk_val = self._get_pk_next_value(opts.db_table, opts.pk.column)
            vals.append(str(self._pk_val))
        for v in self.query.values:
            vals.append(self.placeholder(*v))
        sql.append('VALUES (%s)' % ', '.join(vals))

        params = self.query.params
        if self.return_id and self.connection.features.can_return_id_from_insert:
            col = "%s.%s" % (qn(opts.db_table), qn(opts.pk.column))
            r_fmt, r_params = self.connection.ops.return_insert_id()
            sql.append(r_fmt % col)
            params = params + r_params

        return ' '.join(sql), params


    def as_sql(self, *args, **kwargs):
        # Fix for Django ticket #14019
        if not hasattr(self, 'return_id'):
            self.return_id = False

        meta = self.query.get_meta()

        if meta.has_auto_field:
            # db_column is None if not explicitly specified by model field
            #auto_field_column = meta.auto_field.db_column or meta.auto_field.column
            sql, params = self._get_sql()
        else:
            sql, params = super(SQLInsertCompiler, self).as_sql(*args, **kwargs)

        return sql, params

    def execute_sql(self, return_id=False):
        # How we avoid to use trigger for pk value generator, the primary key
        # field vale is stored and return it instead use of _last_insert_id
        # which is not safe. If the database is FB 2.0 or latter the RETURNING
        # clause is used.

        self._pk_val = None
        self.return_id = return_id
        cursor = super(SQLCompiler, self).execute_sql(None)
        if not (return_id and cursor):
            return
        if self.connection.features.can_return_id_from_insert:
            return self.connection.ops.fetch_returned_insert_id(cursor)
        if not self._pk_val:
            self._pk_val = self._last_insert_id(cursor, self.query.model)
        return self._pk_val


class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    pass

class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    pass

class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    pass

class SQLDateCompiler(compiler.SQLDateCompiler, SQLCompiler):
    pass

