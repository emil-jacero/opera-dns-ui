import os
import sys
import psycopg2
import logging
import time

from lib.logger import logger_name
'''
    SQL migration DLL's are copied from upstream powerdns
    https://github.com/PowerDNS/pdns/tree/master/modules/gpgsqlbackend
'''

log_name = f'{logger_name}.gpgsql'
log = logging.getLogger(log_name)


class DB:
    def __init__(self, host, port, user, password, db):
        self.log_name = f"{log_name}.{self.__class__.__name__}"
        self.log = logging.getLogger(self.log_name)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db

        self.conn_obj = None
        self.cursor_obj = None

    def connection(self):
        try:
            conn = psycopg2.connect(f"host={self.host} \
                                      port={self.port} \
                                      dbname={self.db} \
                                      user={self.user} \
                                      password={self.password}")
            self.log.debug(
                f"Connected to database [DB: {self.db}@{self.host}:{self.port}]"
            )
            return conn

        except (Exception, psycopg2.Error) as error:
            self.log.error(
                f"Unable to connect to the database [DB: {Config.gpgsql_dbname}@{Config.gpgsql_host}:{Config.gpgsql_port}]"
            )
            self.log.debug(error)
            sys.exit(1)

    def create_cursor(self):
        self.conn_obj = self.connection()
        self.cursor_obj = self.conn_obj.cursor()
        return self.cursor_obj

    def close_all(self):
        try:
            self.cursor_obj.close()
            self.log.debug("Cursor closed")
        except (Exception, psycopg2.Error) as error:
            self.log.error(error)
        try:
            self.conn_obj.close()
            self.log.debug("Connection Closed")
        except (Exception, psycopg2.Error) as error:
            self.log.error(error)

    def commit(self):
        self.log.debug(f"Committing SQL query [{self.cursor_obj}]")
        self.conn_obj.commit()

    def rollback(self):
        self.log.debug(f"Rolling back SQL query [{self.cursor_obj}]")
        self.conn_obj.rollback()


def execute_single_query(host, port, user, password, db, query):
    """
        Run a simple single read query.
    """
    conn = DB(host, port, user, password, db)
    try:
        cursor = conn.create_cursor()
        cursor.execute(query)
        record = cursor.fetchone()[0]
        return record

    except (Exception, psycopg2.Error) as error:
        log.error(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close_all()


def execute_sql(host, port, user, password, db, file_path):
    conn = DB(host, port, user, password, db)
    try:
        with conn.create_cursor() as cursor:
            cursor.execute(open(file_path, "r").read())
        conn.commit()
        log.info(f'Committed schema to database: {file_path}')

    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        log.error(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close_all()


def db_connect_check(host, port, user, password):
    conn = None
    try:
        conn_string = f"host={host} port={port} user={user} password={password} connect_timeout=1"
        conn = psycopg2.connect(conn_string)
        return True
    except:
        return False
    finally:
        if conn is not None:
            conn.close()


def wait_for_db(host, port, user, password, timeout=30):
    time_end = time.time() + timeout
    while db_connect_check(host, port, user, password) is False:
        if time.time() > time_end:
            log.error('Could not connect to the database')
            sys.exit(1)
        log.info(
            f"Waiting for postgres at: {host}:{port}"
        )
        time.sleep(5)
    log.info(f"Successfully connected to database ({host}:{port})")


def has_existing_default_user(host, port, user, password, db, default_user):
    """
        Query for table domains and records
        If they exist and has content return true
    """
    query = f"select exists(select id, uid from \"user\" where id = 1 and uid = '{default_user}');"
    record = execute_single_query(host, port, user, password, db, query)
    return record
