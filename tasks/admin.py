from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Project, Task
from .forms import CustomUserLoginForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserLoginForm
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'country', 'avatar', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Особиста інформація', {'fields': ('first_name', 'last_name', 'phone_number', 'country', 'avatar', 'friends')}),  # Додано поле друзів
        ('Права', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Дати', {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'country', 'avatar', 'password1', 'password2', 'is_staff', 'is_active', 'friends')}  # Додано поле друзів
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Project)
admin.site.register(Task)