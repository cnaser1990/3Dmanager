# calculator/views.py
from datetime import timedelta
import json
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .models import (
    Filament,
    Project,
    Sale,
    PricingSettings,
    FilamentUsage,
)
from .forms import (
    FilamentForm,
    ProjectForm,
    SaleForm,
    PricingSettingsForm,
    FilamentUsageForm,
)

import logging
logger = logging.getLogger(__name__)


def index(request):
    filaments = Filament.objects.all()
    recent_projects = Project.objects.all()[:10]
    usage_stats = FilamentUsage.objects.aggregate(
        count=Count('id'),
        total_cost=Sum('total_cost'),
        total_selling=Sum('selling_price')
    )
    thirty_days_ago = timezone.now() - timedelta(days=30)
    sales_stats = Sale.objects.filter(sale_date__gte=thirty_days_ago).aggregate(
        count=Count('id'),
        total_revenue=Sum('total_price')
    )
    projects = Project.objects.all()
    context = {
        'filaments': filaments,
        'recent_projects': recent_projects,
        'usage_stats': usage_stats,
        'sales_stats': sales_stats,
        "projects": projects,
    }
    return render(request, 'calculator/index.html', context)


def filaments(request):
    q = request.GET.get('q', '').strip()
    material = request.GET.get('material', '').strip()
    sort = request.GET.get('sort', '-created_date').strip()
    view_mode = request.GET.get('view', 'grid').strip()
    page = request.GET.get('page', 1)

    filaments_qs = Filament.objects.all()
    if q:
        filaments_qs = filaments_qs.filter(
            Q(name__icontains=q) |
            Q(color__icontains=q) |
            Q(material__icontains=q)
        )
    if material:
        filaments_qs = filaments_qs.filter(material=material)

    allowed_sorts = [
        '-created_date', 'created_date',
        'name', '-name',
        'material', '-material',
        '-remaining_amount', 'remaining_amount',
        '-cost_per_kg', 'cost_per_kg',
    ]
    if sort in allowed_sorts:
        filaments_qs = filaments_qs.order_by(sort)
    else:
        filaments_qs = filaments_qs.order_by('-created_date')

    total_count = filaments_qs.count()
    total_remaining = filaments_qs.aggregate(Sum('remaining_amount'))['remaining_amount__sum'] or 0

    total_value = 0
    for f in filaments_qs:
        total_value += f.remaining_value

    materials_count = filaments_qs.values('material').distinct().count()
    per_page = 12 if view_mode == 'grid' else 20
    paginator = Paginator(filaments_qs, per_page)
    page_obj = paginator.get_page(page)

    context = {
        'filaments': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'total_remaining': total_remaining,
        'total_value': total_value,
        'materials_count': materials_count,
        'q': q,
        'material': material,
        'sort': sort,
        'view_mode': view_mode,
    }
    return render(request, 'calculator/filaments.html', context)


def add_filament(request):
    if request.method == 'POST':
        form = FilamentForm(request.POST)
        if form.is_valid():
            filament = form.save()
            messages.success(
                request,
                f'✅ فیلامنت "{filament.name} - {filament.color}" با موفقیت اضافه شد'
            )
            return redirect('calculator:view_filament', pk=filament.pk)
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید')
    else:
        form = FilamentForm()
    return render(request, 'calculator/add_filament.html', {'form': form})


def edit_filament(request, pk):
    filament = get_object_or_404(Filament, pk=pk)
    if request.method == 'POST':
        form = FilamentForm(request.POST, instance=filament)
        if form.is_valid():
            updated_filament = form.save()
            messages.success(
                request,
                f'✅ اطلاعات فیلامنت "{updated_filament.name}" بروزرسانی شد'
            )
            return redirect('calculator:view_filament', pk=filament.pk)
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید')
    else:
        form = FilamentForm(instance=filament)
    return render(request, 'calculator/edit_filament.html', {'form': form, 'filament': filament})


