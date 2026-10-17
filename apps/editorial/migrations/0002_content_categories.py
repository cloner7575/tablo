from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

CATEGORIES = [
    ('cafe', 'کافه', 'business', 'ایده‌های تابلو کافه؛ از حروف مینیمال تا نور گرم و نمای صنعتی.'),
    ('restaurant', 'رستوران', 'business', 'ایده‌های سردر رستوران و فست‌فود برای هماهنگی با هویت فضا.'),
    ('boutique', 'پوشاک و بوتیک', 'business', 'ایده‌های تابلو بوتیک و فروشگاه پوشاک، با سبک‌های مدرن و لوکس.'),
    ('jewelry', 'طلا و جواهر', 'business', 'ایده‌های تابلو برای طلافروشی و گالری جواهر؛ جزئیات، حروف و نور.'),
    ('beauty', 'زیبایی و سلامت', 'business', 'ایده‌های طراحی تابلو برای سالن زیبایی و فضاهای سلامت.'),
    ('retail', 'فروشگاه', 'business', 'ایده‌های تابلو مغازه و فروشگاه برای شناخت سبک و خوانایی سردر.'),
    ('selection', 'انتخاب تابلو', 'guide', 'راهنماهای انتخاب تابلو برای مغازه، از شناخت نیاز تا بررسی پیشنهادها.'),
    ('design', 'طراحی و الهام', 'guide', 'راهنماهای طراحی تابلو، هویت بصری و استفاده از ایده‌های مفهومی.'),
    ('project', 'از ایده تا اجرا', 'guide', 'راهنماهای آماده‌کردن بریف و همکاری با متخصص تابلوسازی.'),
]


def seed_categories(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    category = apps.get_model('editorial', 'Category')
    for index, (slug, name, kind, description) in enumerate(CATEGORIES):
        category.objects.using(schema_editor.connection.alias).get_or_create(
            slug=slug,
            defaults={'name': name, 'kind': kind, 'description': description, 'sort_order': index},
        )


def remove_empty_categories(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    category = apps.get_model('editorial', 'Category')
    category.objects.using(schema_editor.connection.alias).filter(
        slug__in=[item[0] for item in CATEGORIES], ideas__isnull=True, articles__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [('editorial', '0001_initial')]
    operations = [migrations.RunPython(seed_categories, remove_empty_categories)]
