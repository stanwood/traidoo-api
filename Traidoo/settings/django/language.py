from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent
LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = False
LANGUAGES = [
  ('de', _('German')),
  ('en', _('English')),
]
LOCALE_PATHS = [
    BASE_DIR.joinpath('locale'),
]
