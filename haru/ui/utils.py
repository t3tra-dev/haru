"""
Utility functions for the haru.ui module.
"""

import re
from typing import Dict, Literal, Optional, Union, List
from .element import (
    Element,
    Div,
    Input,
    Label,
    Pre,
    Code,
    Ul,
    Ol,
    Li,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    Blockquote,
    Hr,
    A,
    Img,
    Table,
    Tr,
    Td,
)

__all__ = ["VStack", "HStack", "Markdown", "DataTable", "FormField", "FormGenerator"]


class VStack(Element):
    """
    A vertical stack of elements.
    """

    def __init__(self, *elements: Element) -> None:
        super().__init__(
            "div",
            attributes={
                "class": "vstack",
                "style": "display: flex; flex-direction: column; gap: 1rem;",
            },
            children=elements,
        )


class HStack(Element):
    """
    A horizontal stack of elements.
    """

    def __init__(self, *elements: Element) -> None:
        super().__init__(
            "div",
            attributes={
                "class": "hstack",
                "style": "display: flex; flex-direction: row; gap: 1rem;",
            },
            children=elements,
        )


class Markdown(Element):
    """
    A class to parse and render markdown text into HTML elements.
    """

    def __init__(self, markdown_text: str) -> None:
        super().__init__("div", attributes={"class": "markdown"})
        self.children = self._parse_markdown(markdown_text)

    def _parse_markdown(self, text: str) -> List[Union[str, Element]]:
        lines = text.splitlines()
        elements = []
        buffer = []

        for line in lines:
            line = line.rstrip()

            if line.startswith("#"):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(self._parse_heading(line))
            elif re.match(r"^(\* \* \*|\- \- \-|---|\*{3,})$", line):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(Hr())
            elif line.startswith(">"):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(self._parse_blockquote(line))
            elif re.match(r"^\* |\d+\. ", line):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(self._parse_list(lines))
            elif re.match(r"^\|", line):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(self._parse_table(lines))
            elif line.startswith("```"):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(self._parse_code_block(lines))
            elif re.match(
                r"^!$begin:math:display$.*$end:math:display$$begin:math:text$.*$end:math:text$$",
                line,
            ) or re.match(
                r"^$begin:math:display$.*$end:math:display$$begin:math:text$.*$end:math:text$$",
                line,
            ):
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
                elements.append(self._parse_link_or_image(line))
            elif line:
                buffer.append(line)
            else:
                if buffer:
                    elements.extend(self._parse_paragraph(" ".join(buffer)))
                    buffer = []
        if buffer:
            elements.extend(self._parse_paragraph(" ".join(buffer)))

        return elements

    def _parse_heading(self, line: str) -> Element:
        level = len(line) - len(line.lstrip("#"))
        content = line[level:].strip()
        heading_map = {1: H1, 2: H2, 3: H3, 4: H4, 5: H5, 6: H6}
        return heading_map.get(level, H1)(content)

    def _parse_blockquote(self, line: str) -> Element:
        content = line.lstrip("> ").strip()
        return Blockquote(content)

    def _parse_list(self, lines: List[str]) -> Element:
        elements = []
        for line in lines:
            if re.match(r"^\d+\. ", line):
                elements.append(Li(line.lstrip("0123456789. ")))
                list_type = Ol
            elif line.startswith("* "):
                elements.append(Li(line.lstrip("* ")))
                list_type = Ul
            else:
                break
        return list_type(*elements)

    def _parse_table(self, lines: List[str]) -> Element:
        header, alignments, *rows = lines
        align = []
        for align_indicator in alignments.split("|")[1:-1]:
            align.append(
                "left"
                if align_indicator.startswith(":") and align_indicator.endswith("-")
                else (
                    "right"
                    if align_indicator.endswith(":")
                    else (
                        "center"
                        if align_indicator.startswith(":")
                        and align_indicator.endswith(":")
                        else "left"
                    )
                )
            )
        table_elements = [
            Tr(
                *[
                    Td(cell.strip(), attributes={"style": f"text-align: {align[idx]}"})
                    for idx, cell in enumerate(header.split("|")[1:-1])
                ]
            )
        ]
        for row in rows:
            table_elements.append(
                Tr(*[Td(cell.strip()) for cell in row.split("|")[1:-1]])
            )
        return Table(*table_elements)

    def _parse_code_block(self, lines: List[str]) -> Element:
        language = lines[0][3:].strip() if len(lines[0]) > 3 else None
        code_lines = []
        for line in lines[1:]:
            if line.startswith("```"):
                break
            code_lines.append(line)
        return Code(
            "\n".join(code_lines),
            attributes={"class": f"language-{language}"} if language else None,
        )

    def _parse_link_or_image(self, line: str) -> Element:
        if line.startswith("!"):
            alt_text, src = re.findall(r"!\[(.*?)\]\((.*?)\)", line)[0]
            return Img(attributes={"alt": alt_text, "src": src})
        else:
            text, href = re.findall(r"\[(.*?)\]\((.*?)\)", line)[0]
            return A(text, attributes={"href": href})

    def _parse_paragraph(self, text: str) -> List[Union[str, Element]]:
        text = self._apply_inline_formatting(text)
        return [Div(text)]

    def _apply_inline_formatting(self, text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)  # Bold
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)  # Italic
        text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)  # Strikethrough
        text = re.sub(r"`(.+?)`", lambda m: str(Pre(m.group(1))), text)  # Inline code
        return text


class DataTable(Element):
    """
    A class to render a table of data.
    """

    def __init__(self, data: List[List[Union[str, int]]]) -> None:
        super().__init__("table")
        self.children = [Tr(*[Td(cell) for cell in row]) for row in data]


class FormField(Element):
    """
    A class to represent a field in a form.
    """

    input_types = Literal[
        "button",
        "checkbox",
        "color",
        "date",
        "datetime-local",
        "email",
        "file",
        "hidden",
        "image",
        "month",
        "number",
        "password",
        "radio",
        "range",
        "reset",
        "search",
        "submit",
        "tel",
        "text",
        "time",
        "url",
        "week",
    ]

    def __init__(
        self,
        label: str,
        input_type: Optional[input_types] = "text",
        placeholder: Optional[str] = None,
    ) -> None:
        super().__init__("div")
        self.children = [
            Label(label),
            Input(type=input_type, placeholder=placeholder),
        ]


class FormGenerator(Element):
    """
    A class to generate a form from a dictionary of fields.
    """

    def __init__(
        self, fields: Dict[str, FormField], action: Optional[str] = None
    ) -> None:
        super().__init__("form", attributes={"action": action})
        self.children = [field for field in fields.values()]
