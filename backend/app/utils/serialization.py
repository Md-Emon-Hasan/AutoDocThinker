def to_dict(obj) -> dict:
    return obj if isinstance(obj, dict) else obj.__dict__
