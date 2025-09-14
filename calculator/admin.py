# calculator/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Filament, Project, Sale

@admin.register(Filament)
class FilamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'material', 'remaining_amount', 'initial_amount', 'cost_per_kg', 'created_date']
    list_filter = ['material', 'created_date']
    search_fields = ['name', 'color']
    readonly_fields = ['created_date']
    

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'model_name', 'filament', 'total_cost', 'selling_price', 'created_date']
    list_filter = ['filament', 'created_date']
    search_fields = ['model_name', 'code']
    readonly_fields = ['code', 'filament_weight_used', 'electricity_cost', 'depreciation_cost', 
                      'post_processing_cost', 'painting_cost', 'material_cost', 'total_cost', 
                      'selling_price', 'created_date']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['project_code', 'customer_name', 'customer_phone', 'sale_date']
    list_filter = ['sale_date', 'project__filament']
    search_fields = ['customer_name', 'customer_phone', 'project__model_name', 'project_code']
    readonly_fields = ['project_code', 'sale_date']
    
