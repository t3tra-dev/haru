from haru import Haru, Request
from haru.ui import State, Page, Div, H1, Button

count = State(0)

view = Page(
    Div(
        H1(lambda: f'Count: {count.get()}'),
        Button('Increment', on_click=lambda: count.set(count.get() + 1)),
        Button('Decrement', on_click=lambda: count.set(count.get() - 1)),
    )
)

view.dispatch_info(title='Document Title')

app = Haru(__name__)


@app.route('/')
def index(req: Request):
    return view


app.run()
