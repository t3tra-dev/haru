"""
This module provides the OAuthManager class for handling OAuth 2.0 authentication.
"""

from __future__ import annotations
import os
import hmac
import hashlib
import base64
import json
import time
from datetime import timedelta
from typing import Callable, Any, Optional, List, Dict, Tuple

from .mixins import UserMixin
from ..app import Haru
from ..request import Request
from ..response import Response

__all__ = ['OAuthManager']


class OAuthManager:
    """
    Manages OAuth 2.0 authentication and authorization.

    :param secret_key: Secret key used for token generation and verification.
    :type secret_key: str
    :param auth_endpoint: URL path for the authorization endpoint.
    :type auth_endpoint: str
    :param token_endpoint: URL path for the token endpoint.
    :type token_endpoint: str
    :param token_expiry: Access token expiry duration. Default is 1 hour.
    :type token_expiry: Optional[timedelta]
    :param refresh_token_expiry: Refresh token expiry duration. Default is 30 days.
    :type refresh_token_expiry: Optional[timedelta]
    """

    def __init__(
        self,
        secret_key: str,
        auth_endpoint: str = "/oauth/authorize",
        token_endpoint: str = "/oauth/token",
        token_expiry: Optional[timedelta] = timedelta(hours=1),
        refresh_token_expiry: Optional[timedelta] = timedelta(days=30),
    ):
        self.secret_key = secret_key
        self.auth_endpoint = auth_endpoint
        self.token_endpoint = token_endpoint
        self.token_expiry = token_expiry
        self.refresh_token_expiry = refresh_token_expiry
        self.app: Optional[Haru] = None
        self.user_loader_callback: Optional[Callable[[str], Any]] = None
        self.client_loader_callback: Optional[Callable[[str], Any]] = None
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.auth_codes: Dict[str, Dict[str, Any]] = {}
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def init_app(self, app: Haru):
        """
        Initialize the OAuthManager with the Haru app.

        :param app: The Haru application instance.
        :type app: Haru
        """
        self.app = app
        app.oauth_manager = self
        # Set up routes internally
        app.route(self.auth_endpoint, methods=['GET', 'POST'])(self.authorize_endpoint)
        app.route(self.token_endpoint, methods=['POST'])(self.token_endpoint_handler)

    def user_loader(self, callback: Callable[[str], Any]) -> Callable[[str], Any]:
        """
        Register a callback to load a user given a user ID.

        :param callback: The user loader callback function.
        :type callback: Callable[[str], Any]
        :return: The registered callback.
        :rtype: Callable[[str], Any]
        """
        self.user_loader_callback = callback
        return callback

    def client_loader(self, callback: Callable[[str], Optional[Dict[str, Any]]]) -> Callable[[str], Optional[Dict[str, Any]]]:
        """
        Register a callback to load a client given a client ID.

        :param callback: The client loader callback function.
        :type callback: Callable[[str], Optional[Dict[str, Any]]]
        :return: The registered callback.
        :rtype: Callable[[str], Optional[Dict[str, Any]]]
        """
        self.client_loader_callback = callback
        return callback

    def login(self, request: Request, user: UserMixin) -> None:
        """
        Log in the user by setting the current user in the request.

        :param request: The current request object.
        :type request: Request
        :param user: The user to log in.
        :type user: UserMixin
        """
        request.current_user = user

    def logout(self, request: Request) -> None:
        """
        Log out the current user by clearing the current user in the request.

        :param request: The current request object.
        :type request: Request
        """
        request.current_user = None

    def login_require(self, intents: Optional[List[str]] = None):
        """
        Decorator to protect routes requiring OAuth authentication.

        :param intents: List of required intents (scopes).
        :type intents: Optional[List[str]]
        :return: Decorated function.
        :rtype: Callable
        """
        if intents is None:
            intents = []

        def decorator(func):
            def wrapper(request: Request, *args, **kwargs):
                # Extract access token from Authorization header
                auth_header = request.headers.get('authorization', '')
                if not auth_header.lower().startswith('bearer '):
                    return Response('Unauthorized', status_code=401)
                access_token = auth_header[7:].strip()
                # Validate access token
                token_data = self.validate_access_token(access_token)
                if not token_data:
                    return Response('Unauthorized', status_code=401)
                # Check intents (scopes)
                token_intents = token_data.get('intents', [])
                if not set(intents).issubset(set(token_intents)):
                    return Response('Forbidden', status_code=403)
                # Load user
                user_id = token_data.get('user_id')
                if self.user_loader_callback:
                    user = self.user_loader_callback(user_id)
                    request.current_user = user
                else:
                    request.current_user = None
                return func(request, *args, **kwargs)
            return wrapper
        return decorator

    def generate_token(self, data: Dict[str, Any], expiry: Optional[timedelta]) -> str:
        """
        Generate a signed token with the given data and expiry.

        :param data: Data to include in the token.
        :type data: Dict[str, Any]
        :param expiry: Expiry duration.
        :type expiry: Optional[timedelta]
        :return: Generated token.
        :rtype: str
        """
        token_data = data.copy()
        if expiry is not None:
            expiry_time = time.time() + expiry.total_seconds()
            token_data['expiry'] = expiry_time

        token_json = json.dumps(token_data, separators=(',', ':'))
        token_bytes = token_json.encode('utf-8')
        signature = hmac.new(self.secret_key.encode('utf-8'), token_bytes, hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(token_bytes + signature).decode('utf-8')
        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a token and return its data if valid.

        :param token: The token to validate.
        :type token: str
        :return: Token data if valid, else None.
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            token_bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
            token_data_bytes = token_bytes[:-32]
            signature = token_bytes[-32:]
            expected_signature = hmac.new(self.secret_key.encode('utf-8'), token_data_bytes, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected_signature):
                return None
            token_data = json.loads(token_data_bytes.decode('utf-8'))
            expiry = token_data.get('expiry')
            if expiry is not None and time.time() > expiry:
                return None
            return token_data
        except Exception:
            return None

    def validate_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an access token and return its data if valid.

        :param access_token: The access token to validate.
        :type access_token: str
        :return: Token data if valid, else None.
        :rtype: Optional[Dict[str, Any]]
        """
        return self.validate_token(access_token)

    async def authorize_endpoint(self, request: Request) -> Response:
        """
        Handle the authorization endpoint.

        :param request: The current request object.
        :type request: Request
        :return: The response to send back to the client.
        :rtype: Response
        """
        if request.method == 'GET':
            # Display authorization form
            params = request.args
            client_id = params.get('client_id')
            response_type = params.get('response_type')
            redirect_uri = params.get('redirect_uri')
            state = params.get('state')
            scope = params.get('scope', '')
            if not client_id or response_type != 'code':
                return Response('Invalid request', status_code=400)
            if not self.client_loader_callback:
                return Response('Client loader not configured', status_code=500)
            client = self.client_loader_callback(client_id)
            if not client:
                return Response('Unknown client', status_code=400)
            if redirect_uri not in client.get('redirect_uris', []):
                return Response('Invalid redirect URI', status_code=400)
            # Assume user is already authenticated
            user = request.current_user
            if not user:
                # Redirect to login page or return an error
                return Response('User not authenticated', status_code=401)
            # Display authorization form (for simplicity, we auto-approve)
            # In a real application, you should render a template or prompt the user
            # For now, we proceed to generate the authorization code
            code = self.generate_authorization_code(client_id, user.get_id(), scope.split(), redirect_uri)
            # Redirect back to the client with the authorization code
            redirect_params = {
                'code': code,
            }
            if state:
                redirect_params['state'] = state
            redirect_url = self.build_redirect_uri(redirect_uri, redirect_params)
            return Response(status_code=302, headers={'Location': redirect_url})
        elif request.method == 'POST':
            # Handle form submission (not implemented in this example)
            return Response('Method not allowed', status_code=405)
        else:
            return Response('Method not allowed', status_code=405)

    async def token_endpoint_handler(self, request: Request) -> Response:
        """
        Handle the token endpoint.

        :param request: The current request object.
        :type request: Request
        :return: The response containing the access token or error.
        :rtype: Response
        """
        if request.method != 'POST':
            return Response('Method not allowed', status_code=405)
        # Extract parameters
        params = request.form
        grant_type = params.get('grant_type')
        if grant_type == 'authorization_code':
            code = params.get('code')
            redirect_uri = params.get('redirect_uri')
            client_id, client_secret = self.extract_client_credentials(request)
            if not client_id or not client_secret:
                return Response('Invalid client credentials', status_code=401)
            if not self.client_loader_callback:
                return Response('Client loader not configured', status_code=500)
            client = self.client_loader_callback(client_id)
            if not client or client.get('client_secret') != client_secret:
                return Response('Invalid client credentials', status_code=401)
            # Validate authorization code
            auth_code_data = self.auth_codes.get(code)
            if not auth_code_data:
                return Response('Invalid authorization code', status_code=400)
            if auth_code_data.get('client_id') != client_id:
                return Response('Authorization code does not belong to client', status_code=400)
            if auth_code_data.get('redirect_uri') != redirect_uri:
                return Response('Invalid redirect URI', status_code=400)
            # Generate access token
            access_token_data = {
                'user_id': auth_code_data['user_id'],
                'client_id': client_id,
                'intents': auth_code_data['scope'],
            }
            access_token = self.generate_token(access_token_data, self.token_expiry)
            # Generate refresh token
            refresh_token_data = {
                'user_id': auth_code_data['user_id'],
                'client_id': client_id,
            }
            refresh_token = self.generate_token(refresh_token_data, self.refresh_token_expiry)
            # Remove used authorization code
            del self.auth_codes[code]
            # Return tokens
            response_data = {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': int(self.token_expiry.total_seconds()) if self.token_expiry else None,
                'refresh_token': refresh_token,
            }
            return Response(json.dumps(response_data), content_type='application/json')
        else:
            return Response('Unsupported grant type', status_code=400)

    def generate_authorization_code(self, client_id: str, user_id: str, scope: List[str], redirect_uri: str) -> str:
        """
        Generate an authorization code.

        :param client_id: Client ID.
        :type client_id: str
        :param user_id: User ID.
        :type user_id: str
        :param scope: List of scopes.
        :type scope: List[str]
        :param redirect_uri: Redirect URI.
        :type redirect_uri: str
        :return: Authorization code.
        :rtype: str
        """
        code = base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')
        self.auth_codes[code] = {
            'client_id': client_id,
            'user_id': user_id,
            'scope': scope,
            'redirect_uri': redirect_uri,
            'expiry': time.time() + 600,  # Authorization code valid for 10 minutes
        }
        return code

    def build_redirect_uri(self, base_uri: str, params: Dict[str, str]) -> str:
        """
        Build a redirect URI with query parameters.

        :param base_uri: Base URI.
        :type base_uri: str
        :param params: Query parameters.
        :type params: Dict[str, str]
        :return: Complete redirect URI.
        :rtype: str
        """
        from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
        url_parts = list(urlparse(base_uri))
        query = dict(parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query)
        return urlunparse(url_parts)

    def extract_client_credentials(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract client credentials from the request.

        :param request: The current request object.
        :type request: Request
        :return: Tuple of client_id and client_secret.
        :rtype: Tuple[Optional[str], Optional[str]]
        """
        auth_header = request.headers.get('authorization', '')
        if auth_header.lower().startswith('basic '):
            encoded_credentials = auth_header[6:].strip()
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            client_id, client_secret = decoded_credentials.split(':', 1)
            return client_id, client_secret
        else:
            client_id = request.form.get('client_id')
            client_secret = request.form.get('client_secret')
            return client_id, client_secret
