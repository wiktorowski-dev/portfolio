from __future__ import annotations

import os
from typing import Any, List, Dict, Optional
from collections import defaultdict
from functools import wraps
import uuid
import asyncio
from unittest.mock import patch
from functools import wraps
import sqlite3
import re


def mysql_to_sqlite(mysql_query):
    # Replace AUTO_INCREMENT with AUTOINCREMENT
    # Replace AUTO_INCREMENT with AUTOINCREMENT
    sqlite_query = re.sub(r'\bAUTO_INCREMENT\b', 'AUTOINCREMENT', mysql_query, flags=re.IGNORECASE)

    # Replace INT with INTEGER
    sqlite_query = re.sub(r'\bINT\b', 'INTEGER', sqlite_query, flags=re.IGNORECASE)

    # Replace VARCHAR with TEXT
    sqlite_query = re.sub(r'\bVARCHAR\(\d+\)\b', 'TEXT', sqlite_query, flags=re.IGNORECASE)

    # Replace enum with TEXT
    sqlite_query = re.sub(r'enum\(.*?\)', 'text', sqlite_query)

    # Replace TIMESTAMP with DATETIME
    sqlite_query = re.sub(r'\bTIMESTAMP\b', 'DATETIME', sqlite_query, flags=re.IGNORECASE)

    # Replace DEFAULT CURRENT_TIMESTAMP with SQLite equivalent
    sqlite_query = re.sub(r'DEFAULT CURRENT_TIMESTAMP', "DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))", sqlite_query, flags=re.IGNORECASE)

    # Remove MySQL-specific ENGINE and CHARSET options
    sqlite_query = re.sub(r'ENGINE=\w+\s*', '', sqlite_query, flags=re.IGNORECASE)
    sqlite_query = re.sub(r'DEFAULT CHARSET=\w+', '', sqlite_query, flags=re.IGNORECASE)

    # Remove any remaining MySQL-specific syntax
    sqlite_query = re.sub(r'`', '', sqlite_query)  # Remove backticks

    # Remove schema from query
    sqlite_query = re.sub(r'(?i)\b(FROM|TABLE|REFERENCES|JOIN|INTO|UPDATE)\s+\w+\.', r'\1 ', sqlite_query, flags=re.IGNORECASE)

    # Remove schema from query
    sqlite_query = re.sub(r'CREATE TABLE', r'CREATE TABLE IF NOT EXISTS', sqlite_query, flags=re.IGNORECASE)

    # Replace %s with ?
    sqlite_query = re.sub(r"\%s", "?", sqlite_query)

    # Replace constraint with constraint name
    sqlite_query = re.sub(r"(?i)\b(constraint)", f"CONSTRAINT S{uuid.uuid4().hex}", sqlite_query, flags=re.IGNORECASE)

    # Remove # and --comments
    sqlite_query = re.sub(r'#.*$', '', sqlite_query, flags=re.MULTILINE)
    sqlite_query = re.sub(r'--.*$', '', sqlite_query, flags=re.MULTILINE)

    if (
            sqlite_query.lower().startswith('start')
    ):
        return None

    return sqlite_query.strip()


class MockCursor:
    def __init__(self, conn: MockConnection, sql_cursor: sqlite3.Cursor):
        self.result = []
        self.conn = conn
        self.cursor = sql_cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        sqlite_query = mysql_to_sqlite(query)
        if not sqlite_query:
            return

        if sqlite_query.lower() == 'commit':
            self.conn.commit()
            return

        if sqlite_query.lower() == 'rollback':
            self.conn.rollback()
            return

        if params:
            self.cursor.execute(sqlite_query, params)
        else:
            self.cursor.execute(sqlite_query)

    def fetchall(self) -> List[Dict[str, Any]]:
        return self.cursor.fetchall()

    def fetchone(self) -> Dict[str, Any]:
        return self.cursor.fetchone()

    @property
    def description(self) -> list:
        return self.cursor.description

    def close(self):
        if self.cursor:
            self.cursor.close()


class MockConnection:
    def __init__(self, sql_db):
        self.database = defaultdict(list)
        self._sqlite_db_conn = sql_db
        self._cursor = None
        self._init_tables()

    def _init_tables(self):
        # Initialize tables by executing SQL files
        # Todo handle SQL Create table dynamic pull tables from S3? Or any other place
        base_dir = os.path.dirname(__file__)

        t_paths = [
            os.path.join(base_dir, '../data/sql_tables/users.sql')
        ]
        for t_path in t_paths:
            with open(t_path, 'r') as f:
                query = f.read()
                self.cursor().execute(query)

    def cursor(self) -> MockCursor:
        if self._cursor is None or self._cursor.cursor is None:
            self._cursor = MockCursor(self, sql_cursor=self._sqlite_db_conn.cursor())
        return self._cursor

    def commit(self):
        self._sqlite_db_conn.commit()

    def rollback(self):
        self._sqlite_db_conn.rollback()

    def close(self):
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        # self._sqlite_db_conn.close()


class AsyncWrapper:
    def __init__(self, sync_obj):
        self._sync_obj = sync_obj

    def __getattr__(self, item):
        attr = getattr(self._sync_obj, item)

        if hasattr(type(self._sync_obj), item):
            # If property
            if isinstance(getattr(type(self._sync_obj), item), property):
                return getattr(self._sync_obj, item)

        if callable(attr):
            # Return an awaitable version of the method
            async def async_method(*args, **kwargs):
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, attr, *args, **kwargs)
            return async_method

        else:
            # If it's not callable, just return it wrapped in a future
            return asyncio.ensure_future(asyncio.sleep(0, result=attr))


class AsyncMockConnection:
    def __init__(self, mock_connector):
        self._mock_connector = mock_connector

    def __await__(self, *args, **kwargs):
        return self._mock_connection().__await__()

    def __getattr__(self, item):
        attr = getattr(self._mock_connector, item)

        if callable(attr):
            # Return an awaitable version of the method
            async def async_method(*args, **kwargs):
                loop = asyncio.get_running_loop()
                sync_result = await loop.run_in_executor(None, attr, *args, **kwargs)
                # Wrap the result to make it async-compatible
                return AsyncWrapper(sync_result)
            return async_method
        else:
            # If it's not callable, just return it wrapped in a future
            return asyncio.ensure_future(asyncio.sleep(0, result=attr))

    async def _mock_connection(self):
        # Simulate some async operation, like establishing a connection
        await asyncio.sleep(0)  # Non-blocking sleep
        return self


def set_sql_env_vars():
    """Set here env vars"""
    os.environ['SQL_SCHEMA'] = 'some_schema'
    pass


def mock_sql_custom_class(cls):
    """
    A decorator to mock MySQL for all methods in a class.
    This version wraps each method in the class with the mock_sql_decorator.
    """
    for attr_name, attr_value in cls.__dict__.items():
        # Check if the attribute is a callable (method) and not a dunder method
        if callable(attr_value) and not attr_name.startswith("__"):
            # Wrap the method with the SQL mocking logic`
            wrapped_method = mock_sql_decorator(attr_value)
            # Replace the original method with the wrapped one
            setattr(cls, attr_name, wrapped_method)

    return cls


def mock_sql_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        set_sql_env_vars()
        # Mock pool creation and connection acquisition
        sql_db = sqlite3.connect(':memory:', check_same_thread=False)

        with (
            patch("aiomysql.connect", side_effect=lambda *a, **b: AsyncMockConnection(MockConnection(sql_db))),
            patch("pymysql.connect", side_effect=lambda *a, **b: MockConnection(sql_db))
        ):
            return func(*args, **kwargs)
    return wrapper
