"""
This module provides utilities for creating and rendering HTML elements in the Haru web framework.
It includes the `Element` class for representing HTML elements, the `Props` class for managing
element attributes, and helper functions to create and render elements.

Classes:
    - `Props`: A class that holds element attributes.
    - `Element`: A class that represents an HTML element.

Functions:
    - `create_element`: Creates a new `Element` instance.

Usage example:

.. code-block:: python

    div = create_element('div', Props(id='main', class_name='container'), 'Hello, World!')
    html_string = div.render()
"""

from __future__ import annotations
import inspect
import ast
import html
from typing import List, Optional, Union, Callable

__all__ = ['Element', 'Props', 'create_element']


class Props:
    """
    A class that holds attributes for an HTML element.
    Attributes are stored as keyword arguments.

    Example:

    .. code-block:: python

        props = Props(id='main', class_name='container')
        print(props.id)  # Outputs: 'main'
        print(props.class_name)  # Outputs: 'container'
    """

    def __init__(self, **kwargs):
        """
        Initialize the `Props` object with arbitrary keyword arguments.

        :param kwargs: Arbitrary attributes for the HTML element.
        """
        self.attrs = kwargs

    def __getattr__(self, name):
        """
        Retrieve an attribute value from the `Props` object.
        If the attribute is not found, return `None`.

        :param name: The name of the attribute to retrieve.
        :return: The value of the attribute, or `None` if not found.
        """
        return self.attrs.get(name, None)


def escape_attr_value(value: str) -> str:
    """
    Escape and properly quote an HTML attribute value.

    :param value: The attribute value to escape.
    :return: The escaped and quoted attribute value.
    """
    value = html.escape(value, quote=True)
    if '"' in value and "'" not in value:
        return f"'{value}'"
    else:
        return f'"{value}"'


def extract_code(func: Callable) -> str:
    """
    Extract the code from a callable object, such as a function or lambda expression.

    :param func: The callable object to extract code from.
    :return: The extracted code as a string.
    """
    source = inspect.getsource(func)
    source = inspect.cleandoc(source)
    node = ast.parse(source)

    if isinstance(node, ast.Module) and len(node.body) == 1:
        stmt = node.body[0]
        if isinstance(stmt, ast.FunctionDef):
            # For function definitions, return the body of the function
            code_lines = [ast.get_source_segment(source, s) for s in stmt.body]
            code = '\n'.join(code_lines)
            return code
        elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Lambda):
            # For lambda expressions assigned to a variable
            code = ast.get_source_segment(source, stmt.value.body)
            return code
    elif isinstance(node, ast.Expression) and isinstance(node.body, ast.Lambda):
        # For direct lambda expressions
        code = ast.get_source_segment(source, node.body.body)
        return code
    else:
        raise TypeError("Unsupported callable type")


class Element:
    """
    A class that represents an HTML element. An `Element` can have a tag name, attributes (`Props`),
    and child elements or text. It can be rendered into an HTML string.

    Example:

    .. code-block:: python

        element = Element('div', Props(id='main'), ['Hello, World!'])
        print(element.render())  # Outputs: <div id="main">Hello, World!</div>
    """

    def __init__(self, tag_name: str, props: Optional[Props], children: Optional[List[Union[Element, str]]] = None) -> None:
        """
        Initialize the `Element` object with a tag name, attributes, and optional child elements.

        :param tag_name: The HTML tag name (e.g., 'div', 'span').
        :param props: An optional `Props` object representing element attributes.
        :param children: A list of child elements or text.
        """
        self.tag_name = tag_name
        self.props = props
        self.children = children or []

    def render(self) -> str:
        """
        Recursively render the element and its children into an HTML string.

        :return: The rendered HTML string.
        """
        attrs = ''
        if self.props:
            attrs_list = []
            for key, value in self.props.attrs.items():
                if value is None:
                    continue
                if key == 'class_name':
                    attr_name = 'class'
                elif key.startswith('on_'):
                    attr_name = key.replace('_', '')
                    if callable(value):
                        code = extract_code(value)
                        code = code.replace('\\', '\\\\').replace('"', '\\"')
                        js_code = f'pyodide.runPython("{code}")'
                        attr_value = js_code
                    else:
                        attr_value = str(value)
                else:
                    attr_name = key.replace('_', '-')
                    attr_value = str(value)
                attr_value_escaped = escape_attr_value(attr_value)
                attrs_list.append(f'{attr_name}={attr_value_escaped}')
            attrs = ' ' + ' '.join(attrs_list) if attrs_list else ''

        self_close_tags = [
            'img', 'br', 'hr', 'input', 'meta', 'link',
            'area', 'base', 'col', 'command', 'embed', 'keygen',
            'param', 'source', 'track', 'wbr'
        ]

        if self.tag_name.lower() in self_close_tags:
            return f'<{self.tag_name}{attrs} />'
        else:
            content = ''
            for child in self.children:
                if isinstance(child, Element):
                    content += child.render()
                else:
                    content += html.escape(str(child))
            return f'<{self.tag_name}{attrs}>{content}</{self.tag_name}>'


def create_element(tag_name: str, props: Optional[Props], *children: Union[Element, str, None]) -> Element:
    """
    Create a new `Element` object with the specified tag name, attributes, and child elements.

    :param tag_name: The HTML tag name (e.g., 'div', 'span').
    :param props: An optional `Props` object representing element attributes.
    :param children: A list of child elements or text.
    :return: A new `Element` instance.
    """
    child_list = []
    for child in children:
        if child is None:
            continue
        elif isinstance(child, (Element, str)):
            child_list.append(child)
        else:
            raise TypeError(f'Invalid child type: {type(child)}')

    return Element(tag_name, props, child_list)
