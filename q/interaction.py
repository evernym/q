import sqlite3
import time


class Interaction:
    def __init__(self, thid, last_received_t=None, last_sent_t=None, data=None, db_fresh_t=None):
        self.thid = thid
        self.last_received_t = last_received_t
        self.last_sent_t = last_sent_t
        self.data = data
        self.db_fresh_t = int(time.time()) if db_fresh_t is None else db_fresh_t
    def __iter__(self):
        yield self.thid
        yield self.last_received_t
        yield self.last_sent_t
        yield self.data
        yield self.db_fresh_t
    def __str__(self):
        return '(' + ', '.join([str(x) for x in self]) + ')'
    @classmethod
    def from_row(cls, row):
        return Interaction(row[0], row[1], row[2], row[3], int(time.time()))

class _TransCursor:
    def __init__(self, db):
        self.conn = db.conn
        self.cursor = None

    def __enter__(self):
        self.cursor = self.conn.cursor()
        self.cursor.execute('BEGIN;')
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()


_CLEANUP_AFTER_SECS = 86400*30

class Database:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self._last_cleanup_t = int(time.time())
        c = self.conn.cursor()
        c.execute("select count(*) from sqlite_master where type = 'table' and name not like 'sqlite_%';")
        r = c.fetchone()
        if not r or (r[0] == 0):
            c.execute('create table interactions (thid VARCHAR(64) PRIMARY KEY NOT NULL, last_received_t INTEGER, last_sent_t INTEGER, data BLOB)')
            c.execute('create table kvstore (key VARCHAR(32) PRIMARY KEY NOT NULL, value INTEGER)')
            self.conn.commit()
        else:
            c.execute('select value from kvstore where key=?', ('last_cleanup_t',))
            r = c.fetchone()
            if r:
                self._last_cleanup_t = r[0]

    @property
    def last_cleanup_t(self):
        return self._last_cleanup_t

    def cleanup(self, force=False):
        now = int(time.time())
        cutoff = now - _CLEANUP_AFTER_SECS
        if force or self.last_cleanup_t < cutoff:
            with _TransCursor(self) as c:
                c.execute('delete from interactions where ' +
                          '(last_received_t is null and last_sent_t < ?) ' +
                          'or (last_received_t is < ? and last_sent_t is null) ' +
                          'or (last_received_t is < ? and last_sent_t < ?)', (cutoff, cutoff, cutoff, cutoff))
                c.execute("update kvstore set value=? where key='last_cleanup_t'", (now,))
            self._last_cleanup_t = now

    def get_interaction(self, thid):
        c = self.conn.cursor()
        c.execute("select * from interactions where thid = ?", (thid,))
        row = c.fetchone()
        if row:
            return Interaction.from_row(row)

    def set_interaction(self, inter: Interaction):
        with _TransCursor(self) as c:
            c.execute('replace into interactions (thid, last_received_t, last_sent_t, data) values (?, ?, ?, ?)',
                      (inter.thid, inter.last_received_t, inter.last_sent_t, inter.data))
            inter.db_fresh_t = int(time.time())
        self.cleanup()

    def delete_interaction(self, x):
        if isinstance(x, Interaction):
            x = x.thid
        with _TransCursor(self) as c:
            c.execute('delete from interactions where thid=?', (x,))
        self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