def view_filament(request, pk):
    filament = get_object_or_404(Filament, pk=pk)
    filament_usages = FilamentUsage.objects.filter(filament=filament).select_related('project')
    stats_count = filament_usages.count()
    stats_total_cost = sum(usage.total_all_costs for usage in filament_usages)
    stats_total_selling = sum(usage.total_selling_price for usage in filament_usages)
    stats_total_weight = sum(usage.total_weight_used for usage in filament_usages)
    profit = stats_total_selling - stats_total_cost
    avg_profit = (profit / stats_count) if stats_count else 0
    stats = {
        'count': stats_count,
        'total_cost': stats_total_cost,
        'total_selling': stats_total_selling,
        'total_weight': stats_total_weight,
        'profit': profit,
        'avg_profit': avg_profit,
    }
    try:
        cost_per_kg = float(filament.cost_per_kg or 0)
    except Exception:
        cost_per_kg = 0.0
    cost_per_meter = (cost_per_kg / 330.0) if cost_per_kg else 0.0
    try:
        remaining_amount_m = float(filament.remaining_amount or 0)
    except Exception:
        remaining_amount_m = 0.0
    remaining_value = remaining_amount_m * cost_per_meter
    try:
        initial_amount_m = float(filament.initial_amount or 0)
    except Exception:
        initial_amount_m = 0.0
    if initial_amount_m > 0:
        usage_percentage = int(round((remaining_amount_m / initial_amount_m) * 100))
    else:
        usage_percentage = 0
    usage_percentage = max(0, min(100, usage_percentage))
    context = {
        'filament': filament,
        'filament_usages': filament_usages,
        'stats': stats,
        'cost_per_meter': cost_per_meter,
        'remaining_value': remaining_value,
        'usage_percentage': usage_percentage,
    }
    return render(request, 'calculator/view_filament.html', context)


def delete_filament(request, pk):
    filament = get_object_or_404(Filament, pk=pk)
    usage_count = FilamentUsage.objects.filter(filament=filament).count()
    next_url = request.POST.get('next') or request.GET.get('next')
    default_redirect = reverse('calculator:filaments')
    if request.method == 'POST':
        if usage_count > 0:
            messages.error(
                request,
                f'نمی‌توان این فیلامنت را حذف کرد چون {usage_count} مدل به آن اختصاص داده شده است. ابتدا اختصاص‌ها را حذف کنید.'
            )
            return redirect('calculator:delete_all_filament_usages', filament_id=pk)
        filament_name = f"{filament.name} ({filament.color})"
        filament.delete()
        messages.success(request, f'فیلامنت "{filament_name}" با موفقیت حذف شد')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect(default_redirect)
    consumed_amount = filament.initial_amount - filament.remaining_amount
    context = {
        'filament': filament,
        'usage_count': usage_count,
        'consumed_amount': consumed_amount,
        'next': next_url,
    }
    return render(request, 'calculator/confirm_delete_filament.html', context)


def assign_project_to_filament(request, filament_id):
    filament = get_object_or_404(Filament, pk=filament_id)
    if request.method == 'POST':
        form = FilamentUsageForm(request.POST, filament=filament)
        if form.is_valid():
            filament_usage = form.save(commit=False)
            filament_usage.filament = filament
            filament_usage.save()
            messages.success(
                request,
                f'مدل "{filament_usage.project.model_name}" به فیلامنت "{filament.name}" اختصاص داده شد'
            )
            return redirect('calculator:view_filament', pk=filament.pk)
    else:
        form = FilamentUsageForm(filament=filament)
    return render(request, 'calculator/assign_project.html', {'form': form, 'filament': filament})


def delete_filament_usage(request, pk):
    filament_usage = get_object_or_404(FilamentUsage, pk=pk)
    filament = filament_usage.filament
    if request.method == 'POST':
        filament_usage.delete()
        messages.success(request, 'اختصاص مدل حذف شد و فیلامنت بازگردانده شد')
        return redirect('calculator:view_filament', pk=filament.pk)
    return render(request, 'calculator/confirm_delete_project.html', {
        'filament_usage': filament_usage,
        'filament': filament
    })


