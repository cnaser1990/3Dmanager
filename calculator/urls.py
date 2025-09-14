# calculator/urls.py
from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.index, name='index'),
    path('add_filament/', views.add_filament, name='add_filament'),
    path('filament/<int:pk>/', views.view_filament, name='view_filament'),
    path('filament/<int:pk>/edit/', views.edit_filament, name='edit_filament'),
    path('filament/<int:pk>/delete/', views.delete_filament, name='delete_filament'),
    path('add_project/<int:filament_id>/', views.add_project, name='add_project'),
    path('project/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('sales/', views.sales, name='sales'),
    path('reports/', views.reports, name='reports'),
    path('projects/', views.projects, name='projects'),
    path('calculate_preview/', views.calculate_preview, name='calculate_preview'),
    path('settings/pricing/', views.pricing_settings_view, name='pricing_settings'),
    path('api/settings/pricing.json', views.pricing_settings_json, name='pricing_settings_json'),
    path('api/calculate_preview/', views.calculate_preview, name='calculate_preview'),
]

