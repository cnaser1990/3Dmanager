# calculator/models.py
from django.db import models
from django.urls import reverse
from PIL import Image
import os
from decimal import Decimal, ROUND_HALF_UP

class Filament(models.Model):
    MATERIAL_CHOICES = [
        ('PLA', 'PLA - پلی لاکتیک اسید'),
        ('PLA+', 'PLA+ - پلی لاکتیک اسید بهبود یافته'),
        ('ABS', 'ABS - آکریلونیتریل بوتادین استایرن'),
        ('PETG', 'PETG - پلی اتیلن ترفتالات گلیکول'),
        ('TPU', 'TPU - ترموپلاستیک پولی یورتان'),
        ('WOOD', 'WOOD - چوبی'),
        ('METAL', 'METAL - فلزی'),
        ('CARBON', 'CARBON FIBER - کربن فایبر'),
    ]
    name = models.CharField(max_length=200, verbose_name='نام فیلامنت')
    color = models.CharField(max_length=7, default='6c757d', verbose_name='رنگ')
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, default='PLA+', verbose_name='نوع ماده')
    initial_amount = models.FloatField(verbose_name='مقدار اولیه (متر)')
    remaining_amount = models.FloatField(verbose_name='مقدار باقی‌مانده (متر)')
    cost_per_kg = models.FloatField(default=1500000, verbose_name='قیمت (تومان/کیلو)')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'فیلامنت'
        verbose_name_plural = 'فیلامنت‌ها'
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        if self.color:
            self.color = self.color.replace('#', '').strip().upper()
            if not self.color:
                self.color = '6c757d'
        else:
            self.color = '6c757d'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.color}"

    def get_absolute_url(self):
        return reverse('calculator:view_filament', kwargs={'pk': self.pk})

    @property
    def color_hex(self):
        return f"#{self.color}" if self.color and not self.color.startswith('#') else self.color

    @property
    def usage_percentage(self):
        if self.initial_amount > 0:
            return round((self.remaining_amount / self.initial_amount) * 100)
        return 0

    @property
    def remaining_value(self):
        return (self.remaining_amount * self.cost_per_kg / 330)