def projects(request):
    q = request.GET.get('q', '').strip()
    material = request.GET.get('material', '').strip()
    sort = request.GET.get('sort', '-created_date').strip()
    view_mode = request.GET.get('view', 'cards').strip()
    page = request.GET.get('page', 1)
    qs = Project.objects.all()
    if q:
        qs = qs.filter(
            Q(model_name__icontains=q) |
            Q(code__icontains=q)
        )
    allowed_sorts = {
        '-created_date', 'created_date',
        'code', '-code',
        'model_name', '-model_name',
        '-print_time_hours', 'print_time_hours',
    }
    if sort not in allowed_sorts:
        sort = '-created_date'
    qs = qs.order_by(sort)
    total_count = qs.count()
    paginator = Paginator(qs, 12 if view_mode == 'cards' else 25)
    page_obj = paginator.get_page(page)
    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'q': q,
        'material': material,
        'sort': sort,
        'view_mode': view_mode,
    }
    return render(request, 'calculator/projects.html', context)


def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'مدل جدید با کد {project.code} ثبت شد')
            return redirect('calculator:view_project', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'calculator/add_project.html', {'form': form})


def view_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    filament_usages = FilamentUsage.objects.filter(project=project).select_related('filament')
    sales = Sale.objects.filter(project=project).order_by('-sale_date')
    context = {
        'project': project,
        'filament_usages': filament_usages,
        'sales': sales,
    }
    return render(request, 'calculator/view_project.html', context)


def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save()
            for usage in FilamentUsage.objects.filter(project=project):
                costs = project.calculate_cost_with_filament(usage.filament)
                usage.filament_weight_used = costs['filament_weight']
                usage.material_cost = costs['material_cost']
                usage.electricity_cost = costs['electricity_cost']
                usage.depreciation_cost = costs['depreciation_cost']
                usage.post_processing_cost = costs['post_processing_cost']
                usage.painting_cost = costs['painting_cost']
                usage.total_cost = costs['total_cost']
                usage.selling_price = costs['selling_price']
                usage.save()
            messages.success(request, 'مدل بروزرسانی شد')
            return redirect('calculator:view_project', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'calculator/edit_project.html', {'form': form, 'project': project})


def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    usage_count = FilamentUsage.objects.filter(project=project).count()
    sales_count = Sale.objects.filter(project=project).count()
    
    if request.method == 'POST':
        project_name = project.model_name
        project_code = project.code
        
        # First delete all related FilamentUsages (and return filament to stock)
        usages = FilamentUsage.objects.filter(project=project)
        total_filament_returned = 0
        for usage in usages:
            total_filament_returned += usage.total_filament_used
        usages.delete()
        
        # Delete all related Sales
        Sale.objects.filter(project=project).delete()
        
        # Now delete the project
        project.delete()
        
        # Success message
        msg = f'پروژه "{project_name}" (کد {project_code}) با موفقیت حذف شد.'
        if usage_count > 0:
            msg += f' {usage_count} اختصاص فیلامنت حذف و {total_filament_returned:.1f} متر فیلامنت بازگردانده شد.'
        if sales_count > 0:
            msg += f' {sales_count} فروش مرتبط نیز حذف شد.'
        
        messages.success(request, msg)
        return redirect('calculator:projects')
    
    context = {
        'project': project,
        'usage_count': usage_count,
        'sales_count': sales_count,
    }
    return render(request, 'calculator/confirm_delete_project.html', context)


from django.db import transaction

