"""The ordering guide stays useful before editorial articles are published."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_home_without_articles_links_to_complete_ordering_guides(client) -> None:
    response = client.get(reverse('common:home'))
    assert response.status_code == 200
    content = response.content.decode()
    for anchor in ('prepare', 'price', 'approval'):
        assert f'href="{reverse("common:guide")}#{anchor}"' in content
    assert 'راهنمای قیمت و مراحل سفارش</a></div>' not in content


def test_order_guide_has_readable_sections_without_articles(client) -> None:
    response = client.get(reverse('common:guide'))
    assert response.status_code == 200
    content = response.content.decode()
    for anchor in ('prepare', 'price', 'approval'):
        assert f'id="{anchor}"' in content
    assert reverse('requests:wizard_start') in content
    assert 'مقاله‌های راهنما در حال تکمیل‌اند.' not in content
