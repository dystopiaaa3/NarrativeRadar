from .database import get_session


def session():
    return get_session()