# calculator/forms.py

from django import forms
from .models import Filament, PricingSettings, Project, Sale, FilamentUsage

class FilamentForm(forms.ModelForm):
    remaining_amount = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1'
        }),
        label='مقدار باقی‌مانده (متر)'
    )
    
    class Meta:
        model = Filament
        fields = ['name', 'color', 'material', 'initial_amount', 'cost_per_kg']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: SUNLU PLA+ Premium'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',  # HTML5 color picker
                'class': 'form-control color-picker-input',
                'value': '#6c757d'  # Default gray color
            }),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'initial_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'value': '330'
            }),
            'cost_per_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1500000'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial remaining_amount
        if self.instance.pk:
            self.fields['remaining_amount'].initial = self.instance.remaining_amount
        else:
            self.fields['remaining_amount'].initial = self.initial.get('initial_amount', 330)
        
        # If editing existing filament, set color value with # prefix
        if self.instance.pk and self.instance.color:
            color_value = self.instance.color
            # Ensure it has # prefix for color picker
            if not color_value.startswith('#'):
                color_value = f'#{color_value}'
            self.fields['color'].widget.attrs['value'] = color_value
    
    def clean_color(self):
        """Validate and clean color value"""
        color = self.cleaned_data.get('color', '').strip()
        
        # Remove # if present
        color = color.replace('#', '').upper()
        
        # Default color if empty
        if not color:
            return '6c757d'
        
        # Expand 3-char hex to 6-char (e.g., F00 -> FF0000)
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        
        # Validate length
        if len(color) != 6:
            raise forms.ValidationError('کد رنگ باید 6 کاراکتر باشد (مثال: FF5733)')
        
        # Validate hex characters
        try:
            int(color, 16)
        except ValueError:
            raise forms.ValidationError('کد رنگ نامعتبر است. فقط اعداد 0-9 و حروف A-F مجاز هستند')
        
        return color
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set remaining_amount
        if not instance.pk:
            instance.remaining_amount = instance.initial_amount
        else:
            instance.remaining_amount = self.cleaned_data.get('remaining_amount', instance.remaining_amount)
        
        if commit:
            instance.save()
        return instance



class ProjectForm(forms.ModelForm):
    """Form for creating independent projects"""
    print_hours = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control calc-input',
            'placeholder': '0',
            'min': '0'
        }),
        label='ساعت'
    )
    
    print_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control calc-input',
            'placeholder': '0',
            'min': '0',
            'max': '59'
        }),
        label='دقیقه'
    )
    
    class Meta:
        model = Project
        fields = ['model_name', 'picture', 'filament_used_mm', 
                 'size_x', 'size_y', 'size_z', 'post_processing_enabled', 'painting_enabled']
        widgets = {
            'model_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: گلدان، فیگور، قطعه یدکی'
            }),
            'picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'filament_used_mm': forms.NumberInput(attrs={
                'class': 'form-control calc-input',
                'step': '0.1',
                'placeholder': 'مثال: 15000'
            }),
            'size_x': forms.NumberInput(attrs={
                'class': 'form-control calc-input',
                'step': '0.1',
                'placeholder': 'طول'
            }),
            'size_y': forms.NumberInput(attrs={
                'class': 'form-control calc-input',
                'step': '0.1',
                'placeholder': 'عرض'
            }),
            'size_z': forms.NumberInput(attrs={
                'class': 'form-control calc-input',
                'step': '0.1',
                'placeholder': 'ارتفاع'
            }),
            'post_processing_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'post_processing_enabled'
            }),
            'painting_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'painting_enabled'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.pk and hasattr(self.instance, 'print_time_hours'):
            total_hours = float(self.instance.print_time_hours or 0)
            hours = int(total_hours)
            minutes = int((total_hours - hours) * 60)
            
            self.fields['print_hours'].initial = hours
            self.fields['print_minutes'].initial = minutes
    
    def clean(self):
        cleaned_data = super().clean()
        
        hours = cleaned_data.get('print_hours', 0) or 0
        minutes = cleaned_data.get('print_minutes', 0) or 0
        
        total_hours = hours + (minutes / 60.0)
        cleaned_data['print_time_hours'] = total_hours
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        hours = self.cleaned_data.get('print_hours', 0) or 0
        minutes = self.cleaned_data.get('print_minutes', 0) or 0
        instance.print_time_hours = hours + (minutes / 60.0)
        
        if commit:
            instance.save()
        return instance


