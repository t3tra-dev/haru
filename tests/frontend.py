from haru.ui import Page, Div, H1
from haru.ui.utils import Markdown

view: Page = Page(
    Div(
        H1('Hello, World!'),
        Markdown("# Hello, World!\n\nThis is a test of the UI modules."),
        attributes={'id': 'container'}
    )
)

print(view.query_selector_all('h1'))

print(view.get_element_by_id('container'))

view.dispatch_info(title='Document Title')

print(view.render())
