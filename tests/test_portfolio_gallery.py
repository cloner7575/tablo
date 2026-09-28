from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from PIL import Image

from apps.accounts.models import UserRole
from apps.catalog.models import Service
from apps.locations.models import City, Province
from apps.portfolio.models import (
    MediaKind,
    PortfolioItem,
    PortfolioMedia,
    parse_aparat_hash,
)
from apps.portfolio.services import add_media, delete_media, move_media, set_cover
from apps.vendors.models import Vendor, VerificationStatus

User = get_user_model()

MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 256
WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 256


def _jpeg(name: str = "shot.jpg") -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (8, 8), color=(200, 30, 40)).save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


def _mp4(name: str = "clip.mp4", data: bytes = MP4_BYTES) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, content_type="video/mp4")


@pytest.fixture
def city(db):
    province = Province.objects.create(name="تهران", slug="tehran")
    return City.objects.create(name="تهران", slug="tehran", province=province)


@pytest.fixture
def service(db):
    return Service.objects.create(title="چلنیوم", slug="chalnium", sort_order=1)


def _make_vendor(phone: str, slug: str, city: City) -> Vendor:
    user = User.objects.create_user(
        username=phone,
        phone=phone,
        role=UserRole.VENDOR,
        is_verified=True,
        password="x",
    )
    return Vendor.objects.create(
        user=user,
        business_name=f"کارگاه {slug}",
        slug=slug,
        city=city,
        phone=phone,
        verification_status=VerificationStatus.APPROVED,
        is_active=True,
    )


@pytest.fixture
def vendor(city):
    return _make_vendor("09122222222", "sepehrad", city)


@pytest.fixture
def other_vendor(city):
    return _make_vendor("09123333333", "rival", city)


@pytest.fixture
def item(vendor, service, city):
    return PortfolioItem.objects.create(
        vendor=vendor,
        title="تابلو نئون کافه ساحل",
        slug="cafe-sahel",
        description="اجرای تابلو نئون سردر.",
        service=service,
        city=city,
        image=_jpeg("cover.jpg"),
    )


@pytest.fixture
def vendor_client(client: Client, vendor) -> Client:
    client.force_login(vendor.user)
    return client


# --- Aparat parsing -------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://www.aparat.com/v/abC123",
        "http://aparat.com/v/abC123/",
        "https://www.aparat.com/v/abC123?playlist=1",
        "https://www.aparat.com/video/video/embed/videohash/abC123/vt/frame",
    ],
)
def test_parse_aparat_hash_accepts_known_links(url: str) -> None:
    assert parse_aparat_hash(url) == "abC123"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://www.youtube.com/watch?v=abC123",
        "https://evil.com/aparat.com/v/abC123",
        "https://www.aparat.com/",
        "https://www.aparat.com/v/<script>",
    ],
)
def test_parse_aparat_hash_rejects_other_links(url: str) -> None:
    with pytest.raises(ValidationError):
        parse_aparat_hash(url)


# --- Services ---------------------------------------------------------------


@pytest.mark.django_db
def test_add_media_creates_rows_in_order(item):
    created = add_media(
        item=item,
        images=[_jpeg("a.jpg"), _jpeg("b.jpg")],
        video=_mp4(),
        aparat_url="https://www.aparat.com/v/abC123",
    )
    assert [m.kind for m in created] == [
        MediaKind.IMAGE,
        MediaKind.IMAGE,
        MediaKind.VIDEO,
        MediaKind.APARAT,
    ]
    orders = list(item.media.values_list("sort_order", flat=True))
    assert orders == sorted(orders)
    assert len(set(orders)) == 4
    assert item.media.get(kind=MediaKind.APARAT).aparat_hash == "abC123"


@pytest.mark.django_db
def test_set_cover_swaps_files(item):
    [media] = add_media(item=item, images=[_jpeg("inside.jpg")])
    set_cover(media=media)
    item.refresh_from_db()
    media.refresh_from_db()
    assert "inside" in item.image.name
    assert "cover" in media.image.name


