from django import forms
from .models import Department, Position, Benefit
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['title', 'department', 'description']

class BenefitForm(forms.ModelForm):
    class Meta:
        model = Benefit
        fields = ['name', 'description', 'active']



