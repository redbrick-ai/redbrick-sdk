"""Check the version of the SDK."""
from redbrick.utils import version_check  # pylint: disable=cyclic-import

__version__ = version_check.get_version()
version_check.version_check()
