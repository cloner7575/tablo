"""Guards for the design system: tokens, icon sprite, and shared components."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse

STATIC = Path(settings.BASE_DIR) / "static"
TEMPLATES = Path(settings.BASE_DIR) / "templates"

RAW_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|(?<![-\w])rgba?\(")
ICON_USE = re.compile(r'_icon\.html" with name="([a-z-]+)"')


def test_component_css_declares_no_raw_colors() -> None:
    """Colours belong to tokens.css so a product can restyle in one file."""
    css = (STATIC / "css" / "base.css").read_text(encoding="utf-8")
    assert RAW_COLOR.search(css) is None


def test_tokens_define_both_themes() -> None:
    css = (STATIC / "css" / "tokens.css").read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in css
    assert "--color-accent:" in css
    assert "--space-4:" in css


def test_fonts_are_self_hosted() -> None:
    css = (STATIC / "css" / "tokens.css").read_text(encoding="utf-8")
    for family in ("vazirmatn-arabic.woff2", "vazirmatn-latin.woff2"):
        assert family in css
        assert (STATIC / "fonts" / family).is_file()


def test_every_referenced_icon_exists_in_the_sprite() -> None:
    sprite = (STATIC / "img" / "icons.svg").read_text(encoding="utf-8")
    available = set(re.findall(r'<symbol id="([a-z-]+)"', sprite))
    assert available

    used = {
        name
        for path in TEMPLATES.rglob("*.html")
        for name in ICON_USE.findall(path.read_text(encoding="utf-8"))
    }
    assert used <= available, f"missing from sprite: {sorted(used - available)}"


def test_icon_is_decorative_unless_it_carries_meaning() -> None:
    decorative = render_to_string("components/_icon.html", {"name": "database"})
    assert 'aria-hidden="true"' in decorative

    labelled = render_to_string(
        "components/_icon.html",
        {"name": "database", "label": "Database"},
    )
    assert 'role="img"' in labelled
    assert 'aria-label="Database"' in labelled


def test_button_full_width_flag_survives_inside_a_block() -> None:
    """`block` is bound to the BlockNode inside {% block %}; `full` is not."""
    template = Template(
        "{% block content %}"
        '{% include "components/_button.html" with text="Go" %}'
        "{% endblock %}"
    )
    assert "btn--block" not in template.render(Context({}))

    template = Template(
        "{% block content %}"
        '{% include "components/_button.html" with text="Go" full=True %}'
        "{% endblock %}"
    )
    assert "btn--block" in template.render(Context({}))


@pytest.mark.django_db
def test_home_page_has_one_h1_and_full_chrome(client) -> None:
    html = client.get(reverse("common:home")).content.decode()
    assert html.count("<h1") == 1
    assert "<header" in html
    assert "<footer" in html
    assert "img/icons.svg" in html


def test_login_page_submits_a_full_width_primary_button(client) -> None:
    html = client.get(reverse("accounts:login")).content.decode()
    assert "btn btn--primary btn--block" in html


def test_rtl_layer_covers_what_logical_properties_do_not() -> None:
    """Icons, Latin fragments and Latin typography need explicit RTL rules."""
    tokens = (STATIC / "css" / "tokens.css").read_text(encoding="utf-8")
    base = (STATIC / "css" / "base.css").read_text(encoding="utf-8")

    assert '[dir="rtl"]' in tokens, "RTL must reset Latin tracking and leading"
    for rule in ("icon--flip", "unicode-bidi: isolate", 'input[type="tel"]'):
        assert rule in base


def test_wizard_mobile_css_hides_aside_and_clips_overflow() -> None:
    """Request wizard used to blow out phones via the 9-step aside rail."""
    css = (STATIC / "css" / "tablo.css").read_text(encoding="utf-8")
    assert ".page-wizard .wz-aside" in css
    assert "display: none" in css
    assert "overflow-x: clip" in css
    assert ".wz-layout" in css and "flex-direction: column" in css


@pytest.mark.django_db
def test_shell_flips_direction_from_settings(client, settings) -> None:
    settings.TEXT_DIRECTION = "rtl"
    html = client.get(reverse("common:home")).content.decode()
    assert 'dir="rtl"' in html


def test_help_text_wrapper_survives_a_list(auth_client) -> None:
    """Password help text is a <ul>; a <p> wrapper would be hoisted away."""
    html = auth_client.get(reverse("accounts:password_change")).content.decode()
    index = html.index('class="field__help"')
    assert html.rfind("<div", 0, index) > html.rfind("<p", 0, index)
    assert "{#" not in html and "{%" not in html
