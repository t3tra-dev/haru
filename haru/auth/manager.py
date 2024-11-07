from __future__ import annotations
import hmac
import hashlib
import base64
import json
import time
from datetime import timedelta
from typing import Callable, Any, Optional

from .mixins import UserMixin
from ..app import Haru
from ..request import Request

__all__ = ["AuthManager"]


class AuthManager:
    """
    Manages user authentication and session handling.
    """

    def __init__(
        self, secret_key: str,
        session_expiry: Optional[timedelta] = timedelta(days=7),
        session_cookie_name: Optional[str] = "session"
    ):
        self.secret_key = secret_key
        self.session_expiry = session_expiry
        self.user_loader: Optional[Callable[[str], Any]] = None
        self.session_cookie_name = session_cookie_name
        self.app = None  # Will be set when initialized with the app

    def init_app(self, app: Haru):
        """
        Initialize the AuthManager with the Haru app.
        """
        self.app = app
        app.auth_manager = self

    def user_loader_callback(self, callback: Callable[[str], Any]):
        """
        Set the user loader callback function.
        """
        self.user_loader = callback

    def generate_session_data(self, user_id: str) -> str:
        """
        Generate signed session data for the given user ID.
        """
        session_data = {"user_id": user_id, "expiry": None}
        if self.session_expiry is not None:
            expiry_time = time.time() + self.session_expiry.total_seconds()
            session_data["expiry"] = expiry_time

        session_json = json.dumps(session_data)
        session_bytes = session_json.encode("utf-8")

        signature = hmac.new(
            self.secret_key.encode("utf-8"), session_bytes, hashlib.sha256
        ).hexdigest()

        session_str = base64.urlsafe_b64encode(session_bytes).decode("utf-8")
        session_cookie_value = f"{session_str}|{signature}"

        return session_cookie_value

    def verify_session_data(self, session_cookie_value: str) -> Optional[dict]:
        """
        Verify the session cookie value and return the session data if valid.
        """
        try:
            session_str, signature = session_cookie_value.split("|")
            session_bytes = base64.urlsafe_b64decode(session_str.encode("utf-8"))
            expected_signature = hmac.new(
                self.secret_key.encode("utf-8"), session_bytes, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                return None
            session_data = json.loads(session_bytes.decode("utf-8"))

            expiry = session_data.get("expiry")
            if expiry is not None and time.time() > expiry:
                return None

            return session_data

        except Exception:
            return None

    def login(self, request: Request, user: UserMixin):
        """
        Log in the user and set the session cookie.
        """
        session_cookie_value = self.generate_session_data(user.get_id())
        # Store the cookie to be set in request
        request._auth_cookies = getattr(request, "_auth_cookies", [])
        request._auth_cookies.append(
            ("set", self.session_cookie_name, session_cookie_value)
        )

    def logout(self, request: Request):
        """
        Log out the user and delete the session cookie.
        """
        # Store the cookie to be deleted in request
        request._auth_cookies = getattr(request, "_auth_cookies", [])
        request._auth_cookies.append(("delete", self.session_cookie_name))

    def load_user(self, request: Request) -> Optional[Any]:
        """
        Load the user from the session cookie.
        """
        session_cookie_value = request.cookies.get(self.session_cookie_name)
        if not session_cookie_value:
            return None
        session_data = self.verify_session_data(session_cookie_value)
        if not session_data:
            return None
        user_id = session_data.get("user_id")
        if self.user_loader:
            return self.user_loader(user_id)
        return None
