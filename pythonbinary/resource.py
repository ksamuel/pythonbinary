import os.path

HERE = os.path.dirname(os.path.abspath(__file__))


def filename(*parts: str) -> str:
    return os.path.join(HERE, 'resources', *parts)
