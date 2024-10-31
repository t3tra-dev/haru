"""
This module provides classes for representing HTML elements and their structures.
"""

from __future__ import annotations
from typing import Union, Optional, List, Dict
import html

__all__ = [
    'Element', 'SelfClosingElement',
    'A', 'Abbr', 'Acronym', 'Address', 'Area', 'Article', 'Aside', 'Audio',
    'B', 'Base', 'Bdi', 'Bdo', 'Big', 'Blockquote', 'Body', 'Br', 'Button',
    'Canvas', 'Caption', 'Center', 'Cite', 'Code', 'Col', 'Colgroup', 'Data',
    'Datalist', 'Dd', 'Del', 'Details', 'Dfn', 'Dialog', 'Dir', 'Div', 'Dl',
    'Dt', 'Em', 'Embed', 'Fencedframe', 'Fieldset', 'Figcaption', 'Figure',
    'Font', 'Footer', 'Form', 'Frame', 'Frameset', 'H1', 'H2', 'H3', 'H4',
    'H5', 'H6', 'Head', 'Header', 'Hgroup', 'Hr', 'Html', 'I', 'Iframe',
    'Img', 'Input', 'Ins', 'Kbd', 'Label', 'Legend', 'Li', 'Link',
    'Main', 'Map', 'Mark', 'Menu', 'Meta', 'Meter', 'Nav', 'Noscript',
    'Object', 'Ol', 'Optgroup', 'Option', 'Output', 'P', 'Param',
    'Picture', 'Pre', 'Progress', 'Q', 'Rb', 'Rp', 'Rt', 'Rtc', 'Ruby',
    'S', 'Samp', 'Script', 'Section', 'Select', 'Small', 'Source', 'Span',
    'Strong', 'Style', 'Sub', 'Summary', 'Sup', 'Svg', 'Table', 'Tbody',
    'Td', 'Template', 'Textarea', 'Tfoot', 'Th', 'Thead', 'Time', 'Title',
    'Tr', 'Track', 'U', 'Ul', 'Var', 'Video', 'Wbr', 'Xmp'
]


