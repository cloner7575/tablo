"""Daily workspaces keep actions useful and scoped to their owner."""

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.catalog.models import Service
from apps.locations.models import City, Province
from apps.orders.models import Order
from apps.quotes.models import Quote, QuoteStatus
from apps.requests.models import ProjectRequest, RequestStatus
from apps.vendors.models import Vendor, VerificationStatus


@pytest.fixture
def workspace(db) -> tuple[User, User, Vendor, ProjectRequest, Quote]:
    province = Province.objects.create(name='تهران', slug='tehran')
    city = City.objects.create(name='تهران', slug='tehran', province=province)
    service = Service.objects.create(title='چلنیوم', slug='letters')
    customer = User.objects.create(username='customer')
    outsider = User.objects.create(username='outsider')
    vendor = Vendor.objects.create(
        user=User.objects.create(username='vendor', role=UserRole.VENDOR),
        business_name='کارگاه آبی',
        slug='blue',
        city=city,
        verification_status=VerificationStatus.APPROVED,
    )
    vendor.services.add(service)
    project = ProjectRequest.objects.create(
        customer=customer,
        city=city,
        service=service,
        title='ویترین کافه',
        status=RequestStatus.QUOTED,
    )
    quote = Quote.objects.create(
        request=project, vendor=vendor, price=5000000, estimated_delivery_days=5
    )
    return customer, outsider, vendor, project, quote


@pytest.mark.django_db
def test_customer_dashboard_has_next_actions_filters_and_owner_scope(
    client, workspace
) -> None:
    customer, outsider, vendor, project, quote = workspace
    ProjectRequest.objects.create(
        customer=outsider,
        title='پروژهٔ خصوصی دیگران',
        city=project.city,
        status=RequestStatus.QUOTED,
    )
    client.force_login(customer)
    response = client.get(
        reverse('requests:dashboard'), {'status': 'offers', 'q': 'کافه'}
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert 'مقایسهٔ پیشنهادها' in html
    assert 'پروژهٔ خصوصی دیگران' not in html
    assert response.context['summary']['new_quotes'] == 1
    assert response.context['cards'][0]['project'] == project
    assert (
        client.get(reverse('requests:dashboard'), {'status': 'invalid'}).status_code
        == 400
    )


@pytest.mark.django_db
def test_shortlisting_is_reversible_post_only_and_never_accepts_a_quote(
    client, workspace
) -> None:
    customer, outsider, _, project, quote = workspace
    url = reverse('requests:quote_shortlist', kwargs={'pk': quote.pk})
    client.force_login(outsider)
    assert client.post(url).status_code == 404
    client.force_login(customer)
    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 302
    quote.refresh_from_db()
    assert quote.status == QuoteStatus.SHORTLISTED
    assert not Order.objects.exists()
    client.post(url)
    quote.refresh_from_db()
    assert quote.status == QuoteStatus.VIEWED
    project.status = RequestStatus.CANCELLED
    project.save(update_fields=['status'])
    assert client.post(url).status_code == 400


@pytest.mark.django_db
def test_vendor_can_follow_their_won_project_after_matching_feed_closes(
    client, workspace
) -> None:
    customer, outsider, vendor, project, quote = workspace
    project.status = RequestStatus.ACCEPTED
    project.save(update_fields=['status'])
    quote.status = QuoteStatus.ACCEPTED
    quote.save(update_fields=['status'])
    Order.objects.create(
        request=project,
        quote=quote,
        customer=customer,
        vendor=vendor,
        agreed_price=quote.price,
    )
    client.force_login(vendor.user)
    assert (
        client.get(
            reverse('vendors:request_detail', kwargs={'pk': project.pk})
        ).status_code
        == 200
    )
    response = client.get(reverse('vendors:projects'))
    assert response.status_code == 200
    assert project.title in response.content.decode()
    assert (
        client.get(reverse('vendors:my_quotes'), {'status': 'accepted'}).context[
            'quotes'
        ][0]
        == quote
    )
    other_vendor = Vendor.objects.create(
        user=outsider,
        city=project.city,
        business_name='دیگر',
        slug='other',
        verification_status=VerificationStatus.APPROVED,
    )
    client.force_login(other_vendor.user)
    assert (
        client.get(
            reverse('vendors:request_detail', kwargs={'pk': project.pk})
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_customer_workspace_query_count_does_not_grow_with_cards(
    workspace, django_assert_num_queries
) -> None:
    from apps.requests.views import customer_dashboard

    customer, _, _, project, _ = workspace
    ProjectRequest.objects.bulk_create(
        [
            ProjectRequest(
                customer=customer,
                city=project.city,
                title=f'تابلو {n}',
                status=RequestStatus.SUBMITTED,
            )
            for n in range(15)
        ]
    )
    request = RequestFactory().get('/request/dashboard/')
    request.user = customer
    request.session = {}
    with django_assert_num_queries(4):
        response = customer_dashboard(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_assigned_vendor_can_start_execution_chat_but_not_negotiate_first(
    workspace,
) -> None:
    from apps.chat.services import ChatError, get_or_open_conversation

    _, _, vendor, project, quote = workspace
    with pytest.raises(ChatError):
        get_or_open_conversation(quote=quote, user=vendor.user)
    quote.status = QuoteStatus.ACCEPTED
    quote.save(update_fields=['status'])
    project.status = RequestStatus.ACCEPTED
    project.save(update_fields=['status'])
    conversation = get_or_open_conversation(quote=quote, user=vendor.user)
    assert conversation.quote_id == quote.pk


@pytest.mark.django_db
def test_customer_pagination_preserves_search_and_never_shows_another_account(
    client, workspace
) -> None:
    customer, outsider, _, project, _ = workspace
    ProjectRequest.objects.bulk_create(
        [
            ProjectRequest(
                customer=customer,
                city=project.city,
                title=f'نمای فروشگاه {n}',
                status=RequestStatus.SUBMITTED,
            )
            for n in range(14)
        ]
    )
    ProjectRequest.objects.create(
        customer=outsider,
        city=project.city,
        title='نمای فروشگاه خصوصی',
        status=RequestStatus.SUBMITTED,
    )
    client.force_login(customer)
    response = client.get(reverse('requests:dashboard'), {'q': 'نمای فروشگاه'})
    assert len(response.context['cards']) == 12
    assert 'page=2' in response.content.decode()
    last = client.get(reverse('requests:dashboard'), {'q': 'نمای فروشگاه', 'page': 2})
    assert len(last.context['cards']) == 2
    assert 'خصوصی' not in last.content.decode()


@pytest.mark.django_db
def test_vendor_quote_and_execution_lists_keep_constant_query_counts(
    workspace, django_assert_num_queries
) -> None:
    from apps.vendors.views import my_quotes, projects

    customer, _, vendor, project, quote = workspace
    Order.objects.create(
        request=project,
        quote=quote,
        customer=customer,
        vendor=vendor,
        agreed_price=quote.price,
    )
    request = RequestFactory().get('/vendors/projects/')
    request.user = vendor.user
    request.session = {}
    for view in (my_quotes, projects):
        with django_assert_num_queries(6):
            response = view(request)
        assert response.status_code == 200
