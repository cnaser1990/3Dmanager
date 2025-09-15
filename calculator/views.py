# calculator/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
import json
import math
import json
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from math import pi
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from .models import PricingSettings
from .forms import PricingSettingsForm
from .models import Filament, Project, Sale
from .forms import FilamentForm, ProjectForm, SaleForm


def index(request):
    filaments = Filament.objects.all()
    recent_projects = Project.objects.select_related('filament').all()[:10]
    
    # Project statistics
    project_stats = Project.objects.aggregate(
        count=Count('id'),
        total_cost=Sum('total_cost'),
        total_selling=Sum('selling_price')
    )
    
    # Sales statistics for current month
    thirty_days_ago = timezone.now() - timedelta(days=30)
    sales_stats = Sale.objects.filter(sale_date__gte=thirty_days_ago).aggregate(
        count=Count('id'),
        total_revenue=Sum('total_price')  # Changed from 'sale_price' to 'total_price'
    )
    
    context = {
        'filaments': filaments,
        'recent_projects': recent_projects,
        'project_stats': project_stats,
        'sales_stats': sales_stats,
    }
    return render(request, 'calculator/index.html', context)

def add_filament(request):
    if request.method == 'POST':
        form = FilamentForm(request.POST)
        if form.is_valid():
            filament = form.save()
            messages.success(request, 'فیلامنت جدید با موفقیت اضافه شد')
            return redirect('calculator:index')
    else:
        form = FilamentForm()
    
    return render(request, 'calculator/add_filament.html', {'form': form})

def view_filament(request, pk):
    filament = get_object_or_404(Filament, pk=pk)
    projects = Project.objects.filter(filament=filament)

    # Calculate statistics from projects (aggregates may return None)
    stats = projects.aggregate(
        count=Count('id'),
        total_cost=Sum('total_cost'),
        total_selling=Sum('selling_price'),
        total_weight=Sum('filament_weight_used')
    )

    # Normalize None -> 0
    stats_count = stats.get('count') or 0
    stats_total_cost = float(stats.get('total_cost') or 0)
    stats_total_selling = float(stats.get('total_selling') or 0)
    stats_total_weight = float(stats.get('total_weight') or 0)

    # Profit and average profit
    profit = stats_total_selling - stats_total_cost
    avg_profit = (profit / stats_count) if stats_count else 0

    stats['count'] = stats_count
    stats['total_cost'] = stats_total_cost
    stats['total_selling'] = stats_total_selling
    stats['total_weight'] = stats_total_weight
    stats['profit'] = profit
    stats['avg_profit'] = avg_profit

    # Derived filament values (do NOT set attributes on model)
    try:
        cost_per_kg = float(filament.cost_per_kg or 0)
    except Exception:
        cost_per_kg = 0.0
    # 330 meters per kg (change if your value differs)
    cost_per_meter = (cost_per_kg / 330.0) if cost_per_kg else 0.0

    try:
        remaining_amount_m = float(getattr(filament, 'remaining_amount', 0) or 0)
    except Exception:
        remaining_amount_m = 0.0
    remaining_value = remaining_amount_m * cost_per_meter

    try:
        initial_amount_m = float(getattr(filament, 'initial_amount', 0) or 0)
    except Exception:
        initial_amount_m = 0.0
    if initial_amount_m > 0:
        usage_percentage = int(round((remaining_amount_m / initial_amount_m) * 100))
    else:
        usage_percentage = 0
    usage_percentage = max(0, min(100, usage_percentage))

    context = {
        'filament': filament,
        'projects': projects,
        'stats': stats,
        'cost_per_meter': cost_per_meter,
        'remaining_value': remaining_value,
        'usage_percentage': usage_percentage,
    }
    return render(request, 'calculator/view_filament.html', context)

def edit_filament(request, pk):
    filament = get_object_or_404(Filament, pk=pk)
    if request.method == 'POST':
        form = FilamentForm(request.POST, instance=filament)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات فیلامنت بروزرسانی شد')
            return redirect('calculator:view_filament', pk=filament.pk)
    else:
        form = FilamentForm(instance=filament)
    
    return render(request, 'calculator/edit_filament.html', {'form': form, 'filament': filament})

