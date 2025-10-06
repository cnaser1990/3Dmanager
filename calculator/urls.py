# calculator/urls.py
from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Filament URLs
    path('filaments/', views.filaments, name='filaments'),
    path('add_filament/', views.add_filament, name='add_filament'),
    path('filament/<int:pk>/', views.view_filament, name='view_filament'),
    path('filament/<int:pk>/edit/', views.edit_filament, name='edit_filament'),
    path('filament/<int:pk>/delete/', views.delete_filament, name='delete_filament'),
    path('filament/<int:filament_id>/assign-project/', views.assign_project_to_filament, name='assign_project_to_filament'),
    path('filament-usage/<int:pk>/delete/', views.delete_filament_usage, name='delete_filament_usage'),
    path('filament/<int:filament_id>/delete-all-usages/', views.delete_all_filament_usages, name='delete_all_filament_usages'),
    
    # Project URLs (now independent)
    path('projects/', views.projects, name='projects'),
    path('add_project/', views.add_project, name='add_project'),
    path('project/<int:pk>/', views.view_project, name='view_project'),
    path('project/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    
    # Sales URLs
    path('sales/', views.sales, name='sales'),
    path('sales/history/', views.sales_history, name='sales_history'),
    path('sales/<int:pk>/delete/', views.delete_sale, name='delete_sale'),
    
    # Reports & Settings
    path('reports/', views.reports, name='reports'),
    path('settings/pricing/', views.pricing_settings_view, name='pricing_settings'),
    
    # API endpoints
    path('api/settings/pricing.json', views.pricing_settings_json, name='pricing_settings_json'),
    path('api/calculate_preview/', views.calculate_preview, name='calculate_preview'),
    
]