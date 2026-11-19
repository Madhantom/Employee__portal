from django.contrib import admin
from .models import Employee,Attendance,Leave,Payslip,Announcement,Message,Holiday,Event,Complaint,PushSubscription

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display=("employee_id","user","phone","joining_date",)
    search_fields=("employee_id","user__username",)
    readonly_fields=("employee_id","uuid")

admin.site.register(Attendance)
admin.site.register(Leave) 
admin.site.register(Payslip)
admin.site.register(Announcement)
admin.site.register(Message)
admin.site.register(Holiday)
admin.site.register(Event)
admin.site.register(Complaint)
admin.site.register(PushSubscription)