def sales(request):
    if request.method == 'POST':
        data = request.POST.copy()
        posted_project_id = data.get('project')
        posted_project_code = (data.get('project_code') or '').strip()

        form = SaleForm(data)
        if form.is_valid():
            sale = form.save(commit=False)

            project_obj = None
            # try posted project id first
            if posted_project_id:
                try:
                    project_obj = Project.objects.get(pk=int(posted_project_id))
                except (ValueError, Project.DoesNotExist):
                    project_obj = None

            # fallback: resolve by project_code (code is integer field)
            if not project_obj and posted_project_code:
                try:
                    project_obj = Project.objects.get(code=int(posted_project_code))
                except (ValueError, Project.DoesNotExist):
                    project_obj = None

            if not project_obj:
                # attach error to form so it shows near fields
                form.add_error('project', 'محصول مشخص نشده یا کد نامعتبر است.')
                all_projects = Project.objects.all().order_by('-created_date')
                recent_sales = Sale.objects.select_related('project').order_by('-sale_date')[:10]
                return render(request, 'calculator/sales.html', {
                    'form': form, 'all_projects': all_projects, 'recent_sales': recent_sales
                })

            # save atomically to be safe
            with transaction.atomic():
                sale.project = project_obj
                # keep project_code in sync (overwrite or keep existing depending on policy)
                sale.project_code = project_obj.code
                # compute total in case form didn't
                sale.total_price = (sale.unit_price * sale.quantity) + (sale.packaging_cost or 0)
                sale.save()

            messages.success(request, f'فروش {sale.quantity} عدد محصول {project_obj.model_name} ثبت شد')
            return redirect('calculator:sales_history')
        else:
            messages.error(request, 'فرم معتبر نیست — لطفاً خطاها را بررسی کنید.')
            all_projects = Project.objects.all().order_by('-created_date')
            recent_sales = Sale.objects.select_related('project').order_by('-sale_date')[:10]
            return render(request, 'calculator/sales.html', {
                'form': form, 'all_projects': all_projects, 'recent_sales': recent_sales
            })

    # GET branch (unchanged)
    form = SaleForm()
    all_projects = Project.objects.all().order_by('-created_date')
    recent_sales = Sale.objects.select_related('project').order_by('-sale_date')[:10]
    return render(request, 'calculator/sales.html', {'form': form, 'all_projects': all_projects, 'recent_sales': recent_sales})




