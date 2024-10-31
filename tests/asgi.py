import logging

from haru import Haru, Request
from haru.middlewares import LoggerMiddleware

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Haru(__name__, asgi=True)
app.add_middleware(LoggerMiddleware(logger=logger))


@app.route("/")
def index(req: Request):
    return "Hello, world!"


@app.route("/user/<username:str>")
def user(req: Request):
    return f'Hello, {req.params["username"]}!'


@app.errorhandler(404)
def not_found(req: Request, exc: Exception):
    return "Not found.", 404


asgi_app = app.asgi_app()
