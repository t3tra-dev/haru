"""
This module initializes and imports all the built-in middleware components for the Haru web framework.
Middleware components in this module provide functionality such as authentication, rate-limiting,
logging, caching, and security features like CSRF protection and CORS handling.

Each middleware class in this module can be used to enhance request/response processing
in Haru applications.

Available built-in middleware:

- `BasicAuthMiddleware`: Provides Basic Authentication.
- `BearerAuthMiddleware`: Provides Bearer Token Authentication.
- `BodyLimitMiddleware`: Enforces request body size limits.
- `CacheMiddleware`: Caches responses to improve performance.
- `CORSMiddleware`: Handles Cross-Origin Resource Sharing (CORS) headers.
- `CSRFProtectionMiddleware`: Protects against Cross-Site Request Forgery (CSRF) attacks.
- `IPRestrictionMiddleware`: Restricts access based on IP addresses.
- `LoggerMiddleware`: Logs incoming requests and responses.
"""

__all__ = [
    'BasicAuthMiddleware',
    'BearerAuthMiddleware',
    'BodyLimitMiddleware',
    'CacheMiddleware',
    'CORSMiddleware',
    'CSRFProtectionMiddleware',
    'IPRestrictionMiddleware',
    'LoggerMiddleware',
]

from .basic_auth import BasicAuthMiddleware
from .bearer_auth import BearerAuthMiddleware
from .body_limit import BodyLimitMiddleware
from .cache import CacheMiddleware
from .cors import CORSMiddleware
from .csrf_protection import CSRFProtectionMiddleware
from .ip_restriction import IPRestrictionMiddleware
from .logger import LoggerMiddleware
