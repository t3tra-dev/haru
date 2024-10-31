"""
This class represents a complete HTML page structure. It automatically structures
elements based on the provided root element.
"""

from typing import Literal, Optional, Union, List
from .element import Element, Html, Head, Body, Title, Meta, Link

__all__ = ["Page"]


class Page:
    """
    Represents a complete HTML page structure. Automatically structures
    elements based on the provided root element.

    :param root_element: The root element for the page.
    :type root_element: Union[Element, str]
    """

    def __init__(self, root_element: Union[Element, str]):
        if isinstance(root_element, Html):
            self.root = root_element
        elif isinstance(root_element, Body):
            self.root = Html(Head(), root_element)
        elif isinstance(root_element, (Title, Meta, Link)):
            head = Head(root_element)
            self.root = Html(head, Body())
        else:
            self.root = Html(Head(), Body(root_element))

        self.head = next(
            (child for child in self.root.children if isinstance(child, Head)), None
        )
        self.body = next(
            (child for child in self.root.children if isinstance(child, Body)), None
        )

    def add_to_head(self, element: Union[Title, Meta, Link]) -> None:
        if not self.head:
            self.head = Head()
            self.root.children.insert(0, self.head)
        self.head.children.append(element)

    def add_to_body(self, element: Union[Element, str]) -> None:
        if not self.body:
            self.body = Body()
            self.root.children.append(self.body)
        self.body.children.append(element)

    def query_selector(self, selector: str) -> Optional[Element]:
        """
        Returns the first element that matches the CSS selector in the page.

        :param selector: The CSS selector to match.
        :return: The first matching Element, or None if not found.
        """
        return self.root.query_selector(selector)

    def query_selector_all(self, selector: str) -> List[Element]:
        """
        Returns all elements that match the CSS selector in the page.

        :param selector: The CSS selector to match.
        :return: A list of matching Elements.
        """
        return self.root.query_selector_all(selector)

    def get_element_by_id(self, element_id: str) -> Optional[Element]:
        """
        Returns the first element with the specified ID in the page.

        :param element_id: The ID to search for.
        :return: The Element with the matching ID, or None if not found.
        """
        return self.root.get_element_by_id(element_id)

    def get_elements_by_class_name(self, class_name: str) -> List[Element]:
        """
        Returns a list of elements with the specified class name in the page.

        :param class_name: The class name to search for.
        :return: A list of Elements with the matching class name.
        """
        return self.root.get_elements_by_class_name(class_name)

    # Property to get the child elements of the root
    @property
    def children(self) -> List[Element]:
        """
        Returns the child elements of the root element.

        :return: A list of child Elements.
        """
        return self.root.child_elements

    # Property to get the parent (None for Page)
    @property
    def parent(self) -> None:
        """
        Returns None as the page does not have a parent element.

        :return: None
        """
        return None

    def dispatch_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        image: Optional[str] = None,
        site_name: Optional[str] = None,
        twitter_card: Optional[
            Literal["summary", "summary_large_image", "app", "player"]
        ] = "summary",
    ) -> None:
        """
        Adds or updates basic metadata, OGP, and Twitter Card meta tags in the head section.

        :param title: The page title.
        :type title: Optional[str]
        :param description: The page description.
        :type description: Optional[str]
        :param url: The page URL.
        :type url: Optional[str]
        :param image: The URL to an image for preview.
        :type image: Optional[str]
        :param site_name: The site name.
        :type site_name: Optional[str]
        :param twitter_card: The Twitter Card type (default is 'summary').
        :type twitter_card: Optional[str]
        """
        if title:
            self._set_or_update_element(Title(title), element_type=Title)
            self._set_or_update_meta("og:title", title)
            self._set_or_update_meta("twitter:title", title)
        if description:
            self._set_or_update_meta("description", description)
            self._set_or_update_meta("og:description", description)
            self._set_or_update_meta("twitter:description", description)
        if url:
            self._set_or_update_meta("og:url", url)
        if image:
            self._set_or_update_meta("og:image", image)
            self._set_or_update_meta("twitter:image", image)
        if site_name:
            self._set_or_update_meta("og:site_name", site_name)
        if twitter_card:
            self._set_or_update_meta("twitter:card", twitter_card)

    def _set_or_update_element(
        self, element: Union[Title, Meta, Link], element_type: Optional[type] = None
    ) -> None:
        """
        Helper to set or update an element in the head section.

        :param element: The element to add or update.
        :type element: Union[Title, Meta, Link]
        :param element_type: Optional specific type of element to look for.
        :type element_type: Optional[type]
        """
        existing_element = next(
            (
                child
                for child in self.head.children
                if isinstance(child, element_type or type(element))
            ),
            None,
        )
        if existing_element:
            existing_element.children = element.children  # Update content
        else:
            self.add_to_head(element)

    def _set_or_update_meta(self, name: str, content: str) -> None:
        """
        Helper to set or update a meta tag in the head section.

        :param name: The meta tag name or property attribute.
        :type name: str
        :param content: The content for the meta tag.
        :type content: str
        """
        existing_meta = next(
            (
                child
                for child in self.head.children
                if isinstance(child, Meta)
                and child.attributes.get("name") == name
                or child.attributes.get("property") == name
            ),
            None,
        )
        if existing_meta:
            existing_meta.attributes["content"] = (
                content  # Update content if meta tag exists
            )
        else:
            # Add new meta tag if not exists
            self.add_to_head(
                Meta(
                    attributes={
                        (
                            "name"
                            if "og:" not in name and "twitter:" not in name
                            else "property"
                        ): name,
                        "content": content,
                    }
                )
            )

    def render(self) -> str:
        return self.root.render()