@pytest.mark.django_db
def test_set_cover_without_existing_cover_promotes_media(vendor):
    bare = PortfolioItem.objects.create(vendor=vendor, title="بدون کاور")
    [media] = add_media(item=bare, images=[_jpeg("inside.jpg")])
    set_cover(media=media)
    bare.refresh_from_db()
    assert "inside" in bare.image.name
    assert not PortfolioMedia.objects.filter(pk=media.pk).exists()


@pytest.mark.django_db
def test_set_cover_rejects_video(item):
    [media] = add_media(item=item, video=_mp4())
    with pytest.raises(ValidationError):
        set_cover(media=media)


@pytest.mark.django_db
def test_move_media_reorders(item):
    first, second, third = add_media(
        item=item, images=[_jpeg("1.jpg"), _jpeg("2.jpg"), _jpeg("3.jpg")]
    )
    move_media(media=third, direction="up")
    assert list(item.media.values_list("pk", flat=True)) == [
        first.pk,
        third.pk,
        second.pk,
    ]
    move_media(media=first, direction="up")
    assert list(item.media.values_list("pk", flat=True))[0] == first.pk


@pytest.mark.django_db(transaction=True)
def test_delete_media_removes_row_and_file(item):
    [media] = add_media(item=item, images=[_jpeg("gone.jpg")])
    storage = media.image.storage
    name = media.image.name
    delete_media(media=media)
    assert not PortfolioMedia.objects.filter(pk=media.pk).exists()
    assert not storage.exists(name)


# --- Public detail ----------------------------------------------------------


@pytest.mark.django_db
def test_detail_renders_gallery_and_lightbox(client: Client, item, vendor):
    add_media(
        item=item,
        images=[_jpeg("g1.jpg")],
        video=_mp4(),
        aparat_url="https://www.aparat.com/v/abC123",
    )
    response = client.get(reverse("portfolio:detail", kwargs={"slug": item.slug}))
    assert response.status_code == 200
    body = response.content.decode()
    assert "pf-gallery" in body
    assert "<dialog" in body
    assert "<video" in body
    assert "aparat.com/video/video/embed/videohash/abC123" in body
    assert item.image.url in body
    for media in item.media.filter(kind=MediaKind.IMAGE):
        assert media.image.url in body
    assert "portfolio-gallery.js" in body
    assert vendor.business_name in body
    assert "درخواست قیمت مشابه" in body


@pytest.mark.django_db
def test_detail_gallery_has_stage_thumbs_and_more_tile(client: Client, item):
    add_media(item=item, images=[_jpeg(f"s{n}.jpg") for n in range(7)])
    response = client.get(reverse("portfolio:detail", kwargs={"slug": item.slug}))
    body = response.content.decode()
    assert body.count("data-gallery-slide=") == 8
    assert body.count("data-gallery-thumb=") == 4
    assert "data-gallery-more" in body
    assert "+۴" in body
    assert 'class="pf-buybox' in body


@pytest.mark.django_db
def test_detail_gallery_small_set_has_no_more_tile(client: Client, item):
    add_media(item=item, images=[_jpeg("s1.jpg"), _jpeg("s2.jpg")])
    response = client.get(reverse("portfolio:detail", kwargs={"slug": item.slug}))
    body = response.content.decode()
    assert body.count("data-gallery-thumb=") == 3
    assert "data-gallery-more" not in body


@pytest.mark.django_db
def test_detail_lightbox_filters_only_when_videos_exist(client: Client, item):
    url = reverse("portfolio:detail", kwargs={"slug": item.slug})
    add_media(item=item, images=[_jpeg("s1.jpg")])
    assert 'data-lightbox-filter="video"' not in client.get(url).content.decode()
    add_media(item=item, video=_mp4())
    assert 'data-lightbox-filter="video"' in client.get(url).content.decode()


@pytest.mark.django_db
def test_detail_without_media_falls_back_to_demo_image(client: Client, vendor):
    bare = PortfolioItem.objects.create(vendor=vendor, title="بدون عکس", slug="bare")
    response = client.get(reverse("portfolio:detail", kwargs={"slug": bare.slug}))
    assert response.status_code == 200
    assert "img/demo/" in response.content.decode()


