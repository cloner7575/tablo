import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.catalog.models import Service
from apps.locations.models import City, Province
from apps.quotes.models import Quote
from apps.quotes.services import accept_quote
from apps.requests.models import ProjectRequest, RequestStatus
from apps.requests.selectors import matched_requests_for_vendor
from apps.vendors.models import Vendor, VerificationStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def marketplace():
    city = City.objects.create(
        name='تهران',
        slug='tehran',
        province=Province.objects.create(name='تهران', slug='tehran'),
    )
    service = Service.objects.create(title='چلنیوم', slug='letters')
    customer = User.objects.create(username='buyer')
    vendors = []
    for n in range(2):
        vendor = Vendor.objects.create(
            user=User.objects.create(username=f'signmaker{n}', role=UserRole.VENDOR),
            business_name=f'کارگاه {n}',
            slug=f'maker{n}',
            city=city,
            verification_status=VerificationStatus.APPROVED,
        )
        vendor.services.add(service)
        vendors.append(vendor)
    project = ProjectRequest.objects.create(
        customer=customer,
        city=city,
        service=service,
        status=RequestStatus.QUOTED,
        description='تابلو برای کافه',
    )
    quote = Quote.objects.create(
        request=project,
        vendor=vendors[0],
        price=5000000,
        installation_cost=500000,
        estimated_delivery_days=7,
    )
    return customer, vendors, project, quote


def test_guidance_reaches_contact_and_keeps_data(client, marketplace):
    _, _, project, _ = marketplace
    session = client.session
    session['request_wizard'] = {
        'needs_guidance': True,
        'city_id': project.city_id,
        'description': 'برای کافه راهنمایی می‌خواهم',
    }
    session.save()
    response = client.get(reverse('requests:wizard_phone'))
    assert response.status_code == 200
    assert (
        client.session['request_wizard']['description'] == 'برای کافه راهنمایی می‌خواهم'
    )


def test_direct_request_is_private_to_chosen_vendor(marketplace):
    _, vendors, project, _ = marketplace
    project.preferred_vendor = vendors[0]
    project.save()
    assert matched_requests_for_vendor(vendors[0]).filter(pk=project.pk).exists()
    assert not matched_requests_for_vendor(vendors[1]).filter(pk=project.pk).exists()


def test_order_amount_includes_installation(marketplace):
    customer, _, _, quote = marketplace
    order = accept_quote(quote=quote, user=customer)
    assert order.agreed_price == 5500000


def test_new_request_needs_no_technical_choice(client, marketplace):
    _, _, project, _ = marketplace
    response = client.get(reverse('requests:wizard_start'))
    assert response.url == reverse('requests:wizard_need')
    response = client.post(
        reverse('requests:wizard_need'),
        {
            'city': project.city_id,
            'business_type': 'کافه',
            'use_case': 'shop',
            'audience': 'matched',
        },
    )
    assert response.url == reverse('requests:wizard_details')
    response = client.post(
        reverse('requests:wizard_details'),
        {
            'description': 'یک تابلو برای سردر کافه می‌خواهم',
            'choice': 'unsure',
            'night_light': 'unsure',
        },
    )
    assert response.url == reverse('requests:wizard_phone')
    assert client.get(response.url).status_code == 200
    assert client.session['request_wizard']['needs_guidance'] is True


def test_invalid_details_preserve_location_and_show_errors(client, marketplace):
    _, _, project, _ = marketplace
    session = client.session
    session['request_wizard'] = {'city_id': project.city_id, 'compact': True}
    session.save()
    response = client.post(
        reverse('requests:wizard_details'),
        {'choice': 'unsure', 'night_light': 'unsure', 'budget_max': '-1'},
    )
    assert response.status_code == 400
    assert client.session['request_wizard']['city_id'] == project.city_id
    assert response.context['form'].errors


def test_saved_portfolio_follows_account_across_browsers(client, marketplace):
    from apps.portfolio.models import PortfolioItem

    customer, vendors, _, _ = marketplace
    item = PortfolioItem.objects.create(
        vendor=vendors[0], title='تابلو کافه', slug='cafe'
    )
    client.force_login(customer)
    client.post(
        reverse('portfolio:board_toggle', kwargs={'pk': item.pk}), {'action': 'add'}
    )
    second = Client()
    second.force_login(customer)
    html = second.get(reverse('editorial:saved')).content.decode()
    assert item.title in html
    stranger = Client()
    stranger.force_login(vendors[1].user)
    assert item.title not in stranger.get(reverse('editorial:saved')).content.decode()


