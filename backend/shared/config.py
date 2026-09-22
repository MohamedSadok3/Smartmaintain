import os
from dotenv import load_dotenv

load_dotenv()


def get_env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and value is None:
        raise RuntimeError(f"Environment variable {name} is required.")
    return value
