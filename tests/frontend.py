from haru.ui import Page, Div, H1
from haru.ui.utils import Markdown

view: Page = Page(
    Div(
        H1('Hello, World!'),
        Markdown("""
# Hello, World!

This is a test of the UI modules.
"""),
        attributes={'class': 'container'}
    )
)

view.dispatch_info(title='Document Title')

print(view.render())
