# tasks/forms.py
from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['ticket', 'title', 'description','deadline',  'status','assigned_to']
        widgets = {
            'assigned_employees': forms.CheckboxSelectMultiple(),
            'deadline': forms.DateInput(
                attrs={'type': 'date'}, 
                format='%Y-%m-%d'       
            )
        }

class TaskFormEdit(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['ticket', 'title', 'description','deadline','status']
        widgets = {
            'assigned_employees': forms.CheckboxSelectMultiple(),
            'deadline': forms.DateInput(
                attrs={'type': 'date'}, 
                format='%Y-%m-%d'       
            )
        }

class TaskStatus(forms.Form):
    STATUS_CHOICES = [
        ("0","All"),
        ('PENDING', 'PENDING'),
        ('IN_PROGRESS', 'IN_PROGRESS'),
        ('COMPLETED', 'COMPLETED'),
    ]

    Status = forms.ChoiceField(choices=STATUS_CHOICES,widget=forms.Select(attrs={'onchange': 'this.form.submit();'}))