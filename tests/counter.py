from haru import Haru, Request
from haru.ui import Page


view = Page("Hello, World!")

view.dispatch_info(title='Document Title')

app = Haru(__name__)


@app.route('/')
def index(req: Request):
    return view


app.run()
