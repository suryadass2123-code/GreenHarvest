from django import forms
from .models import Category, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock', 'image', 'location', 'unit', 'is_available']
        widgets = {
            'category': forms.Select(attrs={'class':'form-select'}),
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'rows':5}),
            'price': forms.NumberInput(attrs={'class':'form-control', 'step':'0.01'}),
            'stock': forms.NumberInput(attrs={'class':'form-control', 'min':'0'}),
            'location': forms.TextInput(attrs={'class':'form-control'}),
            'unit': forms.TextInput(attrs={'class':'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'rows':4}),
        }
