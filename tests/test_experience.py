"""Navigation and form contracts for the mobile experience."""

import re

import pytest
from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation


@pytest.mark.django_db
def test_mobile_navigation_has_native_modal_and_real_destinations(client):
    html = client.get(reverse('common:home')).content.decode()
    assert re.search(r'<dialog[^>]+data-nav-drawer', html)
    assert 'aria-labelledby="mobile-menu-title"' in html
    assert 'data-nav-close' in html
    navigation = re.search(
        r'<nav[^>]+aria-label="ناوبری موبایل"[^>]*>(.*?)</nav>', html, re.S
    )[1]
    for route in [
        'common:home',
        'portfolio:list',
        'vendors:list',
        'requests:wizard_start',
        'accounts:login',
    ]:
        assert reverse(route) in navigation


@pytest.mark.django_db
def test_phone_login_has_finished_auth_layout(client):
    html = client.get(reverse('accounts:login')).content.decode()
    assert 'page-auth' in html and 'auth-card' in html
    assert 'در کنسول چاپ می‌شود' not in html
    assert 'autocomplete="tel"' in html


def test_hidden_fields_keep_errors_without_an_empty_visible_label():
    class VerificationForm(forms.Form):
        phone = forms.CharField(widget=forms.HiddenInput)

    form = VerificationForm(data={})
    form.is_valid()
    html = render_to_string('components/_field.html', {'field': form['phone']})
    assert 'type="hidden"' in html
    assert '<label' not in html
    assert 'role="alert"' in html
    assert form['phone'].errors[0] in html


def test_server_error_is_native_and_context_free():
    with translation.override('fa'):
        html = render_to_string('500.html')
    assert 'lang="fa"' in html and 'dir="rtl"' in html
    assert 'خطا' in html
    assert 'Something went wrong' not in html


@pytest.mark.django_db
def test_home_prioritizes_service_request_and_keeps_discovery_available(client) -> None:
    html = client.get(reverse('common:home')).content.decode()
    hero = re.search(
        r'<section[^>]+aria-labelledby="hero-title"[^>]*>(.*?)</section>', html, re.S
    )[1]
    primary = re.search(r'<a[^>]+class="btn btn--primary[^>]+href="([^"]+)"', hero)[1]
    assert primary == reverse('requests:wizard_start')
    assert reverse('portfolio:list') in hero
    assert reverse('editorial:ideas') not in hero
    assert reverse('requests:wizard_start') in hero
    assert 'تصویر مفهومی' in hero


@pytest.mark.django_db
def test_landing_photo_offers_an_accessible_clock_preview(client) -> None:
    html = client.get(reverse('common:home')).content.decode()
    figure = re.search(r'<figure[^>]*>(.*?)</figure>', html, re.S)[1]
    trigger = re.search(r'<button[^>]+data-clock-open[^>]*>', figure)
    assert trigger is not None
    assert 'aria-controls="site-clock-dialog"' in trigger[0]
    assert 'aria-haspopup="dialog"' in trigger[0]
    assert 'id="site-clock-dialog"' in html
