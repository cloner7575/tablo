"""Service discovery and a continuous handoff into the quote request."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from apps.catalog.models import Service
from apps.requests.views import WIZARD_SESSION_KEY


@pytest.mark.django_db
def test_services_only_show_active_matches_and_render_an_empty_state(client) -> None:
    visible = Service.objects.create(
        title='چلنیوم', slug='letters', suitable_for='کافه'
    )
    Service.objects.create(title='خدمت پنهان', slug='hidden', is_active=False)
    response = client.get(reverse('catalog:services'), {'q': 'کافه'})
    assert response.status_code == 200
    html = response.content.decode()
    assert reverse('catalog:service', kwargs={'slug': visible.slug}) in html
    assert 'خدمت پنهان' not in html
    assert '?service=letters' in html
    assert html.count('<h1') == 1
    empty = client.get(reverse('catalog:services'), {'q': 'پیدانشدنی'})
    assert 'خدمتی با این جست‌وجو پیدا نشد' in empty.content.decode()
    assert client.get(reverse('catalog:services'), {'q': 'x' * 81}).status_code == 400


@pytest.mark.django_db
def test_service_directory_query_count_stays_constant(
    django_assert_num_queries,
) -> None:
    from apps.catalog.views import service_index

    Service.objects.bulk_create(
        [Service(title=f'خدمت {n}', slug=f's-{n}') for n in range(8)]
    )
    request = RequestFactory().get('/services/')
    request.user = AnonymousUser()
    request.session = {}
    with django_assert_num_queries(1):
        response = service_index(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_service_handoff_selects_active_service_and_ignores_inactive(client) -> None:
    active = Service.objects.create(title='چلنیوم', slug='letters')
    hidden = Service.objects.create(title='پنهان', slug='hidden', is_active=False)
    start = reverse('requests:wizard_start')
    response = client.get(start, {'service': active.slug})
    assert response.status_code == 302
    assert client.session[WIZARD_SESSION_KEY]['service_id'] == active.pk
    client.get(start, {'service': hidden.slug})
    assert 'service_id' not in client.session[WIZARD_SESSION_KEY]
    client.get(start, {'guidance': '1'})
    assert client.session[WIZARD_SESSION_KEY]['needs_guidance'] is True
