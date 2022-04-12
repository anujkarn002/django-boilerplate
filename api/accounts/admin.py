from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Interest, Skill, User, UserProfile, VerificationCode


admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(Skill)
admin.site.register(Interest)
admin.site.register(VerificationCode)
