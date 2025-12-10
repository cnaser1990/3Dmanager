# calculator/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Filament, Project, Sale, FilamentUsage, PricingSettings


@admin.register(Filament)
class FilamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'material', 'remaining_display', 'initial_amount', 'cost_per_kg', 'created_date']
    list_filter = ['material', 'created_date']
    search_fields = ['name', 'color']
    readonly_fields = ['created_date', 'usage_percentage_display', 'remaining_value_display']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'color', 'material')
        }),
        ('موجودی', {
            'fields': ('initial_amount', 'remaining_amount', 'usage_percentage_display', 'remaining_value_display')
        }),
        ('قیمت', {
            'fields': ('cost_per_kg',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_date',),
            'classes': ('collapse',)
        }),
    )
    
    def remaining_display(self, obj):
        percentage = obj.usage_percentage
        if percentage > 70:
            color = 'green'
        elif percentage > 30:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f} متر ({:.0f}%)</span>',
            color,
            obj.remaining_amount,
            percentage
        )
    remaining_display.short_description = 'موجودی'
    
    def usage_percentage_display(self, obj):
        return f"{obj.usage_percentage}%"
    usage_percentage_display.short_description = 'درصد موجودی'
    
    def remaining_value_display(self, obj):
        return f"{obj.remaining_value:,.0f} تومان"
    remaining_value_display.short_description = 'ارزش موجودی'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'model_name', 'has_image_display', 'filament_used_mm', 
                    'print_time_hours', 'usage_count', 'created_date']
    list_filter = ['created_date', 'post_processing_enabled', 'painting_enabled']
    search_fields = ['model_name', 'code']
    readonly_fields = ['code', 'created_date', 'filament_weight_display', 'usage_count', 'assigned_filaments_display']
    
    fieldsets = (
        ('اطلاعات مدل', {
            'fields': ('model_name', 'code', 'picture')
        }),
        ('مشخصات فنی', {
            'fields': ('filament_used_mm', 'filament_weight_display', 'print_time_hours', 
                      'size_x', 'size_y', 'size_z')
        }),
        ('خدمات اضافی', {
            'fields': ('post_processing_enabled', 'painting_enabled')
        }),
        ('اختصاص‌ها', {
            'fields': ('usage_count', 'assigned_filaments_display'),
            'classes': ('collapse',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_date',),
            'classes': ('collapse',)
        }),
    )
    
    def has_image_display(self, obj):
        if obj.has_image:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">✗</span>')
    has_image_display.short_description = 'تصویر'
    
    def filament_weight_display(self, obj):
        return f"{obj.filament_weight_grams:.2f} گرم"
    filament_weight_display.short_description = 'وزن فیلامنت'
    
    def usage_count(self, obj):
        count = obj.filamentusage_set.count()
        if count > 0:
            return format_html('<span style="color: green;">{} فیلامنت</span>', count)
        return format_html('<span style="color: gray;">هیچ</span>')
    usage_count.short_description = 'تعداد اختصاص'
    
    def assigned_filaments_display(self, obj):
        usages = obj.filamentusage_set.select_related('filament').all()
        if not usages:
            return "هیچ فیلامنتی اختصاص نیافته"
        
        items = []
        for usage in usages:
            items.append(
                f"{usage.filament.name} ({usage.filament.color}) - "
                f"{usage.selling_price:,.0f} تومان"
            )
        return format_html('<br>'.join(items))
    assigned_filaments_display.short_description = 'فیلامنت‌های اختصاص یافته'


@admin.register(FilamentUsage)
class FilamentUsageAdmin(admin.ModelAdmin):
    list_display = ['project_display', 'filament_display', 'total_cost_display', 
                    'selling_price_display', 'profit_display', 'assigned_date']
    list_filter = ['assigned_date', 'filament__material', 'filament']
    search_fields = ['project__model_name', 'project__code', 'filament__name']
    readonly_fields = ['filament_weight_used', 'material_cost', 'electricity_cost', 
                      'depreciation_cost', 'post_processing_cost', 'painting_cost',
                      'total_cost', 'selling_price', 'assigned_date', 'profit_display']
    
    fieldsets = (
        ('اختصاص', {
            'fields': ('filament', 'project')
        }),
        ('هزینه‌ها', {
            'fields': ('filament_weight_used', 'material_cost', 'electricity_cost', 
                      'depreciation_cost', 'post_processing_cost', 'painting_cost')
        }),
        ('قیمت‌گذاری', {
            'fields': ('total_cost', 'selling_price', 'profit_display')
        }),
        ('اطلاعات سیستم', {
            'fields': ('assigned_date',),
            'classes': ('collapse',)
        }),
    )
    
    def project_display(self, obj):
        return f"{obj.project.code} - {obj.project.model_name}"
    project_display.short_description = 'مدل'
    
    def filament_display(self, obj):
        return f"{obj.filament.name} ({obj.filament.color})"
    filament_display.short_description = 'فیلامنت'
    
    def total_cost_display(self, obj):
        return f"{obj.total_cost:,.0f} تومان"
    total_cost_display.short_description = 'هزینه کل'
    
    def selling_price_display(self, obj):
        return f"{obj.selling_price:,.0f} تومان"
    selling_price_display.short_description = 'قیمت فروش'
    
    def profit_display(self, obj):
        profit = obj.profit
        color = 'green' if profit > 0 else 'red'
        return format_html(
            '<span style="color: {};">{:,.0f} تومان</span>',
            color,
            profit
        )
    profit_display.short_description = 'سود'


admin.site.register(Sale)

@admin.register(PricingSettings)
class PricingSettingsAdmin(admin.ModelAdmin):
    list_display = ['singleton_display', 'profit_percent', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('هزینه‌های پایه', {
            'fields': ('power_price_per_kwh', 'depreciation_per_hour', 'filament_waste_percent', 'packaging_cost')
        }),
        ('خدمات', {
            'fields': ('post_processing_rate', 'painting_rate_per_cm2')
        }),
        ('استراتژی قیمت‌گذاری', {
            'fields': ('profit_percent', 'round_to_nearest')
        }),
        ('اطلاعات سیستم', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def singleton_display(self, obj):
        return "تنظیمات قیمت‌گذاری"
    singleton_display.short_description = 'تنظیمات'
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not PricingSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False