import os.path

HERE = os.path.dirname(__file__)


def filename(*parts: str) -> str:
    return os.path.join(HERE, 'resources', *parts)
