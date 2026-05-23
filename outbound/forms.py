from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import ManualOutboundOrder, ManualOutboundItem, Reason


class ManualOutboundOrderForm(forms.ModelForm):
    remark = forms.CharField(
        label=_('备注说明'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'autocomplete': 'off'}),
        error_messages={'required': _('备注说明不能为空。')},
    )
    reason = forms.ChoiceField(
        label=_('手工领料的原因'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_reason', 'autocomplete': 'off'}),
    )

    class Meta:
        model = ManualOutboundOrder
        fields = [
            'department', 'applicant', 'employee_id', 'phone',
            'reason', 'remark', 'needs_system_posting', 'pending_order_numbers',
        ]
        labels = {
            'department': _('领料部门'),
            'applicant': _('领料人'),
            'employee_id': _('工号'),
            'phone': _('联系电话'),
            'needs_system_posting': _('后续是否需要系统补过账'),
            'pending_order_numbers': _('领料单号'),
        }
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'applicant': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'needs_system_posting': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pending_order_numbers': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 1, 'autocomplete': 'off'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reasons = Reason.objects.filter(is_active=True).order_by('sort_order')
        self.fields['reason'].choices = [(r.code, r.label) for r in reasons]

        # Replace needs_system_posting with radio buttons
        initial = True
        if self.instance and self.instance.pk is not None:
            initial = self.instance.needs_system_posting
        self.fields['needs_system_posting'] = forms.ChoiceField(
            choices=[('true', _('是')), ('false', _('否'))],
            widget=forms.RadioSelect(),
            initial='true' if initial else 'false',
            label=_('是否需要补过账'),
        )

    def clean_needs_system_posting(self):
        return self.cleaned_data.get('needs_system_posting') == 'true'


class ManualOutboundItemForm(forms.ModelForm):
    class Meta:
        model = ManualOutboundItem
        fields = [
            'material_code', 'material_name', 'specification',
            'quantity', 'unit', 'storage_location', 'remark',
        ]
        labels = {
            'material_code': _('物料编码'),
            'material_name': _('物料描述'),
            'specification': _('规格'),
            'quantity': _('数量'),
            'unit': _('单位'),
            'storage_location': _('存货库位'),
            'remark': _('备注'),
        }
        widgets = {
            'material_code': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'autocomplete': 'off'}),
            'material_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'autocomplete': 'off'}),
            'specification': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'autocomplete': 'off'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'step': '0.01', 'autocomplete': 'off'}),
            'unit': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'autocomplete': 'off'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'autocomplete': 'off'}),
            'remark': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['storage_location'].required = True


class BaseManualOutboundItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        total_with_data = sum(
            1 for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        )
        if total_with_data < 1:
            raise forms.ValidationError(_('至少需要填写一行出库明细。'))


ManualOutboundItemFormSet = inlineformset_factory(
    parent_model=ManualOutboundOrder,
    model=ManualOutboundItem,
    form=ManualOutboundItemForm,
    formset=BaseManualOutboundItemFormSet,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class ManualOutboundItemCloseForm(forms.Form):
    CLOSE_MODE_CHOICES = [
        ('system', _('补录系统出库单号')),
        ('manual', _('手动关闭')),
    ]
    close_mode = forms.ChoiceField(
        choices=CLOSE_MODE_CHOICES, label=_('关闭方式'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    system_order_no = forms.CharField(
        max_length=30, required=False, label=_('系统出库单号'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('输入系统出库单号')}),
    )
    close_reason = forms.CharField(
        max_length=200, required=False, label=_('关闭原因'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('手动关闭时必填')}),
    )

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('close_mode')
        if mode == 'system' and not cleaned.get('system_order_no'):
            self.add_error('system_order_no', _('补录系统出库单号时，单号不能为空'))
        if mode == 'manual' and not cleaned.get('close_reason'):
            self.add_error('close_reason', _('手动关闭时，关闭原因不能为空'))
        return cleaned


class ReasonForm(forms.ModelForm):
    class Meta:
        model = Reason
        fields = ['code', 'label', 'sort_order', 'is_active']
        labels = {
            'code': _('编码'),
            'label': _('名称'),
            'sort_order': _('排序'),
            'is_active': _('启用'),
        }
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ManualOutboundVoidForm(forms.Form):
    void_reason = forms.CharField(
        label=_('作废原因'), max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': _('请填写作废此出库单的原因'),
        }),
    )
