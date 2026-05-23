from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile',
        verbose_name=_('用户')
    )
    must_change_password = models.BooleanField(_('首次登录需修改密码'), default=True)

    class Meta:
        verbose_name = _('用户配置')
        verbose_name_plural = _('用户配置')

    def __str__(self):
        return f'{self.user.username} {"配置"}'


class Reason(models.Model):
    code = models.CharField(_('编码'), max_length=30, unique=True)
    label = models.CharField(_('名称'), max_length=100)
    sort_order = models.IntegerField(_('排序'), default=0)
    is_active = models.BooleanField(_('启用'), default=True)

    class Meta:
        verbose_name = _('领料原因')
        verbose_name_plural = _('领料原因')
        ordering = ['sort_order']

    def __str__(self):
        return self.label


class Material(models.Model):
    material_code = models.CharField(_('物料编码'), max_length=50, unique=True)
    material_name = models.CharField(_('物料描述'), max_length=200, db_index=True)
    specification = models.CharField(_('规格'), max_length=200, blank=True, default='')
    unit = models.CharField(_('单位'), max_length=20, blank=True, default='')

    class Meta:
        verbose_name = _('物料')
        verbose_name_plural = _('物料')
        ordering = ['material_code']

    def __str__(self):
        return f'{self.material_code} - {self.material_name}'


class ManualOutboundOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ('draft', _('草稿')),
        ('submitted', _('已提交')),
        ('completed', _('已完成')),
        ('voided', _('已作废')),
    ]

    order_no = models.CharField(_('出库单号'), max_length=30, unique=True, editable=False)
    status = models.CharField(
        _('单据状态'), max_length=10, choices=ORDER_STATUS_CHOICES, default='draft'
    )
    department = models.CharField(_('领料部门'), max_length=50)
    applicant = models.CharField(_('领料人'), max_length=50)
    employee_id = models.CharField(_('工号'), max_length=20)
    phone = models.CharField(_('联系电话'), max_length=20, blank=True)
    reason = models.CharField(_('手工领料的原因'), max_length=20, default='urgent')
    remark = models.TextField(_('备注说明'), default='')
    needs_system_posting = models.BooleanField(_('是否需要系统补过账'), default=True)
    pending_order_numbers = models.TextField(
        _('未完成审批的系统领料申请单号'), blank=True,
        help_text=_('如有多个单号，请用换行分隔')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name=_('创建人')
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='voided_orders',
        verbose_name=_('作废人')
    )
    voided_at = models.DateTimeField(_('作废时间'), null=True, blank=True)
    void_reason = models.TextField(_('作废原因'), blank=True, default='')

    class Meta:
        verbose_name = _('手工出库单')
        verbose_name_plural = _('手工出库单')
        ordering = ['-created_at']

    def __str__(self):
        return self.order_no

    @property
    def reason_label(self):
        try:
            return Reason.objects.get(code=self.reason).label
        except Reason.DoesNotExist:
            return self.reason

    @property
    def can_void(self):
        """Returns True if the order can be voided (submitted within 2 hours)."""
        if self.status != 'submitted':
            return False
        elapsed = timezone.now() - self.updated_at
        return elapsed.total_seconds() <= 7200

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = self._generate_order_no()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_no():
        today = timezone.localdate()
        prefix = today.strftime('MO-%Y%m%d-')
        last_today = ManualOutboundOrder.objects.filter(
            order_no__startswith=prefix
        ).order_by('order_no').last()
        if last_today:
            last_seq = int(last_today.order_no[-3:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        return f'{prefix}{new_seq:03d}'


class ManualOutboundItem(models.Model):
    STATUS_CHOICES = [
        ('open', _('未关闭')),
        ('closed', _('已关闭')),
    ]

    order = models.ForeignKey(
        ManualOutboundOrder, on_delete=models.CASCADE,
        related_name='items', verbose_name=_('手工出库单')
    )
    material_code = models.CharField(_('物料编码'), max_length=30)
    material_name = models.CharField(_('物料描述'), max_length=100)
    specification = models.CharField(_('规格'), max_length=100, blank=True)
    quantity = models.DecimalField(_('数量'), max_digits=10, decimal_places=2)
    unit = models.CharField(_('单位'), max_length=20)
    storage_location = models.CharField(_('存货库位'), max_length=50, blank=True)
    remark = models.CharField(_('备注'), max_length=200, blank=True)
    status = models.CharField(
        _('状态'), max_length=10, choices=STATUS_CHOICES, default='open'
    )
    system_order_no = models.CharField(
        _('补录系统出库单号'), max_length=30, blank=True
    )
    close_reason = models.CharField(_('关闭原因'), max_length=200, blank=True)
    closed_at = models.DateTimeField(_('关闭时间'), null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='closed_items',
        verbose_name=_('关闭人')
    )

    class Meta:
        verbose_name = _('出库明细')
        verbose_name_plural = _('出库明细')
        ordering = ['id']

    def __str__(self):
        return f'{self.order.order_no} - {self.material_code}'
