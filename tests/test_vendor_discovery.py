from decimal import Decimal

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import User
from apps.catalog.models import Service
from apps.locations.models import City, Province
from apps.vendors.models import Vendor, VerificationStatus


@pytest.fixture
def directory(db) -> tuple[City, City, Service, list[Vendor]]:
    province = Province.objects.create(name='تهران', slug='tehran')
    city = City.objects.create(name='تهران', slug='tehran', province=province)
    other_city = City.objects.create(name='کرج', slug='karaj', province=province)
    service = Service.objects.create(title='چلنیوم', slug='letters')
    vendors = []
    for n in range(14):
        vendor = Vendor.objects.create(
            user=User.objects.create(username=f'directory-{n}'),
            business_name=f'تابلوساز {n}',
            slug=f'maker-{n}',
            city=city,
            verification_status=VerificationStatus.APPROVED,
            rating=Decimal('4.00'),
            years_of_experience=n,
        )
        vendor.services.add(service)
        vendors.append(vendor)
    vendors[-1].city = other_city
    vendors[-1].save(update_fields=['city'])
    return city, other_city, service, vendors


@pytest.mark.django_db
def test_vendor_directory_filters_and_keeps_selection_when_paginating(
    client, directory
) -> None:
    city, _, service, vendors = directory
    response = client.get(
        reverse('vendors:list'),
        {'city': city.slug, 'service': service.slug, 'sort': 'experience'},
    )
    assert response.status_code == 200
    assert response.context['vendors_count'] == 13
    assert len(response.context['vendors']) == 12
    assert response.context['vendors'][0] == vendors[12]
    html = response.content.decode()
    assert 'city=tehran' in html and 'service=letters' in html and 'page=2' in html
    last = client.get(
        reverse('vendors:list'),
        {'city': city.slug, 'service': service.slug, 'sort': 'experience', 'page': 2},
    )
    assert list(last.context['vendors']) == [vendors[0]]
    search = client.get(reverse('vendors:list'), {'q': 'تابلوساز 13'})
    assert list(search.context['vendors']) == [vendors[-1]]
    assert client.get(reverse('vendors:list'), {'sort': 'invalid'}).status_code == 400


@pytest.mark.django_db
def test_vendor_directory_has_constant_queries_with_related_cards(
    directory, django_assert_num_queries
) -> None:
    from apps.vendors.views import vendor_list

    request = RequestFactory().get('/vendors/')
    request.user = AnonymousUser()
    request.session = {}
    with django_assert_num_queries(5):
        response = vendor_list(request)
    assert response.status_code == 200
