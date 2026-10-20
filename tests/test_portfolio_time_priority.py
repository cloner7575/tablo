"""Complete clock previews precede incomplete covers before pagination."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.portfolio.models import TIME_IMAGE_FIELDS, PortfolioItem
from apps.portfolio.selectors import discoverable_items


def _reference(slug: str, *, complete: bool = False, image: str = '') -> PortfolioItem:
    return PortfolioItem.objects.create(
        title=slug,
        slug=slug,
        source_name='سازنده',
        source_url='https://example.test/',
        image=image or f'portfolio/{slug}.webp',
        **(
            {field: f'portfolio/{slug}-{field}.webp' for field in TIME_IMAGE_FIELDS}
            if complete
            else {}
        ),
    )


@pytest.mark.django_db
def test_complete_uploads_and_bundled_scenes_precede_partial_covers(
    django_assert_num_queries,
) -> None:
    complete = _reference('complete', complete=True)
    bundled = _reference('bundled', image='industry/references/novin-gerad.webp')
    partial = _reference('partial')
    partial.image_morning = 'portfolio/morning.webp'
    partial.image_day = 'portfolio/day.webp'
    partial.image_night = 'portfolio/night.webp'
    partial.save()
    unrelated = _reference('unrelated', image='portfolio/novin-gerad.webp')
    with django_assert_num_queries(1):
        ids = list(discoverable_items().values_list('pk', flat=True))
    assert ids == [bundled.pk, complete.pk, unrelated.pk, partial.pk]


@pytest.mark.django_db
@pytest.mark.parametrize('sort', ['newest', 'maker'])
def test_complete_covers_are_on_first_page_before_newer_incomplete_items(
    client, sort
) -> None:
    complete = _reference('complete', complete=True)
    PortfolioItem.objects.filter(pk=complete.pk).update(
        created_at=timezone.now() - timedelta(days=30)
    )
    for number in range(14):
        _reference(f'incomplete-{number}')
    hidden = _reference('hidden', complete=True)
    hidden.is_published = False
    hidden.save()
    response = client.get(reverse('portfolio:list'), {'sort': sort})
    assert response.status_code == 200
    first_page = list(response.context['page_obj'])
    assert first_page[0].pk == complete.pk
    assert len(first_page) == 12
    second_page = client.get(reverse('portfolio:list'), {'page': 2, 'sort': sort})
    assert complete.pk not in [item.pk for item in second_page.context['page_obj']]
    filtered = client.get(reverse('portfolio:list'), {'q': 'incomplete', 'sort': sort})
    assert all('incomplete' in item.title for item in filtered.context['page_obj'])
    home = client.get(reverse('common:home'))
    assert home.status_code == 200
    assert home.context['portfolio'][0].pk == complete.pk
