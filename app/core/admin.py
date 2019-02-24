# core/admin.py
from django.contrib import admin
# Import default user admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Import gettext for supporting multiple languages using translation engine
from django.utils.translation import gettext as _
# Import our models
from core import models


# Now create our custom user admin
class UserAdmin(BaseUserAdmin):
    # change the ordering we will set to the id of the object
    ordering = ['id']
    # Going to list them by email and name and order by id
    list_display = ['email', 'name']
    # Customize our user admin fieldsets. Reference Notion notes!
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (_('Important Dates'), {'fields': ('last_login',)})
    )
    # Configure add_fieldsets var to define fields in /add page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )


# Register our UserAdmin class to our User model
admin.site.register(models.User, UserAdmin)
# Register our Tag model
admin.site.register(models.Tag)
# Register our Ingredient model
admin.site.register(models.Ingredient)
