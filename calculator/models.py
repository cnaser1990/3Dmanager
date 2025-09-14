# models.py

from django.db import models
from django.urls import reverse
from PIL import Image
import math
import os


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
    color = models.CharField(max_length=100, verbose_name='رنگ')
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, default='PLA+', verbose_name='نوع ماده')
    initial_amount = models.FloatField(verbose_name='مقدار اولیه (متر)')
    remaining_amount = models.FloatField(verbose_name='مقدار باقی‌مانده (متر)')
    cost_per_kg = models.FloatField(default=1500000, verbose_name='قیمت (تومان/کیلو)')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'فیلامنت'
        verbose_name_plural = 'فیلامنت‌ها'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.name} - {self.color}"
    
    def get_absolute_url(self):
        return reverse('calculator:view_filament', kwargs={'pk': self.pk})
    
    @property
    def usage_percentage(self):
        if self.initial_amount > 0:
            return round((self.remaining_amount / self.initial_amount) * 100)
        return 0
    
    @property
    def remaining_value(self):
        return (self.remaining_amount * self.cost_per_kg / 330)


class Project(models.Model):
    filament = models.ForeignKey(Filament, on_delete=models.CASCADE, verbose_name='فیلامنت')
    model_name = models.CharField(max_length=200, verbose_name='نام مدل')
    code = models.PositiveIntegerField(unique=True, verbose_name='کد مدل')
    picture = models.ImageField(
        upload_to='project_images/',
        blank=True,
        null=True,
        verbose_name='تصویر مدل',
        help_text='تصویر محصول  (اختیاری)'
    )
    filament_used_mm = models.FloatField(verbose_name='فیلامنت مصرفی (میلی‌متر)')
    print_time_hours = models.FloatField(verbose_name='زمان پرینت (ساعت)')
    size_x = models.FloatField(verbose_name='ابعاد X (میلی‌متر)')
    size_y = models.FloatField(verbose_name='ابعاد Y (میلی‌متر)')
    size_z = models.FloatField(verbose_name='ابعاد Z (میلی‌متر)')
    filament_weight_used = models.FloatField(verbose_name='وزن فیلامنت (گرم)')
    electricity_cost = models.FloatField(verbose_name='هزینه برق')
    depreciation_cost = models.FloatField(verbose_name='هزینه استهلاک')
    
    # Optional services
    post_processing_enabled = models.BooleanField(default=False, verbose_name='پست‌پروسسینگ')
    post_processing_cost = models.FloatField(default=0, verbose_name='هزینه پست‌پروسسینگ')
    painting_enabled = models.BooleanField(default=False, verbose_name='رنگ‌آمیزی')
    painting_cost = models.FloatField(default=0, verbose_name='هزینه رنگ‌آمیزی')
    
    material_cost = models.FloatField(verbose_name='هزینه مواد')
    total_cost = models.FloatField(verbose_name='هزینه کل')
    selling_price = models.FloatField(verbose_name='قیمت فروش')
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
        
        # Calculate costs
        self.calculate_costs()
        super().save(*args, **kwargs)
        
        # Resize image after saving
        if self.picture:
            self.resize_image()
    
    def resize_image(self):
        """Resize uploaded image to optimize storage"""
        if self.picture:
            try:
                img = Image.open(self.picture.path)
                
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if too large
                max_size = (800, 600)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(self.picture.path, optimize=True, quality=85)
            except Exception as e:
                print(f"Error resizing image: {e}")
    
    def delete(self, *args, **kwargs):
        # Delete image file when project is deleted
        if self.picture:
            if os.path.isfile(self.picture.path):
                os.remove(self.picture.path)
        super().delete(*args, **kwargs)
    
    @property
    def has_image(self):
        return bool(self.picture and hasattr(self.picture, 'url'))
    
    def calculate_costs(self):
        from django.conf import settings
        
        # Calculate filament weight
        radius_mm = settings.DEFAULT_SETTINGS['filament_diameter'] / 2
        volume_mm3 = math.pi * (radius_mm ** 2) * self.filament_used_mm
        volume_cm3 = volume_mm3 / 1000
        self.filament_weight_used = volume_cm3 * settings.DEFAULT_SETTINGS['filament_density']
        
        # Calculate basic costs
        price_per_gram = self.filament.cost_per_kg / 1000
        self.material_cost = self.filament_weight_used * price_per_gram
        self.electricity_cost = (self.print_time_hours * 
                               settings.DEFAULT_SETTINGS['electricity_cost_per_kwh'] * 
                               settings.DEFAULT_SETTINGS['printer_power'])
        self.depreciation_cost = (self.print_time_hours * 
                                settings.DEFAULT_SETTINGS['printer_depreciation_per_hour'])
        
        # Calculate volume for painting
        volume_cm3 = (self.size_x/10) * (self.size_y/10) * (self.size_z/10)
        
        # Optional post-processing cost
        if self.post_processing_enabled:
            self.post_processing_cost = settings.DEFAULT_SETTINGS['post_processing_base_cost']
        else:
            self.post_processing_cost = 0
        
        # Optional painting cost
        if self.painting_enabled:
            self.painting_cost = volume_cm3 * settings.DEFAULT_SETTINGS['painting_cost_per_cm3']
        else:
            self.painting_cost = 0
        
        # Total cost (no packaging here)
        self.total_cost = (self.material_cost + self.electricity_cost + 
                          self.depreciation_cost + self.post_processing_cost + 
                          self.painting_cost)
        
        # Selling price
        self.selling_price = self.total_cost * (1 + settings.DEFAULT_SETTINGS['profit_margin'] / 100)
    
    @property
    def profit(self):
        return self.selling_price - self.total_cost