def delete_filament(request, pk):
    filament = get_object_or_404(Filament, pk=pk)
    project_count = Project.objects.filter(filament=filament).count()
    
    if project_count > 0:
        messages.error(request, f'نمی‌توان این فیلامنت را حذف کرد چون {project_count} مدل با آن انجام شده است')
    else:
        filament.delete()
        messages.success(request, 'فیلامنت حذف شد')
    
    return redirect('calculator:index')

def add_project(request, filament_id):
    filament = get_object_or_404(Filament, pk=filament_id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.filament = filament
            
            # Check if enough filament is available
            filament_used_m = project.filament_used_mm / 1000
            if filament_used_m > filament.remaining_amount:
                messages.error(request, f'فیلامنت کافی نیست! باقی‌مانده: {filament.remaining_amount:.1f} متر')
                return render(request, 'calculator/add_project.html', {'form': form, 'filament': filament})
            
            project.save()
            
            # Update filament remaining amount
            filament.remaining_amount -= filament_used_m
            filament.save()
            
            messages.success(request, f'مدل جدید با کد {project.code} ثبت شد')
            return redirect('calculator:view_filament', pk=filament.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'calculator/add_project.html', {'form': form, 'filament': filament})

def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    old_filament_used_mm = project.filament_used_mm
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            project.save()
            
            # Update filament amount
            filament_diff_m = (project.filament_used_mm - old_filament_used_mm) / 1000
            project.filament.remaining_amount -= filament_diff_m
            project.filament.save()
            
            messages.success(request, 'مدل بروزرسانی شد')
            return redirect('calculator:view_filament', pk=project.filament.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'calculator/edit_project.html', {'form': form, 'project': project})

def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    filament = project.filament
    
    # Return filament to stock
    filament_used_m = project.filament_used_mm / 1000
    filament.remaining_amount += filament_used_m
    filament.save()
    
    project.delete()
    messages.success(request, 'مدل حذف شد و فیلامنت بازگردانده شد')
    return redirect('calculator:view_filament', pk=filament.pk)

def sales(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            messages.success(request, f'فروش {sale.quantity} عدد محصول {sale.project.model_name} با کد {sale.project_code} ثبت شد')
            return redirect('calculator:sales')
    else:
        form = SaleForm()
    
    all_projects = Project.objects.select_related('filament').order_by('-created_date')
    recent_sales = Sale.objects.select_related('project__filament').all()[:20]
    
    context = {
        'form': form,
        'all_projects': all_projects,
        'recent_sales': recent_sales,
    }
    return render(request, 'calculator/sales.html', context)

def sales_history(request):
    # Get filter parameters
    period = request.GET.get('period', 'all')
    search = request.GET.get('search', '').strip()
    customer = request.GET.get('customer', '').strip()
    sort = request.GET.get('sort', '-sale_date')
    page = request.GET.get('page', 1)
    
    # Base queryset
    sales_qs = Sale.objects.select_related('project__filament').all()
    
    # Date filtering
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
    
    # Search filtering (project name, code, customer name)
    if search:
        sales_qs = sales_qs.filter(
            Q(project__model_name__icontains=search) |
            Q(project_code__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    
    # Customer filtering
    if customer:
        sales_qs = sales_qs.filter(customer_name__icontains=customer)
    
    # Sorting
    allowed_sorts = ['-sale_date', 'sale_date', '-total_price', 'total_price', 
                     '-quantity', 'quantity', 'customer_name', '-customer_name']
    if sort in allowed_sorts:
        sales_qs = sales_qs.order_by(sort)
    else:
        sales_qs = sales_qs.order_by('-sale_date')
    
    # Calculate statistics
    total_sales = sales_qs.count()
    total_revenue = sales_qs.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_quantity = sales_qs.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_profit = sum(sale.total_profit for sale in sales_qs)
    
    # Pagination
    paginator = Paginator(sales_qs, 20)
    page_obj = paginator.get_page(page)
    
    # Get unique customers for filter dropdown
    customers = (Sale.objects.exclude(customer_name='')
                .values_list('customer_name', flat=True)
                .distinct()
                .order_by('customer_name'))
    
    context = {
        'page_obj': page_obj,
        'period': period,
        'period_name': period_name,
        'search': search,
        'customer': customer,
        'sort': sort,
        'customers': customers,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_quantity': total_quantity,
        'total_profit': total_profit,
    }
    return render(request, 'calculator/sales_history.html', context)

def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'فروش حذف شد')
        return redirect('calculator:sales_history')
    return render(request, 'calculator/confirm_delete_sale.html', {'sale': sale})

def reports(request):
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
    sales_qs = Sale.objects.select_related('project__filament')
    if date_filter:
        sales_qs = sales_qs.filter(sale_date__gte=date_filter)
    if item_filter:
        sales_qs = sales_qs.filter(project__model_name__icontains=item_filter)
    
    sales_data = sales_qs.all()
    
    # Calculate statistics - Updated for new field names
    total_sales = sales_data.count()
    total_revenue = sum(sale.total_price for sale in sales_data)  # Updated field name
    total_production_cost = sum(sale.project.total_cost * sale.quantity for sale in sales_data if sale.project)  # Updated calculation
    total_packaging_cost = sum(sale.packaging_cost for sale in sales_data)  # New field
    total_cost = total_production_cost + total_packaging_cost
    total_profit = sum(sale.total_profit for sale in sales_data)  # Use model property
    
    # Top products - Updated field name
    top_products = (sales_qs.values('project__model_name')
                   .annotate(
                       count=Count('id'), 
                       revenue=Sum('total_price'),  # Updated field name
                       total_quantity=Sum('quantity')  # New aggregation
                   )
                   .order_by('-count')[:10])
    
    # Daily stats - Updated field name
    daily_stats = (sales_qs.extra({'date': "date(sale_date)"})
                  .values('date')
                  .annotate(
                      count=Count('id'), 
                      revenue=Sum('total_price'),  # Updated field name
                      total_quantity=Sum('quantity')  # New aggregation
                  )
                  .order_by('-date')[:30])
    
    context = {
        'sales_data': sales_data,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_production_cost': total_production_cost,
        'total_packaging_cost': total_packaging_cost,
        'total_profit': total_profit,
        'top_products': top_products,
        'daily_stats': daily_stats,
        'period': period,
        'period_name': period_name,
        'item_filter': item_filter,
    }
    return render(request, 'calculator/reports.html', context)

def _D(val, default='0'):
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)

# ---------- Pricing Settings UI (public) ----------
@require_http_methods(["GET", "POST"])
def pricing_settings_view(request):
    settings_obj = PricingSettings.get_solo()
    if request.method == 'POST':
        if request.POST.get('confirm_apply') != 'on':
            messages.error(request, 'برای ذخیره، تیک «تایید اعمال تغییرات» را بزنید.')
            form = PricingSettingsForm(request.POST, instance=settings_obj)
        else:
            form = PricingSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'تنظیمات با موفقیت ذخیره شد.')
                return redirect('calculator:pricing_settings')
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

def projects(request):
    q = request.GET.get('q', '').strip()
    material = request.GET.get('material', '').strip()
    filament_id = request.GET.get('filament', '').strip()
    sort = request.GET.get('sort', '-created_date').strip()
    view_mode = request.GET.get('view', 'cards').strip()
    page = request.GET.get('page', 1)

    # Base queryset
    qs = Project.objects.select_related('filament').all()

    # Search by model_name, code, filament name/color
    if q:
        qs = qs.filter(
            Q(model_name__icontains=q) |
            Q(code__icontains=q) |
            Q(filament__name__icontains=q) |
            Q(filament__color__icontains=q)
        )

    # Filter by material
    if material:
        qs = qs.filter(filament__material=material)

    # Filter by specific filament
    if filament_id:
        try:
            qs = qs.filter(filament__id=int(filament_id))
        except ValueError:
            pass

    # Sorting (allow only known fields)
    allowed_sorts = {
        '-created_date', 'created_date',
        '-selling_price', 'selling_price',
        '-print_time_hours', 'print_time_hours',
        'code', '-code',
        # profit is a property, not a DB field. To sort by profit, annotate.
        'profit', '-profit',
    }

    if sort not in allowed_sorts:
        sort = '-created_date'

    # Handle profit sorting by annotation: selling_price - total_cost
    if sort in ('profit', '-profit'):
        qs = qs.annotate(_profit=Decimal('0'))  # fallback if needed
        # Use expression: selling_price - total_cost
        from django.db.models import F, ExpressionWrapper, DecimalField
        qs = qs.annotate(
            profit_value=ExpressionWrapper(
                F('selling_price') - F('total_cost'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        qs = qs.order_by('profit_value' if sort == 'profit' else '-profit_value')
    else:
        qs = qs.order_by(sort)

    total_count = qs.count()

    # Pagination
    paginator = Paginator(qs, 12 if view_mode == 'cards' else 25)
    page_obj = paginator.get_page(page)

    # Materials and filaments data for filters
    materials = Filament.MATERIAL_CHOICES
    filaments = Filament.objects.all().order_by('name', 'color')

    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'q': q,
        'material': material,
        'filament_id': filament_id,
        'sort': sort,
        'view_mode': view_mode,
        'materials': materials,
        'filaments': filaments,
    }
    return render(request, 'calculator/projects.html', context)

@require_POST
def calculate_preview(request):
    """
    Expected JSON:
    {
      filament_used_mm: number,
      print_time_hours: number,
      size_x: number, size_y: number, size_z: number,
      filament_cost_per_kg: number,
      post_processing_enabled: bool,
      painting_enabled: bool,
      packaging_cost: number (optional)
      // optional:
      // filament_id: number  -> if you later add diameter/density per spool
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'ورودی نامعتبر است'}, status=400)

    s = PricingSettings.get_solo()

    # Parse inputs
    filament_used_mm      = _D(data.get('filament_used_mm'))
    print_time_hours      = _D(data.get('print_time_hours'))
    size_x                = _D(data.get('size_x'))
    size_y                = _D(data.get('size_y'))
    size_z                = _D(data.get('size_z'))
    filament_cost_per_kg  = _D(data.get('filament_cost_per_kg'))
    post_processing_flag  = bool(data.get('post_processing_enabled'))
    painting_flag         = bool(data.get('painting_enabled'))

    packaging_cost = _D(
        data.get('packaging_cost'),
        default=str(s.packaging_cost)
    ) if data.get('packaging_cost') is not None else s.packaging_cost

    # ----- Filament weight (fixed) -----
    # Use a robust default grams-per-meter for 1.75 mm filament
    # 1.75 mm PLA theoretical ~2.98 g/m; we use 3.0 g/m default for practicality.
    g_per_m = _D('3.0')

    # If you want to consider material density/diameter later, see Option B/C below.
    filament_length_m = filament_used_mm / _D('1000')
    filament_weight_g = filament_length_m * g_per_m

    # Apply waste % from settings
    filament_weight_g *= (_D('1') + s.filament_waste_percent / _D('100'))

    # ----- Costs -----
    material_cost     = (filament_weight_g / _D('1000')) * filament_cost_per_kg

    # Electricity: using a conservative default average power 120W
    average_watts     = _D('120')
    electricity_cost  = (average_watts * print_time_hours / _D('1000')) * s.power_price_per_kwh

    depreciation_cost = s.depreciation_per_hour * print_time_hours

    post_processing_cost = s.post_processing_rate if post_processing_flag else _D('0')

    # Surface area estimate in cm^2: 2(xy + yz + xz), inputs are mm so convert mm^2 -> cm^2 by /100
    surface_cm2 = (_D('2') * ((size_x * size_y) + (size_y * size_z) + (size_x * size_z))) / _D('100')
    painting_cost = (s.painting_rate_per_cm2 * surface_cm2) if painting_flag else _D('0')

    base_total = material_cost + electricity_cost + depreciation_cost + post_processing_cost + painting_cost + packaging_cost

    # Selling price with profit and rounding
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
        # Debug helpers
        'g_per_m': float(g_per_m),
    })