def sales_history(request):
    period = request.GET.get('period', 'all')
    search = request.GET.get('search', '').strip()
    customer = request.GET.get('customer', '').strip()
    sort = request.GET.get('sort', '-sale_date')
    page = request.GET.get('page', 1)

    sales_qs = Sale.objects.select_related('project').all()

    if period == 'today':
        date_filter = timezone.now().date()
        sales_qs = sales_qs.filter(sale_date__date=date_filter)
        period_name = "امروز"
    elif period == 'week':
        date_filter = timezone.now() - timedelta(days=7)
        sales_qs = sales_qs.filter(sale_date__gte=date_filter)
        period_name = "هفته گذشته"
    elif period == 'month':
        date_filter = timezone.now() - timedelta(days=30)
        sales_qs = sales_qs.filter(sale_date__gte=date_filter)
        period_name = "ماه گذشته"
    elif period == 'year':
        date_filter = timezone.now() - timedelta(days=365)
        sales_qs = sales_qs.filter(sale_date__gte=date_filter)
        period_name = "سال گذشته"
    else:
        period_name = "همه فروش‌ها"

    if search:
        sales_qs = sales_qs.filter(
            Q(project_code__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )

    if customer:
        sales_qs = sales_qs.filter(customer_name__icontains=customer)

    allowed_sorts = ['-sale_date', 'sale_date', '-total_price', 'total_price',
                     '-quantity', 'quantity', 'customer_name', '-customer_name']
    if sort in allowed_sorts:
        sales_qs = sales_qs.order_by(sort)
    else:
        sales_qs = sales_qs.order_by('-sale_date')

    paginator = Paginator(sales_qs, 20)
    page_obj = paginator.get_page(page)

    # Build set of project_code integers we need to resolve (when project FK missing)
    codes_to_fetch = set()
    sales_list = list(page_obj)  # materialize for safe iteration

    for sale in sales_list:
        sale._dbg = {
            'project_fk': getattr(sale, 'project_id', None),
            'project_code_raw': sale.project_code,
            'found_by': None,
            'project_repr': None,
            'picture_url': None,
        }
        if getattr(sale, 'project_id', None):
            # safe to attach the related Project because project_id exists and select_related used
            sale.project_obj = sale.project
            sale._dbg['found_by'] = 'fk'
            if getattr(sale.project, 'code', None) is not None:
                sale._dbg['project_repr'] = f'PK:{sale.project.pk} code:{sale.project.code}'
            if getattr(sale.project, 'picture', None):
                try:
                    sale._dbg['picture_url'] = sale.project.picture.url
                except Exception:
                    sale._dbg['picture_url'] = 'error-getting-url'
        else:
            # collect integer codes for batch lookup
            code_val = sale.project_code
            if code_val is not None:
                try:
                    codes_to_fetch.add(int(code_val))
                except Exception:
                    pass

    projects_map = {}
    if codes_to_fetch:
        qs_projects = Project.objects.filter(code__in=list(codes_to_fetch))
        for p in qs_projects:
            projects_map[p.code] = p

    # attach found projects to sales that were missing FK
    for sale in sales_list:
        if getattr(sale, 'project_obj', None):
            continue
        code_val = sale.project_code
        if code_val is not None and int(code_val) in projects_map:
            p = projects_map[int(code_val)]
            sale.project_obj = p
            sale._dbg['found_by'] = 'code_lookup'
            sale._dbg['project_repr'] = f'PK:{p.pk} code:{p.code}'
            try:
                sale._dbg['picture_url'] = p.picture.url if getattr(p, 'picture', None) else None
            except Exception:
                sale._dbg['picture_url'] = 'error-getting-url'
        else:
            sale.project_obj = None
            sale._dbg['found_by'] = 'not_found'

    # optional logging for debugging
    missing = [s for s in sales_list if s._dbg.get('found_by') == 'not_found']
    if missing:
        logger.debug("sales_history: %d missing projects on current page example: %s",
                     len(missing), [(s.pk, s.project_code) for s in missing[:10]])

    # preserve current querystring (without page) for pagination links
    current_query = request.GET.copy()
    current_query.pop('page', None)
    context = {
        'page_obj': page_obj,
        'period': period,
        'period_name': period_name,
        'search': search,
        'customer': customer,
        'sort': sort,
        'customers': (Sale.objects.exclude(customer_name='').values_list('customer_name', flat=True).distinct().order_by('customer_name')),
        'total_sales': sales_qs.count(),
        'total_revenue': sales_qs.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'total_quantity': sales_qs.aggregate(Sum('quantity'))['quantity__sum'] or 0,
        'current_querystring': current_query.urlencode(),
    }
    if settings.DEBUG:
        context['DEBUG_SALES_LIST'] = [(s.pk, s.project_code, s._dbg) for s in sales_list[:50]]
    return render(request, 'calculator/sales_history.html', context)


def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'فروش حذف شد')
        return redirect('calculator:sales_history')
    return render(request, 'calculator/confirm_delete_sale.html', {'sale': sale})


