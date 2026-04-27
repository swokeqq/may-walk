"""Вспомогательные операции импорта XML-файлов маршрутов."""

from xml.etree import ElementTree

from may_walk.services.route.imports.types import RouteImportError


def parse_xml(content: bytes, error_message: str) -> ElementTree.Element:
    """Распарсить XML-файл."""
    try:
        return ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise RouteImportError(error_message) from error


def find_by_local_name(
    element: ElementTree.Element,
    local_name: str,
) -> list[ElementTree.Element]:
    """Найти XML-элементы без привязки к namespace."""
    return [
        child
        for child in element.iter()
        if local_name_from_tag(child.tag) == local_name
    ]


def first_by_local_name(
    element: ElementTree.Element,
    local_name: str,
) -> ElementTree.Element | None:
    """Найти первый XML-элемент без привязки к namespace."""
    for child in element.iter():
        if local_name_from_tag(child.tag) == local_name:
            return child

    return None


def local_name_from_tag(tag: str) -> str:
    """Вернуть XML local-name без namespace."""
    return tag.rsplit('}', maxsplit=1)[-1]
