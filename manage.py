"""Django's command-line utility for administrative tasks."""
import os
import sys

from google.auth.exceptions import DefaultCredentialsError
from loguru import logger

try:
    import googleclouddebugger

    googleclouddebugger.enable()
except ImportError:
    pass
except DefaultCredentialsError as error:
    logger.warning(error)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Traidoo.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
