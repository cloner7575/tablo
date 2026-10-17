from django import forms
from django.utils.translation import gettext_lazy as _

from apps.common.validators import validate_uploaded_image
from apps.orders.models import OrderStage


class DesignProposalForm(forms.Form):
    image = forms.ImageField(
        label=_("عکس طرح"),
        required=False,
        validators=[validate_uploaded_image],
        help_text=_("یا طرح را در گفتگو ارسال کنید و در توضیحات به آن اشاره کنید."),
    )
    price = forms.IntegerField(label=_("مبلغ نهایی ساخت (تومان)"), min_value=0)
    installation_cost = forms.IntegerField(
        label=_("مبلغ نهایی نصب (تومان)"), min_value=0
    )
    materials = forms.CharField(
        label=_("مشخصات و اقلام شامل قیمت"),
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    notes = forms.CharField(
        label=_("توضیح طرح، زمان اجرا و هزینه‌های خارج از قیمت"),
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class DesignDecisionForm(forms.Form):
    action = forms.ChoiceField(choices=(("approve", "تأیید"), ("changes", "اصلاح")))
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    notes = forms.CharField(
        label=_("چه چیزی تغییر کند؟"),
        required=False,
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self) -> dict:
        cleaned = super().clean()
        if cleaned.get("action") == "changes" and not cleaned.get("notes", "").strip():
            self.add_error("notes", _("تغییر مدنظرتان را بنویسید."))
        return cleaned


class OrderStageForm(forms.Form):
    stage = forms.ChoiceField(
        choices=(
            (OrderStage.INSTALLATION, _("ساخت تمام شده؛ هماهنگی نصب")),
            (OrderStage.DELIVERED, _("نصب و تحویل انجام شده")),
        )
    )
