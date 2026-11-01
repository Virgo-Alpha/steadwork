"""Request-scoped SQLAlchemy unit of work for the API's SQLite store."""

from copy import deepcopy
from functools import lru_cache

from django.conf import settings
from sqlalchemy import text

from .repositories import SQLAlchemyStoreRepository, create_database
from .store import clear_request_store, set_request_store


@lru_cache(maxsize=4)
def _database(url):
    return create_database(url)


class SQLiteStoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.STORE_BACKEND == "inmemory":
            return self.get_response(request)

        engine, session_factory = _database(settings.DATABASE_URL)
        session = session_factory()
        store_token = None
        try:
            if engine.dialect.name == "sqlite":
                # SQLite's deferred transaction permits two requests to read
                # the same snapshot before either writes. Serialize writes.
                session.execute(text("BEGIN IMMEDIATE"))
            store = SQLAlchemyStoreRepository(session).load()
            session.flush()
            before = deepcopy(store)
            store_token = set_request_store(store)
            response = self.get_response(request)
            if response.status_code < 400:
                SQLAlchemyStoreRepository(session).apply_changes(before, store)
                session.commit()
            else:
                session.rollback()
            return response
        except Exception:
            session.rollback()
            raise
        finally:
            if store_token is not None:
                clear_request_store(store_token)
            session.close()