class Element:
    """
    A base class for representing an HTML element.

    :param tag: The HTML tag name for the element (e.g., 'div', 'button').
    :type tag: str
    :param args: Children elements or text content for the HTML element.
    :type args: Union[str, Element]
    :param attributes: A dictionary of HTML attributes for the element.
    :type attributes: Optional[Dict[str, Union[str, bool]]]
    :param raw: Whether to render the content as raw HTML without escaping.
    :type raw: bool
    """
    def __init__(
        self,
        tag: str,
        *args: Union[str, Element],
        attributes: Optional[dict[str, Union[str, bool]]] = None,
        raw: bool = False,
    ) -> None:
        self.tag = tag
        self.attributes = attributes if attributes else {}
        self.raw = raw
        self.children: List[Union[str, Element]] = list(args)
        self.parent: Optional[Element] = None

        # Set parent for child elements
        for child in self.children:
            if isinstance(child, Element):
                child.parent = self

    def render(self) -> str:
        # Render attributes, handling boolean attributes
        attrs = ' '.join(
            f'{key}' if isinstance(value, bool) and value else f'{key}="{value}"'
            for key, value in self.attributes.items()
            if not (isinstance(value, bool) and not value)
        )
        opening_tag = f"<{self.tag} {attrs}>" if attrs else f"<{self.tag}>"
        closing_tag = f"</{self.tag}>"

        # Render child elements
        content = ''.join(
            [
                child.render() if isinstance(child, Element) else (child if self.raw else html.escape(child))
                for child in self.children
            ]
        )
        return f"{opening_tag}{content}{closing_tag}"

    def append_child(self, child: Union[str, Element]) -> None:
        """
        Appends a child element or text to the current element.

        :param child: The child element or text to append.
        """
        if isinstance(child, Element):
            child.parent = self
        self.children.append(child)

    def remove_child(self, child: Union[str, Element]) -> None:
        """
        Removes a child element or text from the current element.

        :param child: The child element or text to remove.
        """
        self.children.remove(child)
        if isinstance(child, Element):
            child.parent = None

    def get_element_by_id(self, element_id: str) -> Optional[Element]:
        """
        Returns the first element with the specified ID.

        :param element_id: The ID to search for.
        :return: The Element with the matching ID, or None if not found.
        """
        if self.attributes.get('id') == element_id:
            return self
        for child in self._child_elements():
            result = child.get_element_by_id(element_id)
            if result:
                return result
        return None

    def get_elements_by_class_name(self, class_name: str) -> List[Element]:
        """
        Returns a list of elements with the specified class name.

        :param class_name: The class name to search for.
        :return: A list of Elements with the matching class name.
        """
        elements = []
        classes = self.attributes.get('class', '').split()
        if class_name in classes:
            elements.append(self)
        for child in self._child_elements():
            elements.extend(child.get_elements_by_class_name(class_name))
        return elements

    def query_selector(self, selector: str) -> Optional[Element]:
        """
        Returns the first element that matches the CSS selector.

        :param selector: The CSS selector to match.
        :return: The first matching Element, or None if not found.
        """
        return self._query_selector(selector, first_only=True)

    def query_selector_all(self, selector: str) -> List[Element]:
        """
        Returns all elements that match the CSS selector.

        :param selector: The CSS selector to match.
        :return: A list of matching Elements.
        """
        return self._query_selector(selector, first_only=False)

    def _query_selector(self, selector: str, first_only: bool) -> Union[Optional[Element], List[Element]]:
        # Simple selector parsing (supports tag, #id, .class)
        elements = []
        selector = selector.strip()
        if selector.startswith('#'):
            element = self.get_element_by_id(selector[1:])
            if element:
                return element if first_only else [element]
            else:
                return None if first_only else []
        elif selector.startswith('.'):
            elements = self.get_elements_by_class_name(selector[1:])
            return elements[0] if first_only and elements else elements
        else:
            if self.tag == selector:
                elements.append(self)
                if first_only:
                    return self
            for child in self._child_elements():
                result = child._query_selector(selector, first_only)
                if result:
                    if first_only:
                        return result
                    elif isinstance(result, list):
                        elements.extend(result)
            return elements if not first_only else (elements[0] if elements else None)

    def _child_elements(self) -> List[Element]:
        """
        Returns a list of child elements (excluding text nodes).

        :return: A list of child Elements.
        """
        return [child for child in self.children if isinstance(child, Element)]

    # Property to get the parent element
    @property
    def parent_element(self) -> Optional[Element]:
        """
        Returns the parent element of the current element.

        :return: The parent Element, or None if there is no parent.
        """
        return self.parent

    # Property to get child elements (excluding text nodes)
    @property
    def child_elements(self) -> List[Element]:
        """
        Returns a list of child elements (excluding text nodes).

        :return: A list of child Elements.
        """
        return self._child_elements()


class SelfClosingElement(Element):
    """
    A base class for representing a self-closing HTML element.

    :param tag: The HTML tag name for the self-closing element.
    :type tag: str
    :param attributes: A dictionary of HTML attributes for the element.
    :type attributes: Optional[Dict[str, Union[str, bool]]]
    """
    def render(self) -> str:
        attrs = ' '.join(
            f'{key}' if isinstance(value, bool) and value else f'{key}="{value}"'
            for key, value in self.attributes.items()
            if not (isinstance(value, bool) and not value)
        )
        return f"<{self.tag} {attrs} />" if attrs else f"<{self.tag} />"


class A(Element):
    """
    Represents an anchor HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('a', *args, attributes=attributes)


class Abbr(Element):
    """
    Represents an abbreviation HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('abbr', *args, attributes=attributes)


class Acronym(Element):
    """
    Represents an acronym HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('acronym', *args, attributes=attributes)


class Address(Element):
    """
    Represents an address HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('address', *args, attributes=attributes)


class Area(SelfClosingElement):
    """
    Represents an area HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('area', attributes=attributes)


class Article(Element):
    """
    Represents an article HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('article', *args, attributes=attributes)


