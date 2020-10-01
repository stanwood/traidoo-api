import logging

import google.cloud.logging
from Traidoo.wsgi import application

log_client = google.cloud.logging.Client()
log_client.setup_logging(log_level=logging.DEBUG)

try:
    import googleclouddebugger

    googleclouddebugger.enable()
except ImportError:
    pass


app = application