@pytest.mark.django_db
def test_detail_hides_drafts(client: Client, item):
    item.is_published = False
    item.save()
    response = client.get(reverse("portfolio:detail", kwargs={"slug": item.slug}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_query_count_is_constant(client: Client, item):
    url = reverse("portfolio:detail", kwargs={"slug": item.slug})
    add_media(item=item, images=[_jpeg("q1.jpg")])
    with CaptureQueriesContext(connection) as few:
        client.get(url)
    add_media(item=item, images=[_jpeg(f"q{n}.jpg") for n in range(2, 8)])
    with CaptureQueriesContext(connection) as many:
        client.get(url)
    assert len(many) == len(few)


# --- Vendor panel -----------------------------------------------------------


@pytest.mark.django_db
def test_create_page_renders_drop_zones(vendor_client: Client):
    response = vendor_client.get(reverse("portfolio:create"))
    assert response.status_code == 200
    body = response.content.decode()
    assert body.count("data-drop") >= 2
    assert "pf-form-grid" in body


@pytest.mark.django_db
def test_create_page_accepts_video_and_aparat(vendor_client: Client, vendor):
    response = vendor_client.post(
        reverse("portfolio:create"),
        {
            "title": "تابلو با ویدیو",
            "is_published": "on",
            "gallery": [_jpeg("g1.jpg")],
            "video": _mp4(),
            "poster": _jpeg("poster.jpg"),
            "aparat_url": "https://www.aparat.com/v/abC123",
        },
    )
    assert response.status_code == 302
    created = PortfolioItem.objects.get(vendor=vendor, title="تابلو با ویدیو")
    assert list(created.media.values_list("kind", flat=True)) == [
        MediaKind.IMAGE,
        MediaKind.VIDEO,
        MediaKind.APARAT,
    ]
    assert created.media.get(kind=MediaKind.VIDEO).poster


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("extra", "field"),
    [
        ({"poster": "poster"}, "poster"),
        ({"video": "bad"}, "video"),
        ({"aparat_url": "https://www.youtube.com/watch?v=abc"}, "aparat_url"),
    ],
)
def test_create_page_rejects_bad_video_input(
    vendor_client: Client, vendor, extra: dict[str, str], field: str
):
    data: dict[str, object] = {"title": "نمونه"}
    for key, value in extra.items():
        if value == "poster":
            data[key] = _jpeg("poster.jpg")
        elif value == "bad":
            data[key] = _mp4(data=b"not a video at all")
        else:
            data[key] = value
    response = vendor_client.post(reverse("portfolio:create"), data)
    assert response.status_code == 400
    assert field in response.context["form"].errors
    assert not PortfolioItem.objects.filter(vendor=vendor).exists()


@pytest.mark.django_db
def test_create_page_counts_video_toward_limit(vendor_client: Client, vendor, settings):
    settings.PORTFOLIO_MAX_MEDIA = 2
    response = vendor_client.post(
        reverse("portfolio:create"),
        {
            "title": "پر",
            "gallery": [_jpeg("a.jpg"), _jpeg("b.jpg")],
            "aparat_url": "https://www.aparat.com/v/abC123",
        },
    )
    assert response.status_code == 400
    assert not PortfolioItem.objects.filter(vendor=vendor).exists()


@pytest.mark.django_db
def test_create_page_rejects_missing_title(vendor_client: Client, vendor):
    response = vendor_client.post(reverse("portfolio:create"), {"title": ""})
    assert response.status_code == 400
    assert not PortfolioItem.objects.filter(vendor=vendor).exists()


@pytest.mark.django_db
def test_manage_list_is_read_only(vendor_client: Client):
    response = vendor_client.post(reverse("portfolio:manage"), {"title": "x"})
    assert response.status_code == 405


@pytest.mark.django_db
def test_manage_filters_by_status_and_search(vendor_client: Client, item, vendor):
    PortfolioItem.objects.create(
        vendor=vendor, title="حروف برجسته بوتیک", slug="boutique", is_published=False
    )
    url = reverse("portfolio:manage")

    response = vendor_client.get(url)
    assert response.context["counts"] == {"all": 2, "published": 1, "draft": 1}

    drafts = vendor_client.get(url, {"status": "draft"}).content.decode()
    assert "حروف برجسته بوتیک" in drafts
    assert item.title not in drafts

    found = vendor_client.get(url, {"q": "کافه"}).content.decode()
    assert item.title in found
    assert "حروف برجسته بوتیک" not in found

    empty = vendor_client.get(url, {"q": "ناموجود"}).content.decode()
    assert "نتیجه‌ای پیدا نشد" in empty


@pytest.mark.django_db
def test_manage_ignores_unknown_status(vendor_client: Client, item):
    response = vendor_client.get(reverse("portfolio:manage"), {"status": "bogus"})
    assert response.status_code == 200
    assert response.context["status"] == "all"


@pytest.mark.django_db
def test_create_page_creates_item_with_gallery(vendor_client: Client, vendor):
    response = vendor_client.post(
        reverse("portfolio:create"),
        {
            "title": "تابلو بوتیک",
            "description": "حروف برجسته",
            "is_published": "on",
            "image": _jpeg("cover.jpg"),
            "gallery": [_jpeg("g1.jpg"), _jpeg("g2.jpg")],
        },
    )
    assert response.status_code == 302
    created = PortfolioItem.objects.get(vendor=vendor, title="تابلو بوتیک")
    assert created.is_published
    assert created.media.filter(kind=MediaKind.IMAGE).count() == 2


@pytest.mark.django_db
def test_manage_requires_vendor_profile(client: Client, city):
    user = User.objects.create_user(
        username="09124444444", phone="09124444444", password="x"
    )
    client.force_login(user)
    assert client.get(reverse("portfolio:manage")).status_code == 403
    assert client.get(reverse("portfolio:create")).status_code == 403


@pytest.mark.django_db
def test_edit_updates_item(vendor_client: Client, item):
    url = reverse("portfolio:edit", kwargs={"pk": item.pk})
    assert vendor_client.get(url).status_code == 200
    response = vendor_client.post(
        url, {"title": "عنوان تازه", "description": "", "is_published": ""}
    )
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.title == "عنوان تازه"
    assert not item.is_published


@pytest.mark.django_db
def test_media_add_accepts_images_video_and_aparat(vendor_client: Client, item):
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    vendor_client.post(url, {"images": [_jpeg("x.jpg"), _jpeg("y.jpg")]})
    vendor_client.post(url, {"video": _mp4(), "poster": _jpeg("poster.jpg")})
    vendor_client.post(url, {"aparat_url": "https://www.aparat.com/v/abC123"})
    kinds = list(item.media.values_list("kind", flat=True))
    assert kinds == [
        MediaKind.IMAGE,
        MediaKind.IMAGE,
        MediaKind.VIDEO,
        MediaKind.APARAT,
    ]
    assert item.media.get(kind=MediaKind.VIDEO).poster


@pytest.mark.django_db
def test_media_add_accepts_webm(vendor_client: Client, item):
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    webm = SimpleUploadedFile("clip.webm", WEBM_BYTES, content_type="video/webm")
    response = vendor_client.post(url, {"video": webm})
    assert response.status_code == 302
    assert item.media.filter(kind=MediaKind.VIDEO).exists()


@pytest.mark.django_db
def test_media_add_requires_something(vendor_client: Client, item):
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    response = vendor_client.post(url, {})
    assert response.status_code == 400
    assert not item.media.exists()


@pytest.mark.django_db
def test_media_add_error_reopens_submitting_tab(vendor_client: Client, item):
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    response = vendor_client.post(url, {"tab": "aparat"})
    assert response.status_code == 400
    assert response.context["active_tab"] == "aparat"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "upload",
    [
        SimpleUploadedFile("clip.mov", MP4_BYTES, content_type="video/quicktime"),
        SimpleUploadedFile("fake.mp4", b"not a video at all", content_type="video/mp4"),
    ],
    ids=["wrong-content-type", "wrong-signature"],
)
def test_media_add_rejects_bad_video(vendor_client: Client, item, upload):
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    upload.seek(0)
    response = vendor_client.post(url, {"video": upload})
    assert response.status_code == 400
    assert not item.media.exists()


