from Traidoo.wsgi import application

try:
    import googleclouddebugger
    googleclouddebugger.enable()
except ImportError:
    pass

app = application
