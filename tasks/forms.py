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
