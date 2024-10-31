"""
The haru.ui modules provide UI components and utilities for building web interfaces in the Haru framework.
It includes HTML element classes for constructing DOM structures, a Page class for creating complete
web pages, and utility functions for UI-related operations. The module makes it easy to create
dynamic and interactive web UIs using Python code.
"""

from .element import (
    Element, SelfClosingElement,
    A, Abbr, Acronym, Address, Area, Article, Aside, Audio,
    B, Base, Bdi, Bdo, Big, Blockquote, Body, Br, Button,
    Canvas, Caption, Center, Cite, Code, Col, Colgroup,
    Data, Datalist, Dd, Del, Details, Dfn, Dialog, Dir, Div, Dl, Dt,
    Em, Embed, Fencedframe, Fieldset, Figcaption, Figure, Font, Footer, Form, Frame, Frameset,
    H1, H2, H3, H4, H5, H6, Head, Header, Hgroup, Hr, Html,
    I, Iframe, Img, Input, Ins, Kbd, Label, Legend, Li, Link, Main, Map, Mark, Menu, Meta, Meter,
    Nav, Noscript, Object, Ol, Optgroup, Option, Output, P, Param, Picture, Pre, Progress,
    Q, Rb, Rp, Rt, Rtc, Ruby, S, Samp, Script, Section, Select, Small, Source, Span, Strong, Style, Sub, Summary, Sup, Svg,
    Table, Tbody, Td, Template, Textarea, Tfoot, Th, Thead, Time, Title, Tr, Track,
    U, Ul, Var, Video, Wbr, Xmp
)
from .page import Page
from . import utils

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
    'Tr', 'Track', 'U', 'Ul', 'Var', 'Video', 'Wbr', 'Xmp',
    'Page', 'utils'
]
