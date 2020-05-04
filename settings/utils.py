from .models import Setting


def get_settings():
    return Setting.objects.first()