class Aside(Element):
    """
    Represents an aside HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('aside', *args, attributes=attributes)


class Audio(Element):
    """
    Represents an audio HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('audio', *args, attributes=attributes)


class B(Element):
    """
    Represents a b HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('b', *args, attributes=attributes)


class Base(Element):
    """
    Represents a base HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('base', *args, attributes=attributes)


class Bdi(Element):
    """
    Represents a bdi HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('bdi', *args, attributes=attributes)


class Bdo(Element):
    """
    Represents a bdo HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('bdo', *args, attributes=attributes)


class Big(Element):
    """
    Represents a big HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('big', *args, attributes=attributes)


class Blockquote(Element):
    """
    Represents a blockquote HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('blockquote', *args, attributes=attributes)


class Body(Element):
    """
    Represents a body HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('body', *args, attributes=attributes)


class Br(SelfClosingElement):
    """
    Represents a br HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('br', attributes=attributes)


class Button(Element):
    """
    Represents a button HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('button', *args, attributes=attributes)


class Canvas(Element):
    """
    Represents a canvas HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('canvas', *args, attributes=attributes)


class Caption(Element):
    """
    Represents a caption HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('caption', *args, attributes=attributes)


class Center(Element):
    """
    Represents a center HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('center', *args, attributes=attributes)


class Cite(Element):
    """
    Represents a cite HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('cite', *args, attributes=attributes)


class Code(Element):
    """
    Represents a code HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('code', *args, attributes=attributes)


class Col(SelfClosingElement):
    """
    Represents a col HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('col', attributes=attributes)


class Colgroup(Element):
    """
    Represents a colgroup HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('colgroup', *args, attributes=attributes)


class Data(Element):
    """
    Represents a data HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('data', *args, attributes=attributes)


class Datalist(Element):
    """
    Represents a datalist HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('datalist', *args, attributes=attributes)


class Dd(Element):
    """
    Represents a dd HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('dd', *args, attributes=attributes)


class Del(Element):
    """
    Represents a del HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('del', *args, attributes=attributes)


class Details(Element):
    """
    Represents a details HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('details', *args, attributes=attributes)


class Dfn(Element):
    """
    Represents a dfn HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('dfn', *args, attributes=attributes)


class Dialog(Element):
    """
    Represents a dialog HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('dialog', *args, attributes=attributes)


class Dir(Element):
    """
    Represents a dir HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('dir', *args, attributes=attributes)


class Div(Element):
    """
    Represents a div HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('div', *args, attributes=attributes)


class Dl(Element):
    """
    Represents a dl HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('dl', *args, attributes=attributes)


class Dt(Element):
    """
    Represents a dt HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('dt', *args, attributes=attributes)


class Em(Element):
    """
    Represents an em HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('em', *args, attributes=attributes)


class Embed(Element):
    """
    Represents an embed HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('embed', *args, attributes=attributes)


class Fencedframe(Element):
    """
    Represents a fencedframe HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('fencedframe', *args, attributes=attributes)


class Fieldset(Element):
    """
    Represents a fieldset HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('fieldset', *args, attributes=attributes)


class Figcaption(Element):
    """
    Represents a figcaption HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('figcaption', *args, attributes=attributes)


class Figure(Element):
    """
    Represents a figure HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('figure', *args, attributes=attributes)


class Font(Element):
    """
    Represents a font HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('font', *args, attributes=attributes)


class Footer(Element):
    """
    Represents a footer HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('footer', *args, attributes=attributes)


class Form(Element):
    """
    Represents a form HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('form', *args, attributes=attributes)


class Frame(Element):
    """
    Represents a frame HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('frame', *args, attributes=attributes)


class Frameset(Element):
    """
    Represents a frameset HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('frameset', *args, attributes=attributes)


class H1(Element):
    """
    Represents an h1 HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('h1', *args, attributes=attributes)


class H2(Element):
    """
    Represents an h2 HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('h2', *args, attributes=attributes)