@pytest.mark.django_db
def test_media_add_rejects_oversized_video(vendor_client: Client, item, settings):
    settings.VIDEO_UPLOAD_MAX_BYTES = 64
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    response = vendor_client.post(url, {"video": _mp4()})
    assert response.status_code == 400
    assert not item.media.exists()


@pytest.mark.django_db
def test_media_add_rejects_bad_aparat_link(vendor_client: Client, item):
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    response = vendor_client.post(url, {"aparat_url": "https://youtube.com/x"})
    assert response.status_code == 400
    assert "آپارات" in response.content.decode()
    assert not item.media.exists()


@pytest.mark.django_db
def test_media_add_enforces_limit(vendor_client: Client, item, settings):
    settings.PORTFOLIO_MAX_MEDIA = 2
    add_media(item=item, images=[_jpeg("1.jpg")])
    url = reverse("portfolio:media_add", kwargs={"pk": item.pk})
    response = vendor_client.post(url, {"images": [_jpeg("2.jpg"), _jpeg("3.jpg")]})
    assert response.status_code == 400
    assert item.media.count() == 1


@pytest.mark.django_db
def test_media_actions_via_views(vendor_client: Client, item):
    first, second = add_media(item=item, images=[_jpeg("1.jpg"), _jpeg("2.jpg")])
    move_url = reverse(
        "portfolio:media_move", kwargs={"pk": second.pk, "direction": "up"}
    )
    assert vendor_client.post(move_url).status_code == 302
    assert list(item.media.values_list("pk", flat=True)) == [second.pk, first.pk]

    cover_url = reverse("portfolio:media_cover", kwargs={"pk": first.pk})
    assert vendor_client.post(cover_url).status_code == 302
    item.refresh_from_db()
    assert "1" in item.image.name

    delete_url = reverse("portfolio:media_delete", kwargs={"pk": second.pk})
    assert vendor_client.post(delete_url).status_code == 302
    assert not PortfolioMedia.objects.filter(pk=second.pk).exists()