class Project(models.Model):
    model_name = models.CharField(max_length=200, verbose_name='نام مدل')
    code = models.PositiveIntegerField(unique=True, verbose_name='کد مدل')
    picture = models.ImageField(upload_to='project_images/', blank=True, null=True, verbose_name='تصویر مدل')
    filament_used_mm = models.FloatField(verbose_name='فیلامنت مصرفی (میلی‌متر)')
    print_time_hours = models.FloatField(verbose_name='زمان پرینت (ساعت)')
    size_x = models.FloatField(verbose_name='ابعاد X (میلی‌متر)')
    size_y = models.FloatField(verbose_name='ابعاد Y (میلی‌متر)')
    size_z = models.FloatField(verbose_name='ابعاد Z (میلی‌متر)')
    post_processing_enabled = models.BooleanField(default=False, verbose_name='پست‌پروسسینگ')
    painting_enabled = models.BooleanField(default=False, verbose_name='رنگ‌آمیزی')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'مدل'
        verbose_name_plural = 'مدل‌ها'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.code} - {self.model_name}"

    def save(self, *args, **kwargs):
        if not self.code:
            last_project = Project.objects.order_by('-code').first()
            self.code = (last_project.code + 1) if last_project else 1
        super().save(*args, **kwargs)
        if self.picture:
            self.resize_image()

    def resize_image(self):
        if self.picture:
            try:
                img = Image.open(self.picture.path)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                max_size = (800, 600)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(self.picture.path, optimize=True, quality=85)
            except Exception as e:
                print(f"Error resizing image: {e}")

    def delete(self, *args, **kwargs):
        if self.picture:
            if os.path.isfile(self.picture.path):
                os.remove(self.picture.path)
        super().delete(*args, **kwargs)

    @property
    def has_image(self):
        return bool(self.picture and hasattr(self.picture, 'url'))

    @property
    def filament_weight_grams(self):
        g_per_m = Decimal('3.0')
        filament_length_m = Decimal(str(self.filament_used_mm)) / Decimal('1000')
        return float(filament_length_m * g_per_m)

    def get_assigned_filaments(self):
        return self.filamentusage_set.select_related('filament').all()

    def calculate_cost_with_filament(self, filament):
        settings_obj = PricingSettings.get_solo()
        filament_weight_g = Decimal(str(self.filament_weight_grams))
        filament_weight_g *= (Decimal('1') + settings_obj.filament_waste_percent / Decimal('100'))
        price_per_gram = Decimal(str(filament.cost_per_kg)) / Decimal('1000')
        material_cost = float(filament_weight_g * price_per_gram)
        average_watts = Decimal('120')
        electricity_cost = float(
            (average_watts * Decimal(str(self.print_time_hours)) / Decimal('1000')) *
            settings_obj.power_price_per_kwh
        )
        depreciation_cost = float(
            settings_obj.depreciation_per_hour * Decimal(str(self.print_time_hours))
        )
        post_processing_cost = float(settings_obj.post_processing_rate) if self.post_processing_enabled else 0
        surface_cm2 = (
            Decimal('2') * (
                (Decimal(str(self.size_x)) * Decimal(str(self.size_y))) +
                (Decimal(str(self.size_y)) * Decimal(str(self.size_z))) +
                (Decimal(str(self.size_x)) * Decimal(str(self.size_z)))
            )
        ) / Decimal('100')
        painting_cost = float(settings_obj.painting_rate_per_cm2 * surface_cm2) if self.painting_enabled else 0
        total_cost = material_cost + electricity_cost + depreciation_cost + post_processing_cost + painting_cost
        selling_price = Decimal(str(total_cost)) * (Decimal('1') + settings_obj.profit_percent / Decimal('100'))
        if settings_obj.round_to_nearest and settings_obj.round_to_nearest > 0:
            step = settings_obj.round_to_nearest
            selling_price = (selling_price / step).to_integral_value(rounding=ROUND_HALF_UP) * step
        return {
            'filament_weight': float(filament_weight_g),
            'material_cost': material_cost,
            'electricity_cost': electricity_cost,
            'depreciation_cost': depreciation_cost,
            'post_processing_cost': post_processing_cost,
            'painting_cost': painting_cost,
            'total_cost': total_cost,
            'selling_price': float(selling_price),
        }


class FilamentUsage(models.Model):
    filament = models.ForeignKey(Filament, on_delete=models.CASCADE, verbose_name='فیلامنت')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='مدل')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد تولید')
    filament_weight_used = models.FloatField(verbose_name='وزن فیلامنت (گرم)')
    material_cost = models.FloatField(verbose_name='هزینه مواد')
    electricity_cost = models.FloatField(verbose_name='هزینه برق')
    depreciation_cost = models.FloatField(verbose_name='هزینه استهلاک')
    post_processing_cost = models.FloatField(default=0, verbose_name='هزینه پست‌پروسسینگ')
    painting_cost = models.FloatField(default=0, verbose_name='هزینه رنگ‌آمیزی')
    total_cost = models.FloatField(verbose_name='هزینه کل')
    selling_price = models.FloatField(verbose_name='قیمت فروش')
    assigned_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ اختصاص')

    class Meta:
        verbose_name = 'استفاده از فیلامنت'
        verbose_name_plural = 'استفاده‌های فیلامنت'
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.project.model_name} - {self.filament.name} ({self.quantity} عدد) - {self.assigned_date.strftime('%Y/%m/%d')}"

    def save(self, *args, **kwargs):
        if not self.pk:
            costs = self.project.calculate_cost_with_filament(self.filament)
            self.filament_weight_used = costs['filament_weight']
            self.material_cost = costs['material_cost']
            self.electricity_cost = costs['electricity_cost']
            self.depreciation_cost = costs['depreciation_cost']
            self.post_processing_cost = costs['post_processing_cost']
            self.painting_cost = costs['painting_cost']
            self.total_cost = costs['total_cost']
            self.selling_price = costs['selling_price']
            filament_used_m = (self.project.filament_used_mm / 1000) * self.quantity
            self.filament.remaining_amount -= filament_used_m
            self.filament.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        filament_used_m = (self.project.filament_used_mm / 1000) * self.quantity
        self.filament.remaining_amount += filament_used_m
        self.filament.save()
        super().delete(*args, **kwargs)

    @property
    def total_filament_used(self):
        return (self.project.filament_used_mm / 1000) * self.quantity

    @property
    def total_weight_used(self):
        return self.filament_weight_used * self.quantity

    @property
    def total_material_cost(self):
        return self.material_cost * self.quantity

    @property
    def total_electricity_cost(self):
        return self.electricity_cost * self.quantity

    @property
    def total_depreciation_cost(self):
        return self.depreciation_cost * self.quantity

    @property
    def total_post_processing_cost(self):
        return self.post_processing_cost * self.quantity

    @property
    def total_painting_cost(self):
        return self.painting_cost * self.quantity

    @property
    def total_all_costs(self):
        return self.total_cost * self.quantity

    @property
    def total_selling_price(self):
        return self.selling_price * self.quantity

    @property
    def profit(self):
        return self.selling_price - self.total_cost

    @property
    def total_profit(self):
        return self.profit * self.quantity


