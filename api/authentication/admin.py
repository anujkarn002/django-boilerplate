from django.contrib import admin

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin



class CustomThirdPartyAdmin(OutstandingTokenAdmin):
    # Read-only behavior defined below
    actions = []

    def get_readonly_fields(self, *args, **kwargs):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return True

    def has_change_permission(self, request, obj=None):
        return (
            request.method in ['GET', 'HEAD'] and  # noqa: W504
            super().has_change_permission(request, obj)
        )


admin.site.unregister(OutstandingToken)
admin.site.register(OutstandingToken, CustomThirdPartyAdmin)