@pytest.mark.django_db
def test_other_vendor_cannot_touch_media(client: Client, item, other_vendor):
    [media] = add_media(item=item, images=[_jpeg("mine.jpg")])
    client.force_login(other_vendor.user)
    urls = [
        ("get", reverse("portfolio:edit", kwargs={"pk": item.pk})),
        ("post", reverse("portfolio:media_add", kwargs={"pk": item.pk})),
        ("post", reverse("portfolio:media_cover", kwargs={"pk": media.pk})),
        (
            "post",
            reverse("portfolio:media_move", kwargs={"pk": media.pk, "direction": "up"}),
        ),
        ("post", reverse("portfolio:media_delete", kwargs={"pk": media.pk})),
    ]
    for method, url in urls:
        assert getattr(client, method)(url).status_code == 404, url
    assert PortfolioMedia.objects.filter(pk=media.pk).exists()


@pytest.mark.django_db
def test_media_actions_reject_get(vendor_client: Client, item):
    [media] = add_media(item=item, images=[_jpeg("1.jpg")])
    url = reverse("portfolio:media_delete", kwargs={"pk": media.pk})
    assert vendor_client.get(url).status_code == 405


# --- API --------------------------------------------------------------------


@pytest.mark.django_db
def test_api_portfolio_includes_media(client: Client, item):
    add_media(
        item=item,
        images=[_jpeg("api.jpg")],
        aparat_url="https://www.aparat.com/v/abC123",
    )
    response = client.get(
        reverse("api:v1:portfolio-detail", kwargs={"slug": item.slug})
    )
    assert response.status_code == 200
    media = response.json()["media"]
    assert [m["kind"] for m in media] == ["image", "aparat"]
    assert media[1]["embed_url"].endswith("/videohash/abC123/vt/frame")
