"""Presentation decisions for the customer's next useful action."""

from django.urls import reverse

from apps.requests.models import ProjectRequest, RequestStatus


def next_project_action(project: ProjectRequest) -> dict[str, str]:
    detail = reverse('requests:request_detail', kwargs={'pk': project.pk})
    order = getattr(project, 'order', None)
    if order and order.status == 'active':
        return {
            'label': order.get_stage_display(),
            'hint': 'طرح، مبلغ و مراحل سفارش را اینجا پیگیری کنید.',
            'url': reverse('orders:progress', kwargs={'pk': order.pk}),
            'kind': 'active',
        }
    if project.status == RequestStatus.COMPLETED:
        if not getattr(project, 'review', None):
            return {
                'label': 'ثبت نظر و امتیاز',
                'hint': 'تجربهٔ همکاری‌تان را ثبت کنید.',
                'url': reverse('requests:review_create', kwargs={'pk': project.pk}),
                'kind': 'review',
            }
        return {
            'label': 'مشاهدهٔ سفارش',
            'hint': 'سفارش تمام شده و نظر شما ثبت شده است.',
            'url': detail,
            'kind': 'completed',
        }
    if project.status == RequestStatus.CANCELLED:
        return {
            'label': 'مشاهدهٔ جزئیات',
            'hint': 'این درخواست لغو شده است.',
            'url': detail,
            'kind': 'closed',
        }
    if project.status == RequestStatus.DRAFT:
        return {
            'label': 'مشاهدهٔ پیش‌نویس',
            'hint': 'این درخواست هنوز ارسال نشده است.',
            'url': detail,
            'kind': 'draft',
        }
    if project.quote_count:
        return {
            'label': 'مقایسهٔ پیشنهادها',
            'hint': 'قیمت، زمان اجرا و گارانتی را بررسی کنید.',
            'url': detail + '#quotes-title',
            'kind': 'offers',
        }
    return {
        'label': 'پیگیری درخواست',
        'hint': 'هنوز پیشنهادی برای این سفارش نرسیده است.',
        'url': detail,
        'kind': 'waiting',
    }
