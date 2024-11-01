from haru.ui import Page, Div
from haru.ui.utils import Markdown, DataTable

view: Page = Page(
    Div(
        Markdown("# Hello, World!\n\nThis is a test of the UI modules."),
        DataTable([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
        attributes={"id": "container"},
    )
)

print(view.query_selector_all("h1"))

print(view.get_element_by_id("container"))

view.dispatch_info(title="Document Title")

print(view.render())
