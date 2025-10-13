# customer/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import Ticket

class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['name','username', 'email', 'password1', 'password2']
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_CUSTOMER
        if commit:
            user.save()
        return user
    
class CustomerForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['name', 'email']

class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'description']

class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']


from .models import TicketAttachment

class TicketAttachmentForm(forms.ModelForm):
    class Meta:
        model = TicketAttachment
        fields = ['file']

from django import forms
from .models import BugReport

class BugReportForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = ['title', 'description']

class BugReportStatusForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = ['status']