# models.py - Update the Sale model

class Sale(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='مدل')
    project_code = models.PositiveIntegerField(verbose_name='کد مدل')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    customer_name = models.CharField(max_length=200, blank=True, verbose_name='نام مشتری')
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')
    unit_price = models.FloatField(verbose_name='قیمت واحد')
    packaging_cost = models.FloatField(default=0, verbose_name='هزینه بسته‌بندی')
    total_price = models.FloatField(verbose_name='قیمت کل')
    sale_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ فروش')
    notes = models.TextField(blank=True, verbose_name='یادداشت')
    
    class Meta:
        verbose_name = 'فروش'
        verbose_name_plural = 'فروش‌ها'
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"فروش {self.project_code} - {self.customer_name or 'ناشناس'} - {self.quantity} عدد"
    
    def save(self, *args, **kwargs):
        if self.project:
            self.project_code = self.project.code
        
        # Calculate total price including packaging
        self.total_price = (self.unit_price * self.quantity) + self.packaging_cost
        super().save(*args, **kwargs)
    
    @property
    def unit_profit(self):
        if self.project:
            return self.unit_price - self.project.total_cost
        return 0
    
    @property
    def total_profit(self):
        # FIX: Packaging is not profit, only calculate profit from units sold
        return self.unit_profit * self.quantity
    
    @property
    def sale_revenue(self):
        # Revenue from actual sale (excluding packaging which is cost pass-through)
        return self.unit_price * self.quantity
    

class PricingSettings(models.Model):
    singleton_id = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)

    # Base costs
    power_price_per_kwh = models.DecimalField(max_digits=12, decimal_places=2, default=3500)  # Toman/kWh
    depreciation_per_hour = models.DecimalField(max_digits=12, decimal_places=2, default=12000)
    filament_waste_percent = models.DecimalField(max_digits=6, decimal_places=2, default=3)  # %
    packaging_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Services
    post_processing_rate = models.DecimalField(max_digits=12, decimal_places=2, default=25000)
    painting_rate_per_cm2 = models.DecimalField(max_digits=12, decimal_places=2, default=180)

    # Pricing strategy
    profit_percent = models.DecimalField(max_digits=6, decimal_places=2, default=35)  # %
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


# OPTIONAL: If you want per-spool accuracy, add these fields to your Filament model:
# class Filament(models.Model):
#     name = models.CharField(max_length=100)
#     material = models.CharField(max_length=50, blank=True, default='')
#     color = models.CharField(max_length=50, blank=True, default='')
#     cost_per_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     diameter_mm = models.DecimalField(max_digits=4, decimal_places=2, default=1.75)
#     density_g_cm3 = models.DecimalField(max_digits=4, decimal_places=2, default=1.24)  # PLA default
#     def __str__(self):
#         return f"{self.name} - {self.color} ({self.material})"