class Sale(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name='محصول'
    )
    project_code = models.PositiveIntegerField(verbose_name='کد مدل', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    customer_name = models.CharField(max_length=200, blank=True, verbose_name='نام مشتری')
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')
    unit_price = models.FloatField(verbose_name='قیمت واحد')
    packaging_cost = models.FloatField(default=0, verbose_name='هزینه بسته‌بندی')
    unit_cost = models.FloatField(default=0, verbose_name='هزینه تولید (واحد)')
    total_price = models.FloatField(verbose_name='قیمت کل')
    sale_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ فروش')
    notes = models.TextField(blank=True, verbose_name='یادداشت')

    class Meta:
        verbose_name = 'فروش'
        verbose_name_plural = 'فروش‌ها'
        ordering = ['-sale_date']

    def __str__(self):
        # safe: use project_id check to avoid RelatedObjectDoesNotExist
        proj_code = self.project_code or (self.project.code if getattr(self, 'project_id', None) else None)
        return f"فروش {proj_code or '—'} - {self.customer_name or 'ناشناس'} - {self.quantity} عدد"

    def save(self, *args, **kwargs):
        # Auto-fill project_code if possible (safe)
        if not self.project_code and getattr(self, 'project_id', None):
            try:
                self.project_code = self.project.code
            except Exception:
                # shouldn't happen, but fail gracefully
                pass
        # Compute total safely
        try:
            self.total_price = (self.unit_price * self.quantity) + (self.packaging_cost or 0)
        except Exception:
            self.total_price = 0
        super().save(*args, **kwargs)

    @property
    def unit_profit(self):
        # Prefer stored unit_cost only (avoid referencing nonexistent relations)
        base_cost = self.unit_cost or 0
        return (self.unit_price - base_cost)

    @property
    def total_profit(self):
        return self.unit_profit * self.quantity

    @property
    def sale_revenue(self):
        return self.unit_price * self.quantity


class PricingSettings(models.Model):
    singleton_id = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    power_price_per_kwh = models.DecimalField(max_digits=12, decimal_places=2, default=3500)
    depreciation_per_hour = models.DecimalField(max_digits=12, decimal_places=2, default=12000)
    filament_waste_percent = models.DecimalField(max_digits=6, decimal_places=2, default=3)
    packaging_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    post_processing_rate = models.DecimalField(max_digits=12, decimal_places=2, default=25000)
    painting_rate_per_cm2 = models.DecimalField(max_digits=12, decimal_places=2, default=180)
    profit_percent = models.DecimalField(max_digits=6, decimal_places=2, default=35)
    round_to_nearest = models.DecimalField(max_digits=12, decimal_places=0, default=1000)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.singleton_id = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(singleton_id=1)
        return obj

    def __str__(self):
        return "Pricing Settings"
