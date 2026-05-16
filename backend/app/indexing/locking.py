from threading import RLock


def new_lock() -> RLock:
    return RLock()
