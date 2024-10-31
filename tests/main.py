from haru import Haru, Request

app = Haru(__name__)


@app.route('/')
def index(req: Request):
    return 'Hello, world!'


@app.route('/user/<username:str>')
def user(req: Request):
    return f'Hello, {req.params["username"]}!'


@app.errorhandler(404)
def not_found(req: Request, exc: Exception):
    return 'Not found.', 404


app.run()