def reports(request):
    """Generate sales and profit reports"""
    period = request.GET.get('period', 'month')
    item_filter = request.GET.get('item_filter', '')
    
    # Date filtering
    if period == 'week':
        date_filter = timezone.now() - timedelta(days=7)
        period_name = "هفته گذشته"
    elif period == 'month':
        date_filter = timezone.now() - timedelta(days=30)
        period_name = "ماه گذشته"
    elif period == 'year':
        date_filter = timezone.now() - timedelta(days=365)
        period_name = "سال گذشته"
    else:
        date_filter = None
        period_name = "همه زمان‌ها"
    
    # Base queryset
    sales_qs = Sale.objects.all()
    if date_filter:
        sales_qs = sales_qs.filter(sale_date__gte=date_filter)
    if item_filter:
        sales_qs = sales_qs.filter(project_code__icontains=item_filter)
    
    sales_data = list(sales_qs.all())
    
    # Attach project objects AND Jalali dates
    project_codes = [sale.project_code for sale in sales_data]
    projects_dict = {p.code: p for p in Project.objects.filter(code__in=project_codes)}
    
    # Convert dates to Jalali
    try:
        import jdatetime
        use_jalali = True
    except ImportError:
        use_jalali = False
    
    for sale in sales_data:
        sale.project_obj = projects_dict.get(sale.project_code)
        
        if use_jalali:
            try:
                j_dt = jdatetime.datetime.fromgregorian(datetime=sale.sale_date)
                sale.display_date = f"{j_dt.year}/{j_dt.month:02d}/{j_dt.day:02d}"
                sale.display_time = f"{j_dt.hour:02d}:{j_dt.minute:02d}"
            except Exception:
                sale.display_date = sale.sale_date.strftime('%Y/%m/%d')
                sale.display_time = sale.sale_date.strftime('%H:%M')
        else:
            sale.display_date = sale.sale_date.strftime('%Y/%m/%d')
            sale.display_time = sale.sale_date.strftime('%H:%M')
    
    # Statistics
    total_sales = len(sales_data)
    total_revenue = sum(sale.total_price for sale in sales_data)
    total_packaging_cost = sum(sale.packaging_cost for sale in sales_data)
    
    # Top products - UPDATED to include project objects
    top_products_raw = (sales_qs.values('project_code')
                       .annotate(
                           count=Count('id'), 
                           revenue=Sum('total_price'),
                           total_quantity=Sum('quantity')
                       )
                       .order_by('-count')[:10])
    
    # Fetch all top product codes and get their project objects
    top_product_codes = [p['project_code'] for p in top_products_raw]
    top_projects_dict = {p.code: p for p in Project.objects.filter(code__in=top_product_codes)}
    
    # Build top_products with full project data
    top_products = []
    for product in top_products_raw:
        project_obj = top_projects_dict.get(product['project_code'])
        top_products.append({
            'project_code': product['project_code'],
            'name': project_obj.model_name if project_obj else f"کد {product['project_code']}",
            'count': product['count'],
            'revenue': product['revenue'],
            'total_quantity': product.get('total_quantity', 0),
            'project': project_obj,  # Full project object with image
        })
    
    # Daily stats
    daily_stats_raw = (sales_qs.extra({'date': "date(sale_date)"})
                      .values('date')
                      .annotate(
                          count=Count('id'), 
                          revenue=Sum('total_price'),
                          total_quantity=Sum('quantity')
                      )
                      .order_by('-date')[:30])
    
    # Convert daily stats
    daily_stats = []
    for day in daily_stats_raw:
        if use_jalali:
            try:
                from datetime import datetime as dt
                if isinstance(day['date'], str):
                    date_obj = dt.strptime(day['date'], '%Y-%m-%d').date()
                else:
                    date_obj = day['date']
                
                j_dt = jdatetime.date.fromgregorian(date=date_obj)
                jalali_display = f"{j_dt.month:02d}/{j_dt.day:02d}"
            except Exception:
                jalali_display = str(day['date'])[5:]
        else:
            jalali_display = str(day['date'])[5:]
        
        daily_stats.append({
            'date_display': jalali_display,
            'count': day['count'],
            'revenue': day['revenue'],
        })
    
    context = {
        'sales_data': sales_data,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_packaging_cost': total_packaging_cost,
        'top_products': top_products,
        'daily_stats': daily_stats,
        'period': period,
        'period_name': period_name,
        'item_filter': item_filter,
    }
    return render(request, 'calculator/reports.html', context)


@require_http_methods(["GET", "POST"])
def pricing_settings_view(request):
    settings_obj = PricingSettings.get_solo()
    if request.method == 'POST':
        storage = messages.get_messages(request)
        for _ in storage:
            pass
        form = PricingSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات با موفقیت ذخیره شد.')
            return redirect(reverse('calculator:pricing_settings') + f'?updated={timezone.now().timestamp()}')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PricingSettingsForm(instance=settings_obj)
    return render(request, 'calculator/pricing_settings.html', {
        'form': form,
        'settings_obj': settings_obj,
    })


