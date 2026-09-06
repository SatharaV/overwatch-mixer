"""Owervach TMixer application package.

Central app metadata. Kept import-light to avoid circular imports.
"""

from owervach_tmixer.core.version import get_version_info

_v_info = get_version_info()

APP_TITLE = "Owervach TMixer"
APP_NAME = "owervach-tmixer"
ORG_NAME = "OwervachTMixer"
__version__ = _v_info.version
VERSION_INFO = _v_info
