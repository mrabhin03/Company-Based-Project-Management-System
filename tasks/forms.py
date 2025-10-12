# tasks/forms.py
from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['ticket', 'title', 'description','deadline',  'status','assigned_to']
        widgets = {
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
            'deadline': forms.DateInput(
                attrs={'type': 'date'}, 
                format='%Y-%m-%d'       
            )
        }


class TaskStatus(forms.Form):
    STATUS_CHOICES = [
    ('Main Tasks','Main Tasks'),
    ('All', 'All'),
    ('Assigned', 'Assigned'),
    ('In Progress', 'In Progress'),
    ('Submitted', 'Submitted'),
    ('Needs Revision', 'Needs Revision'),
    ('Approved', 'Approved'),
    ('Completed', 'Completed'),
    ]

    Status = forms.ChoiceField(choices=STATUS_CHOICES,widget=forms.Select(attrs={'onchange': 'this.form.submit();'}))

from .models import TaskAttachment

class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ['file']

from .models import TaskComment

class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['text', 'attachment']
class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']