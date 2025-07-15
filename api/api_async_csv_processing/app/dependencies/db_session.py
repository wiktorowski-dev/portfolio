from fastapi import Request


async def get_db_session(request: Request):
    """
    Dependency to get the database session from the request state.
    """
    return request.app.state.session_factory
