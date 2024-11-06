from haru import Haru, Request, Response
from haru.auth import AuthManager, UserMixin

from datetime import timedelta

app = Haru(__name__)
auth_manager = AuthManager(
    secret_key="your-secret-key", session_expiry=timedelta(days=7)
)
auth_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

    def get_id(self) -> str:
        return str(self.id)


@auth_manager.user_loader_callback
def load_user(user_id: str):
    # temp
    if user_id == "1":
        return User(user_id="1", username="john")
    return None


@app.route("/login", methods=["POST"])
def login(req: Request):
    username = req.form.get("username")
    password = req.form.get("password")
    if username == "john" and password == "secret":
        user = User(user_id="1", username="john")
        req.login(user)
        return Response("Logged in!")
    else:
        return Response("Invalid credentials", status_code=401)


@app.route("/logout")
def logout(req: Request):
    req.logout()
    return Response("Logged out!")


@app.route("/protected")
def protected(req: Request):
    if req.current_user is not None and req.current_user.is_authenticated:
        return Response(f"Hello, {req.current_user.username}!")
    else:
        return Response("Unauthorized", status_code=401)


app.run()
