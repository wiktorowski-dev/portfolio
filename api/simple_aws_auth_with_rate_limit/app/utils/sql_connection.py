import pymysql
import aiomysql
import pymysql.cursors
from pydantic import BaseModel
import json
import boto3
import os
from functools import wraps


def _load_mysql_credentials():
    mysql_creds = json.loads(boto3.client('secretsmanager').get_secret_value(SecretId=os.environ.get('sql_secret'))['SecretString'])
    if not isinstance(mysql_creds['port'], int):
        mysql_creds['port'] = int(mysql_creds['port'])

    if 'username' in mysql_creds:
        mysql_creds['user'] = mysql_creds.pop('username')

    mysql_creds = {k: mysql_creds[k] for k in ('user', 'password', 'host', 'port')}
    return mysql_creds


class SQLConnection:
    def __init__(self, database: str = None):
        creds = _load_mysql_credentials()
        self._creds = creds
        self._con = None
        self._cursor = None
        self._database = database
        self._url = f'mysql+mysqlconnector://{creds["user"]}:{creds["password"]}@{creds["host"]}:{creds["port"]}'
        if self._database:
            self._url += f'/{self._database}'

    @property
    def url(self) -> str:
        return self._url

    def __enter__(self) -> pymysql.cursors.Cursor:
        self._con = pymysql.connect(
            **self._creds
        )
        cursor = self._con.cursor()
        cursor.execute('START TRANSACTION')
        self._cursor = cursor
        return cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If exception, then ROLLBACK
        if exc_type is not None:
            self._cursor.execute("ROLLBACK")
        else:
            self._cursor.execute("COMMIT")

        self._cursor.close()
        self._con.close()

    async def __aenter__(self):
        self._con = await aiomysql.connect(
            **self._creds
        )
        cursor = await self._con.cursor()
        await cursor.execute('START TRANSACTION')
        self._cursor = cursor
        return cursor

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # If exception, then ROLLBACK
        if exc_type is not None:
            await self._cursor.execute("ROLLBACK")
        else:
            await self._cursor.execute("COMMIT")

        await self._cursor.close()
        self._con.close()


def fetch_one_dict(cursor: aiomysql.cursors.Cursor, fetch_result: tuple) -> dict:
    return {k: v for k, v in zip([c[0] for c in cursor.description], fetch_result)}


async def insert_pydantic_object(obj: BaseModel, table_schema: str, conn=None):
    if conn is None:
        async with SQLConnection() as conn:
            await insert_pydantic_object(obj, table_schema, conn)
        return

    cols = ', '.join(obj.dict().keys())
    string_vals = ', '.join(['%s'] * len(obj.dict().keys()))
    query = f"""INSERT INTO {table_schema} ({cols}) VALUES ({string_vals})"""
    await conn.execute(query, tuple(obj.dict().values()))


def cursor_wrapper(func):
    @wraps(func)
    async def wrapper(*args, cursor=None, **kwargs):
        if cursor is None:
            async with SQLConnection() as new_cursor:
                return await func(*args, cursor=new_cursor, **kwargs)
        else:
            return await func(*args, cursor=cursor, **kwargs)
    return wrapper
