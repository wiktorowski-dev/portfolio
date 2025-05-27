import os

from app.utils.sql_connection import fetch_one_dict, cursor_wrapper


@cursor_wrapper
async def get_internal_data(cursor=None) -> list[dict] | None:
    query = f'SELECT * FROM {os.environ["SQL_SCHEMA"]}.internal_data'
    await cursor.execute(query)

    fetch = await cursor.fetchall()
    if not fetch:
        return None

    return [fetch_one_dict(cursor, fetch_result=x) for x in fetch]
