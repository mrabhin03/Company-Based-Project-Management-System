from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, EmployeeProfile
from company.models import Department, Position, Benefit
from datetime import date

class CustomUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['name','username', 'email', 'role', 'phone', 'password1', 'password2']

class ChangePassword(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [ 'password1', 'password2']

class UserFormEdit(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name','username', 'email', 'role', 'phone']


class EmpSelfEdit1(forms.ModelForm):
     class Meta:
        model = CustomUser
        fields = ['name','email', 'phone']
        
class EmpSelfEdit2(forms.ModelForm):
     class Meta:
        model = EmployeeProfile
        fields = ['skills']
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 5, 'placeholder': 'List your skills, certifications, or trainings'}),
        }


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ['skills','department', 'position', 'benefits', 'date_of_joining', 'salary']
        widgets = {
            'benefits': forms.CheckboxSelectMultiple(),
            'skills': forms.Textarea(attrs={'rows': 5, 'placeholder': 'List your skills, certifications, or trainings'}),
            'date_of_joining': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
        self.fields['position'].queryset = Position.objects.all()
        self.fields['benefits'].queryset = Benefit.objects.filter(active=True)

# Add this back — this is the missing part
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


from django import forms
from .models import Payroll

class PayrollForm(forms.ModelForm):
    month = forms.DateField(
        input_formats=['%Y-%m'], 
        widget=forms.DateInput(
            format='%Y-%m',
            attrs={'type': 'month'}
        )
    )
    class Meta:
        model = Payroll
        fields = ['base_salary', 'bonuses', 'deductions', 'month', 'is_paid']


MONTH_CHOICES = [(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)]
YEAR_CHOICES = [(y, y) for y in range(2020, date.today().year + 2)]  # adjust years as needed

class PayrollFilterForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    year = forms.ChoiceField(choices=YEAR_CHOICES)

class DepFilterForm(forms.Form):
    department = forms.ChoiceField(choices=[],widget=forms.Select(attrs={'onchange': 'this.form.submit();'})) 
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = Department.objects.all()
        DEPT_CHOICES = [(d.pk, d.name) for d in departments]

        DEPT_CHOICES.insert(0, ('0', 'All Departments')) 
        self.fields['department'].choices = DEPT_CHOICES
