from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'HR']

def is_manager(user):
    return user.is_authenticated and user.role == 'MANAGER'


def is_employee(user):
    return user.is_authenticated and user.role == 'EMPLOYEE'

# You can use them as decorators like this:
# @user_passes_test(is_admin)
def is_admin_or_manager(user):
    return user.is_authenticated and user.role in ['ADMIN', 'MANAGER']

is_admin_or_manager = user_passes_test(is_admin_or_manager, login_url='/users/login/')
is_employee = user_passes_test(is_employee, login_url='/users/login/')
manager_required = user_passes_test(is_manager, login_url='/users/login/')
admin_required = user_passes_test(is_admin, login_url='/users/login/')