class FilamentUsageForm(forms.ModelForm):
    """Form for assigning a project to a filament"""
    project_code = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد مدل را وارد کنید',
            'min': '1'
        }),
        label='کد مدل'
    )
    
    class Meta:
        model = FilamentUsage
        fields = ['project', 'quantity']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-select',
                'id': 'project-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1',
                'placeholder': 'تعداد'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.filament = kwargs.pop('filament', None)
        super().__init__(*args, **kwargs)
        
        # UPDATED: Don't filter out already assigned projects - allow multiple batches
        if self.filament:
            self.fields['project'].queryset = Project.objects.all().order_by('-created_date')
    
    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        project_code = cleaned_data.get('project_code')
        quantity = cleaned_data.get('quantity', 1)
        
        # Try to find project by code if provided
        if not project and project_code:
            try:
                project = Project.objects.get(code=project_code)
                cleaned_data['project'] = project
            except Project.DoesNotExist:
                raise forms.ValidationError('پروژه با این کد یافت نشد!')
        
        # Check if enough filament available for quantity
        if project and self.filament:
            filament_needed_m = (project.filament_used_mm / 1000) * quantity
            if filament_needed_m > self.filament.remaining_amount:
                raise forms.ValidationError(
                    f'فیلامنت کافی نیست! مورد نیاز: {filament_needed_m:.1f} متر ({quantity} عدد)، '
                    f'موجودی: {self.filament.remaining_amount:.1f} متر'
                )
        
        return cleaned_data


class SaleForm(forms.ModelForm):
    project_code = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد مدل',
            'min': '1'
        }),
        label='کد مدل'
    )
    
    filament_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
        label='شناسه فیلامنت'
    )
    
    class Meta:
        model = Sale
        fields = ['filament_usage', 'quantity', 'customer_name', 'customer_phone', 
                 'unit_price', 'packaging_cost', 'notes']
        widgets = {
            'filament_usage': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '1',
                'min': '1',
                'placeholder': '1'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09123456789'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'قیمت هر واحد'
            }),
            'packaging_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
                'step': '100'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات اضافی در مورد فروش...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        filament_usage = cleaned_data.get('filament_usage')
        project_code = cleaned_data.get('project_code')
        filament_id = cleaned_data.get('filament_id')
        
        if not filament_usage and project_code:
            try:
                # Find FilamentUsage by project code (and optionally filament)
                query = FilamentUsage.objects.filter(project__code=project_code)
                
                if filament_id:
                    query = query.filter(filament_id=filament_id)
                
                filament_usage = query.first()
                
                if not filament_usage:
                    raise forms.ValidationError('ترکیب پروژه و فیلامنت یافت نشد!')
                
                cleaned_data['filament_usage'] = filament_usage
            except FilamentUsage.DoesNotExist:
                raise forms.ValidationError('استفاده از فیلامنت یافت نشد!')
        
        return cleaned_data


class PricingSettingsForm(forms.ModelForm):
    class Meta:
        model = PricingSettings
        fields = [
            'power_price_per_kwh',
            'depreciation_per_hour',
            'filament_waste_percent',
            'packaging_cost',
            'post_processing_rate',
            'painting_rate_per_cm2',
            'profit_percent',
            'round_to_nearest',
        ]
        widgets = {
            'power_price_per_kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'depreciation_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'filament_waste_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'packaging_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'post_processing_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'painting_rate_per_cm2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'profit_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'round_to_nearest': forms.NumberInput(attrs={'class': 'form-control', 'step': '100', 'min': '1'}),
        }

    def clean_round_to_nearest(self):
        v = self.cleaned_data['round_to_nearest']
        if v and v < 1:
            raise forms.ValidationError('مقدار گرد کردن باید حداقل 1 باشد.')
        return v