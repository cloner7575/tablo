"""Shared photographs follow the clock without changing source media."""

from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context, Template

from apps.portfolio.models import PortfolioItem


def test_provider_card_loads_its_own_scene_image_tags() -> None:
    from django.template.loader import render_to_string

    html = render_to_string(
        'partials/_industry_provider_card.html',
        {'provider': {'name': 'سازنده', 'image': 'gerad.webp'}},
    )
    assert 'data-clock-picture' in html
    assert 'alt="سازنده"' in html


def test_static_photographs_share_variants_and_every_variant_exists() -> None:
    from apps.common.daylight_images import SCENE_SOURCES, scene_variants

    for source in SCENE_SOURCES:
        variants = scene_variants(source)
        assert set(variants) == {'morning', 'day', 'sunset', 'night'}
        for phase in variants:
            slug = SCENE_SOURCES[source]
            assert (
                Path(settings.BASE_DIR) / 'static/img/daylight' / f'{slug}-{phase}.webp'
            ).is_file()
    assert scene_variants('img/landing-office-v1.webp') == scene_variants(
        'img/demo/portfolio-office.png'
    )


def test_unknown_uploaded_media_keep_their_original_without_invented_variants() -> None:
    from apps.common.daylight_images import scene_variants

    assert scene_variants('/media/vendor/real-installation.jpg') == {}
    html = Template('{% load time_images %}{% scene_image source alt=alt %}').render(
        Context({'source': '/media/vendor/real-installation.jpg', 'alt': '<تابلو>'})
    )
    assert 'src="/media/vendor/real-installation.jpg"' in html
    assert 'data-clock-morning=' not in html
    assert '&lt;تابلو&gt;' in html


def test_scene_images_keep_default_lazy_dimensions_and_single_exposure() -> None:
    html = Template(
        '{% load time_images %}'
        '{% scene_image "img/landing-signature-v1.webp" width=1000 height=1000 %}'
    ).render(Context())
    assert 'data-clock-exposure="single"' in html
    assert 'src="/static/img/landing-signature-v1.webp"' in html
    assert 'width="1000" height="1000"' in html
    assert 'loading="lazy"' in html
    assert 'data-clock-night="/static/img/daylight/signature-night.webp"' in html


def test_portfolio_demo_variants_preserve_explicit_uploaded_overrides() -> None:
    from apps.portfolio.templatetags.time_images import time_image

    item = PortfolioItem(pk=1, title='تابلو', image_morning='portfolio/morning.webp')
    result = time_image(item)
    assert result['variants']['morning'].endswith('/portfolio/morning.webp')
    assert result['variants']['night'].endswith('/daylight/boutique-night.webp')
    assert result['single_exposure'] is True
    item.image = 'portfolio/original.jpg'
    result = time_image(item)
    assert set(result['variants']) == {'morning'}


@pytest.mark.django_db
def test_resolving_scene_images_does_not_query_the_database(
    django_assert_num_queries,
) -> None:
    from apps.common.daylight_images import scene_variants

    with django_assert_num_queries(0):
        for _ in range(10):
            assert scene_variants('img/demo/portfolio-office.png')
