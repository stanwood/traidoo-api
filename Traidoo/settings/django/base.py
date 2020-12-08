AUTH_USER_MODEL = "users.User"
ALLOWED_HOSTS = ["*"]
APPEND_SLASH = False
ROOT_URLCONF = "Traidoo.urls"
SITE_ID = 1
WSGI_APPLICATION = "Traidoo.wsgi.application"
INTERNAL_IPS = ["91.226.199.9", "127.0.0.1"]
