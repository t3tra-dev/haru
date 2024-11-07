# app.py

from typing import Any, Dict, Optional
from haru import Haru, Request, Response
from haru.oauth import OAuthManager, UserMixin

app = Haru(__name__)


oauth_manager = OAuthManager(secret_key='your-secret-key')
oauth_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_id: str, username: str):
        self.id = user_id
        self.username = username

    def get_id(self) -> str:
        return self.id


@oauth_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    if user_id == '1':
        return User(user_id='1', username='john')
    return None


@oauth_manager.client_loader
def load_client(client_id: str) -> Optional[Dict[str, Any]]:
    if client_id == 'client_123':
        return {
            'client_id': 'client_123',
            'client_secret': 'secret_456',
            'redirect_uris': ['http://localhost:8000/callback'],
            'intents': ['read', 'write'],
        }
    return None


@app.route('/login', methods=['GET', 'POST'])
def login(request: Request):
    if request.method == 'GET':
        return Response('Login Form', content_type='text/html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'john' and password == 'secret':
            user = User(user_id='1', username='john')
            oauth_manager.login(request, user)
            return Response('Logged in')
        else:
            return Response('Invalid credentials', status_code=401)


@app.route('/logout')
def logout(request: Request):
    oauth_manager.logout(request)
    return Response('Logged out')


@app.route('/protected')
@oauth_manager.login_require(intents=['read'])
def protected_resource(request: Request):
    user = request.current_user
    return Response(f'Hello, {user.username}!')


app.run()
