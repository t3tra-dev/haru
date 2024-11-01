import haru
from haru import Haru, Request
from haru.ui import Page, Div, Br
from haru.ui.utils import Markdown

app = Haru(__name__)


@app.route("/")
def index(req: Request):
    return Page(
        Div(
            Markdown(
                f"# Hello, world!\n\nWelcome to Haru/{haru.__version__}, the Python framework for web applications."
            ),
            Br(),
            Div(f"request info: {req.method} {req.path} {req.headers}"),
        )
    )


@app.route("/user/<username:str>")
def user(req: Request):
    return Page(Markdown(f"# Hello, {req.params['username']}!"))


@app.errorhandler(404)
def not_found(req: Request, exc: Exception):
    return Page(Markdown("# Not found.\n\nThe page you are looking for does not exist.")), 404


app.run()
