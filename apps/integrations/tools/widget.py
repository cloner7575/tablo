import base64
from pathlib import Path

from django.conf import settings
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from apps.integrations.tools.context import actor, database_tool

RESOURCE = 'ui://tablo/design-saver.html'


def show_design_saver() -> dict[str, object]:
    """
    کارت فارسی انتخاب و ذخیره تصویر در سایت. وقتی فایل تصویر مستقیم در ابزار
    در دسترس نبود، این کارت را باز کن تا تابلوساز در همین گفتگو تصویر را
    انتخاب یا پیوست کند.
    """
    connection = actor(write=True)
    return {'business_name': connection.vendor.business_name}


def register(server: FastMCP) -> None:
    @server.resource(
        RESOURCE,
        mime_type='text/html;profile=mcp-app',
        meta={
            'ui': {
                'prefersBorder': True,
                'csp': {'connectDomains': [], 'resourceDomains': []},
            },
            'openai/widgetDescription': (
                'انتخاب تصویر و ذخیره خصوصی در پنل تابلوساز؛ همراه پیش‌نمایش نتیجه.'
            ),
        },
    )
    def design_saver() -> str:
        root = Path(settings.BASE_DIR)
        html = (root / 'templates/pages/integrations/widget.html').read_text()
        font = base64.b64encode(
            (root / 'static/fonts/vazirmatn-arabic.woff2').read_bytes()
        ).decode()
        return html.replace('FONT_DATA', font)

    server.add_tool(
        database_tool(show_design_saver),
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, openWorldHint=False
        ),
        meta={
            'ui': {'resourceUri': RESOURCE},
            'openai/outputTemplate': RESOURCE,
        },
    )