def pricing_settings_json(request):
    s = PricingSettings.get_solo()
    return JsonResponse({
        'power_price_per_kwh': float(s.power_price_per_kwh),
        'depreciation_per_hour': float(s.depreciation_per_hour),
        'filament_waste_percent': float(s.filament_waste_percent),
        'packaging_cost': float(s.packaging_cost),
        'post_processing_rate': float(s.post_processing_rate),
        'painting_rate_per_cm2': float(s.painting_rate_per_cm2),
        'profit_percent': float(s.profit_percent),
        'round_to_nearest': float(s.round_to_nearest),
        'updated_at': s.updated_at.isoformat(),
    })


def _D(val, default='0'):
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


@require_POST
def calculate_preview(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'ورودی نامعتبر است'}, status=400)

    s = PricingSettings.get_solo()
    filament_used_mm = _D(data.get('filament_used_mm'))
    print_time_hours = _D(data.get('print_time_hours'))
    size_x = _D(data.get('size_x'))
    size_y = _D(data.get('size_y'))
    size_z = _D(data.get('size_z'))
    filament_cost_per_kg = _D(data.get('filament_cost_per_kg'))
    post_processing_flag = bool(data.get('post_processing_enabled'))
    painting_flag = bool(data.get('painting_enabled'))

    packaging_cost = _D(
        data.get('packaging_cost'),
        default=str(s.packaging_cost)
    ) if data.get('packaging_cost') is not None else s.packaging_cost

    g_per_m = _D('3.0')
    filament_length_m = filament_used_mm / _D('1000')
    filament_weight_g = filament_length_m * g_per_m
    filament_weight_g *= (_D('1') + s.filament_waste_percent / _D('100'))

    material_cost = (filament_weight_g / _D('1000')) * filament_cost_per_kg
    average_watts = _D('120')
    electricity_cost = (average_watts * print_time_hours / _D('1000')) * s.power_price_per_kwh
    depreciation_cost = s.depreciation_per_hour * print_time_hours
    post_processing_cost = s.post_processing_rate if post_processing_flag else _D('0')
    surface_cm2 = (_D('2') * ((size_x * size_y) + (size_y * size_z) + (size_x * size_z))) / _D('100')
    painting_cost = (s.painting_rate_per_cm2 * surface_cm2) if painting_flag else _D('0')
    base_total = material_cost + electricity_cost + depreciation_cost + post_processing_cost + painting_cost + packaging_cost
    selling_price = base_total * (_D('1') + s.profit_percent / _D('100'))
    if s.round_to_nearest and s.round_to_nearest > 0:
        step = s.round_to_nearest
        selling_price = (selling_price / step).to_integral_value(rounding=ROUND_HALF_UP) * step

    return JsonResponse({
        'filament_weight': float(filament_weight_g),
        'material_cost': float(material_cost),
        'electricity_cost': float(electricity_cost),
        'depreciation_cost': float(depreciation_cost),
        'post_processing_cost': float(post_processing_cost),
        'painting_cost': float(painting_cost),
        'total_cost': float(base_total),
        'selling_price': float(selling_price),
        'g_per_m': float(g_per_m),
    })


def delete_all_filament_usages(request, filament_id):
    filament = get_object_or_404(Filament, pk=filament_id)
    if request.method == 'POST':
        usages = FilamentUsage.objects.filter(filament=filament)
        count = usages.count()
        total_filament_returned = 0
        for usage in usages:
            total_filament_returned += usage.total_filament_used
        usages.delete()
        messages.success(
            request,
            f'✅ {count} اختصاص مدل حذف شد و {total_filament_returned:.2f} متر فیلامنت به موجودی بازگردانده شد.'
        )
        return redirect('calculator:delete_filament', pk=filament_id)
    usages = FilamentUsage.objects.filter(filament=filament).select_related('project')
    total_filament = sum(usage.total_filament_used for usage in usages)
    context = {
        'filament': filament,
        'usages': usages,
        'usage_count': usages.count(),
        'total_filament': total_filament,
    }
    return render(request, 'calculator/confirm_delete_all_usages.html', context)