def test_design_requires_customer_approval_before_production(marketplace):
    from django.core.exceptions import PermissionDenied, ValidationError

    from apps.orders.services import advance_order, approve_design, propose_design

    customer, vendors, _, quote = marketplace
    order = accept_quote(quote=quote, user=customer)
    with pytest.raises(ValidationError):
        advance_order(order=order, user=vendors[0].user, stage='production')
    with pytest.raises(PermissionDenied):
        propose_design(
            order=order,
            user=vendors[1].user,
            image=None,
            price=6000000,
            installation_cost=500000,
            materials='حروف چلنیوم',
            notes='پیشنهاد طرح',
        )
    propose_design(
        order=order,
        user=vendors[0].user,
        image=None,
        price=6000000,
        installation_cost=500000,
        materials='حروف چلنیوم',
        notes='طبق فایل طرح در گفتگو',
    )
    with pytest.raises(PermissionDenied):
        approve_design(
            order=order, user=vendors[0].user, version=order.proposal_version
        )
    with pytest.raises(ValidationError):
        approve_design(order=order, user=customer, version=0)
    approve_design(order=order, user=customer, version=order.proposal_version)
    order.refresh_from_db()
    assert order.stage == 'production'
    assert order.agreed_price == 6500000


def test_compact_request_round_trip_and_recipient_choice(client, marketplace):
    customer, vendors, project, _ = marketplace
    client.force_login(customer)
    response = client.get(
        reverse('requests:from_vendor', kwargs={'slug': vendors[0].slug})
    )
    assert response.url == reverse('requests:wizard_need')
    client.post(
        reverse('requests:wizard_need'),
        {
            'city': project.city_id,
            'business_type': 'کافه',
            'use_case': 'shop',
            'audience': 'direct',
        },
    )
    response = client.post(
        reverse('requests:wizard_details'),
        {
            'description': 'تابلو سردر کافه',
            'choice': 'unsure',
            'text_content': 'کافه آبی',
            'budget_max': 9000000,
        },
    )
    assert response.status_code == 302
    review = client.get(reverse('requests:wizard_submit'))
    assert review.context['recipient'] == f'فقط {vendors[0].business_name}'
    client.post(reverse('requests:wizard_submit'))
    created = ProjectRequest.objects.exclude(pk=project.pk).get(customer=customer)
    assert created.needs_guidance and created.use_case == 'shop'
    assert created.preferred_vendor == vendors[0]
    assert created.text_content == 'کافه آبی'
    assert created.budget_max == 9000000
    assert 'request_wizard' not in client.session
    client.get(reverse('requests:wizard_start'))
    assert 'preferred_vendor_id' not in client.session['request_wizard']


def test_order_pages_enforce_roles_versions_and_final_delivery(client, marketplace):
    from django.core.exceptions import ValidationError

    from apps.orders.services import (
        advance_order,
        approve_design,
        complete_order,
        propose_design,
        request_design_changes,
    )

    customer, vendors, _, quote = marketplace
    order = accept_quote(quote=quote, user=customer)
    url = reverse('orders:progress', kwargs={'pk': order.pk})
    client.force_login(vendors[1].user)
    assert client.get(url).status_code == 404
    client.force_login(vendors[0].user)
    assert client.get(url).status_code == 200
    assert client.post(url, {'price': '-1'}).status_code == 400
    response = client.post(
        url,
        {
            'price': 6000000,
            'installation_cost': 500000,
            'materials': 'حروف چلنیوم و زمینه',
            'notes': 'تحویل ۷ روز پس از تأیید طرح، حمل شامل قیمت است.',
        },
    )
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.stage == 'approval'
    old_version = order.proposal_version
    request_design_changes(
        order=order, user=customer, version=old_version, notes='رنگ سفید باشد'
    )
    propose_design(
        order=order,
        user=vendors[0].user,
        image=None,
        price=6200000,
        installation_cost=500000,
        materials='حروف سفید',
        notes='طرح اصلاح شده در گفتگو',
    )
    client.force_login(customer)
    assert (
        client.post(url, {'action': 'approve', 'version': old_version}).status_code
        == 400
    )
    order.refresh_from_db()
    approve_design(order=order, user=customer, version=order.proposal_version)
    with pytest.raises(ValidationError):
        complete_order(order=order, user=customer)
    advance_order(order=order, user=vendors[0].user, stage='installation')
    advance_order(order=order, user=vendors[0].user, stage='delivered')
    complete_order(order=order, user=customer)
    order.refresh_from_db()
    assert order.status == 'completed' and order.agreed_price == 6700000
    with pytest.raises(ValidationError):
        complete_order(order=order, user=customer)