class H3(Element):
    """
    Represents an h3 HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('h3', *args, attributes=attributes)


class H4(Element):
    """
    Represents an h4 HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('h4', *args, attributes=attributes)


class H5(Element):
    """
    Represents an h5 HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('h5', *args, attributes=attributes)


class H6(Element):
    """
    Represents an h6 HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('h6', *args, attributes=attributes)


class Head(Element):
    """
    Represents a head HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('head', *args, attributes=attributes)


class Header(Element):
    """
    Represents a header HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('header', *args, attributes=attributes)


class Hgroup(Element):
    """
    Represents a hgroup HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('hgroup', *args, attributes=attributes)


class Hr(SelfClosingElement):
    """
    Represents an hr HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('hr', attributes=attributes)


class Html(Element):
    """
    Represents an html HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('html', *args, attributes=attributes)


class I(Element): # noqa
    """
    Represents an i HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('i', *args, attributes=attributes)


class Iframe(Element):
    """
    Represents an iframe HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('iframe', *args, attributes=attributes)


class Img(SelfClosingElement):
    """
    Represents an img HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('img', attributes=attributes)


class Input(SelfClosingElement):
    """
    Represents an input HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('input', attributes=attributes)


class Ins(Element):
    """
    Represents an ins HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('ins', *args, attributes=attributes)


class Kbd(Element):
    """
    Represents a kbd HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('kbd', *args, attributes=attributes)


class Label(Element):
    """
    Represents a label HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('label', *args, attributes=attributes)


class Legend(Element):
    """
    Represents a legend HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('legend', *args, attributes=attributes)


class Li(Element):
    """
    Represents a li HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('li', *args, attributes=attributes)


class Link(SelfClosingElement):
    """
    Represents a link HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('link', attributes=attributes)


class Main(Element):
    """
    Represents a main HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('main', *args, attributes=attributes)


class Map(Element):
    """
    Represents a map HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('map', *args, attributes=attributes)


class Mark(Element):
    """
    Represents a mark HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('mark', *args, attributes=attributes)


class Marquee(Element):
    """
    Represents a marquee HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('marquee', *args, attributes=attributes)


class Menu(Element):
    """
    Represents a menu HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('menu', *args, attributes=attributes)


class Meta(SelfClosingElement):
    """
    Represents a meta HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('meta', attributes=attributes)


class Meter(Element):
    """
    Represents a meter HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('meter', *args, attributes=attributes)


class Nav(Element):
    """
    Represents a nav HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('nav', *args, attributes=attributes)


class Nobr(Element):
    """
    Represents a nobr HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('nobr', *args, attributes=attributes)


class Noembed(Element):
    """
    Represents a noembed HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('noembed', *args, attributes=attributes)


class Noframes(Element):
    """
    Represents a noframes HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('noframes', *args, attributes=attributes)


class Noscript(Element):
    """
    Represents a noscript HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('noscript', *args, attributes=attributes)


class Object(Element):
    """
    Represents an object HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('object', *args, attributes=attributes)


class Ol(Element):
    """
    Represents an ol HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('ol', *args, attributes=attributes)


class Optgroup(Element):
    """
    Represents an optgroup HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('optgroup', *args, attributes=attributes)


class Option(Element):
    """
    Represents an option HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('option', *args, attributes=attributes)


class Output(Element):
    """
    Represents an output HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('output', *args, attributes=attributes)


class P(Element):
    """
    Represents a p HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('p', *args, attributes=attributes)


class Param(SelfClosingElement):
    """
    Represents a param HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('param', attributes=attributes)


class Picture(Element):
    """
    Represents a picture HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('picture', *args, attributes=attributes)


class Plaintext(Element):
    """
    Represents a plaintext HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('plaintext', *args, attributes=attributes)


class Portal(Element):
    """
    Represents a portal HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('portal', *args, attributes=attributes)


class Pre(Element):
    """
    Represents a pre HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('pre', *args, attributes=attributes)


class Progress(Element):
    """
    Represents a progress HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('progress', *args, attributes=attributes)


class Q(Element):
    """
    Represents a q HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('q', *args, attributes=attributes)


