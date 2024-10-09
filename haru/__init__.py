"""
haru
~~~~~~~~~~~~~~~~~~~

The Python framework for web applications.

:copyright: (c) 2024 t3tra
:license: MIT, see LICENSE for more details.

"""


__title__ = 'haru'
__author__ = 't3tra'
__license__ = 'MIT'
__copyright__ = 'Copyright 2024-present t3tra'
__version__ = '0.0.1a2'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import logging
from typing import NamedTuple, Literal

__all__ = ['middlewares', 'ui', 'webapi', 'Haru', 'request', 'Blueprint', 'FileWrapper', 'BytesWrapper']

from . import middlewares
from . import ui
from . import webapi
from .app import Haru
from .request import request
from .blueprint import Blueprint
from .wrappers import FileWrapper, BytesWrapper


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(major=0, minor=0, micro=1, releaselevel='alpha', serial=1)

logging.getLogger(__name__).addHandler(logging.NullHandler())

del logging, NamedTuple, Literal, VersionInfo
