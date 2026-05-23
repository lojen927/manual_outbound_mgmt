from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import ManualOutboundOrder, ManualOutboundItem, Reason, Material

admin.site.site_header = _('手工出库系统')
admin.site.site_title = _('手工出库系统')


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_staff = True
        super().save_model(request, obj, form, change)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class ManualOutboundItemInline(admin.TabularInline):
    model = ManualOutboundItem
    extra = 1
    fields = [
        'material_code', 'material_name', 'specification',
        'quantity', 'unit', 'storage_location', 'remark',
        'status', 'system_order_no', 'close_reason',
    ]
    readonly_fields = ['closed_at', 'closed_by']


@admin.register(ManualOutboundOrder)
class ManualOutboundOrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'department', 'applicant', 'needs_system_posting', 'created_at', 'created_by']
    list_filter = ['needs_system_posting', 'created_at', 'department']
    search_fields = ['order_no', 'department', 'applicant', 'employee_id']
    readonly_fields = ['order_no', 'created_at', 'updated_at', 'created_by']
    inlines = [ManualOutboundItemInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Reason)
class ReasonAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['material_code', 'material_name', 'specification', 'unit']
    search_fields = ['material_code', 'material_name']
    list_per_page = 50