class Rb(Element):
    """
    Represents a rb HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('rb', *args, attributes=attributes)


class Rp(Element):
    """
    Represents a rp HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('rp', *args, attributes=attributes)


class Rt(Element):
    """
    Represents a rt HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('rt', *args, attributes=attributes)


class Rtc(Element):
    """
    Represents a rtc HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('rtc', *args, attributes=attributes)


class Ruby(Element):
    """
    Represents a ruby HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('ruby', *args, attributes=attributes)


class S(Element):
    """
    Represents an s HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('s', *args, attributes=attributes)


class Samp(Element):
    """
    Represents a samp HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('samp', *args, attributes=attributes)


class Script(Element):
    """
    Represents a script HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('script', *args, attributes=attributes)


class Search(Element):
    """
    Represents a search HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('search', *args, attributes=attributes)


class Section(Element):
    """
    Represents a section HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('section', *args, attributes=attributes)


class Select(Element):
    """
    Represents a select HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('select', *args, attributes=attributes)


class Slot(Element):
    """
    Represents a slot HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('slot', *args, attributes=attributes)


class Small(Element):
    """
    Represents a small HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('small', *args, attributes=attributes)


class Source(SelfClosingElement):
    """
    Represents a source HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('source', attributes=attributes)


class Span(Element):
    """
    Represents a span HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('span', *args, attributes=attributes)


class Strike(Element):
    """
    Represents a strike HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('strike', *args, attributes=attributes)


class Strong(Element):
    """
    Represents a strong HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('strong', *args, attributes=attributes)


class Style(Element):
    """
    Represents a style HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('style', *args, attributes=attributes)


class Sub(Element):
    """
    Represents a sub HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('sub', *args, attributes=attributes)


class Summary(Element):
    """
    Represents a summary HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('summary', *args, attributes=attributes)


class Sup(Element):
    """
    Represents a sup HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('sup', *args, attributes=attributes)


class Svg(Element):
    """
    Represents an svg HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('svg', *args, attributes=attributes)


class Table(Element):
    """
    Represents a table HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('table', *args, attributes=attributes)


class Tbody(Element):
    """
    Represents a tbody HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('tbody', *args, attributes=attributes)


class Td(Element):
    """
    Represents a td HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('td', *args, attributes=attributes)


class Template(Element):
    """
    Represents a template HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('template', *args, attributes=attributes)


class Textarea(Element):
    """
    Represents a textarea HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('textarea', *args, attributes=attributes)


class Tfoot(Element):
    """
    Represents a tfoot HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('tfoot', *args, attributes=attributes)


class Th(Element):
    """
    Represents a th HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('th', *args, attributes=attributes)


class Thead(Element):
    """
    Represents a thead HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('thead', *args, attributes=attributes)


class Time(Element):
    """
    Represents a time HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('time', *args, attributes=attributes)


class Title(Element):
    """
    Represents a title HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('title', *args, attributes=attributes)


class Tr(Element):
    """
    Represents a tr HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('tr', *args, attributes=attributes)


class Track(SelfClosingElement):
    """
    Represents a track HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('track', attributes=attributes)


class Tt(Element):
    """
    Represents a tt HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('tt', *args, attributes=attributes)


class U(Element):
    """
    Represents a u HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('u', *args, attributes=attributes)


class Ul(Element):
    """
    Represents an ul HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('ul', *args, attributes=attributes)


class Var(Element):
    """
    Represents a var HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('var', *args, attributes=attributes)


class Video(Element):
    """
    Represents a video HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('video', *args, attributes=attributes)


class Wbr(SelfClosingElement):
    """
    Represents a wbr HTML element.
    """
    def __init__(self, attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('wbr', attributes=attributes)


class Xmp(Element):
    """
    Represents an xmp HTML element.
    """
    def __init__(self, *args: Union[str, Element], attributes: Optional[Dict[str, Union[str, bool]]] = None) -> None:
        super().__init__('xmp', *args, attributes=attributes)
