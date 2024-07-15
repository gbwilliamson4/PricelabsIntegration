from django.contrib import admin
from .models import Property, Property_Info, History, CalendarSyncInfo

admin.site.register(Property)
admin.site.register(Property_Info)
admin.site.register(History)
admin.site.register(CalendarSyncInfo)