def test_browser_saves_can_be_imported_and_removed_from_account(client, marketplace):
    from apps.portfolio.models import PortfolioItem

    customer, vendors, _, _ = marketplace
    item = PortfolioItem.objects.create(
        vendor=vendors[0], title='نمونه آبی', slug='blue-sign'
    )
    client.post(
        reverse('portfolio:board_toggle', kwargs={'pk': item.pk}), {'action': 'add'}
    )
    client.force_login(customer)
    url = reverse('editorial:sync_saved')
    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 302
    other = Client()
    other.force_login(customer)
    assert item.title in other.get(reverse('editorial:saved')).content.decode()
    other.post(
        reverse('portfolio:board_toggle', kwargs={'pk': item.pk}), {'action': 'remove'}
    )
    assert item.title not in client.get(reverse('editorial:saved')).content.decode()


def test_saved_account_gallery_query_count_stays_constant(
    marketplace, django_assert_num_queries
):
    from django.test import RequestFactory

    from apps.editorial.models import Category, Idea, SavedReference
    from apps.editorial.views import saved
    from apps.portfolio.models import PortfolioItem

    customer, vendors, _, _ = marketplace
    category = Category.objects.create(name='کافه', slug='qa-cafe', kind='business')
    idea = Idea.objects.create(
        title='طرح کافه', category=category, image='ideas/test.jpg', status='published'
    )
    SavedReference.objects.create(user=customer, idea=idea)
    for n in range(12):
        item = PortfolioItem.objects.create(
            vendor=vendors[0], title=f'نمای کافه {n}', slug=f'cafe-{n}'
        )
        SavedReference.objects.create(user=customer, portfolio_item=item)
    request = RequestFactory().get('/inspiration/saved/')
    request.user = customer
    request.session = {}
    with django_assert_num_queries(4):
        assert saved(request).status_code == 200


def test_full_account_import_keeps_untransferred_browser_images(client, marketplace):
    from apps.editorial.models import SavedReference
    from apps.portfolio.models import PortfolioItem

    customer, vendors, _, _ = marketplace
    for n in range(24):
        item = PortfolioItem.objects.create(
            vendor=vendors[0], title=f'تابلو {n}', slug=f'sign-{n}'
        )
        SavedReference.objects.create(user=customer, portfolio_item=item)
    extra = PortfolioItem.objects.create(
        vendor=vendors[0], title='طرح مرورگر', slug='browser-only'
    )
    session = client.session
    session['inspiration_board'] = [extra.pk]
    session.save()
    client.force_login(customer)
    client.post(reverse('editorial:sync_saved'))
    assert client.session['inspiration_board'] == [extra.pk]
    assert not SavedReference.objects.filter(
        user=customer, portfolio_item=extra
    ).exists()


def test_back_navigation_keeps_both_recipient_options(client, marketplace):
    _, vendors, project, _ = marketplace
    client.get(reverse('requests:from_vendor', kwargs={'slug': vendors[0].slug}))
    client.post(
        reverse('requests:wizard_need'),
        {
            'city': project.city_id,
            'business_type': 'کافه',
            'use_case': 'shop',
            'audience': 'matched',
        },
    )
    form = client.get(reverse('requests:wizard_need')).context['form']
    assert (
        dict(form.fields['audience'].choices)['direct']
        == f'فقط {vendors[0].business_name}'
    )
    client.post(
        reverse('requests:wizard_need'),
        {
            'city': project.city_id,
            'business_type': 'کافه',
            'use_case': 'shop',
            'audience': 'direct',
        },
    )
    assert client.session['request_wizard']['preferred_vendor_id'] == vendors[0].pk
