from __future__ import annotations

from django.urls import register_converter
from django.urls.converters import StringConverter, get_converters


class UnicodeSlugConverter(StringConverter):
    """Slug converter that accepts Persian and other Unicode letters.

    Django's built-in ``slug`` only matches ``[-a-zA-Z0-9_]``, which breaks
    ``allow_unicode=True`` SlugFields used across the product.
    """

    regex = (
        r"[-a-zA-Z0-9_\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF"
        r"\uFB50-\uFDFF\uFE70-\uFEFF]+"
    )


if "uslug" not in get_converters():
    register_converter(UnicodeSlugConverter, "uslug")
