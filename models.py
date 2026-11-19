from django.db import models
from django.contrib.auth.models import User
import uuid

from employee_portal import settings
class Employee(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=10,unique=True,editable=False,blank=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    date_of_birth=models.DateField(null=True,blank=True)
    father_name=models.CharField(max_length=100,blank=True)
    native_place=models.CharField(max_length=100,blank=True)
    photo=models.ImageField(upload_to="employees/",blank=True,null=True)
    joining_date = models.DateField()
    STATUS_CHOICES = [
        ("Active","Active"),
        ("Inactive","Inactive"),
    ]
    status=models.CharField(max_length=10,choices=STATUS_CHOICES,default="Active")
    casual_leave = models.DecimalField(max_digits=4,decimal_places=1,default=10)
    medical_leave = models.DecimalField(max_digits=4,decimal_places=1,default=4)
    half_day_used = models.IntegerField(default=0)
    permission_used = models.IntegerField(default=0)
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = Employee.objects.exclude(employee_id="").order_by("-id").first()
            if last_employee:
                last_number = int(last_employee.employee_id[1:])
                self.employee_id = f"E{last_number + 1}"
            else:
                self.employee_id = "E1015"

        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.employee_id} - {self.user.username}"

   
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.TimeField(auto_now_add=True)
    check_out = models.TimeField(blank=True, null=True)
    status=models.CharField(max_length=20,default="Present")
    def __str__(self):
        return f"{self.employee.employee_id} - {self.date}"


class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

class Leave(models.Model):
    LEAVE_TYPES = (
        ("CL", "Casual Leave"),
        ("ML", "Medical Leave"),
        ("HD", "Half Day"),
        ("PR", "Permission"),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=2,choices=LEAVE_TYPES,default="CL")
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField(null=True,blank=True)
    permission_from = models.TimeField(null=True,blank=True)
    permission_to = models.TimeField(null=True,blank=True)
    status = models.CharField(max_length=20,choices=[
            ("Pending", "Pending"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
        ],
        default="Pending"
    )
    def __str__(self):
        return self.employee.employee_id
    

class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.month} {self.year}"
    

class Announcement(models.Model):
    title=models.CharField(max_length=200)
    message=models.TextField()
    created_at=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    title = models.CharField(max_length=100, blank=True, default="")
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to="chat_attachments/", blank=True, null=True)
    attachment_type = models.CharField(max_length=10, blank=True, null=True)  # image / video / audio / file
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")

    def __str__(self):
        return self.title

class Holiday(models.Model):
    title = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ("IT", "IT Issue"),
        ("PAYROLL", "Payroll Issue"),
        ("LEAVE", "Leave Issue"),
        ("MANAGEMENT", "Management Issue"),
        ("INFRA", "Infrastructure Problem"),
        ("HARASSMENT", "Harassment"),
        ("DISCRIMINATION", "Discrimination"),
        ("OTHER", "Other"),
    ]
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    ]
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="complaints"
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    description = models.TextField()
    attachment = models.FileField(
        upload_to="complaints/",
        blank=True,
        null=True
    )
    anonymous = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN"
    )
    admin_reply = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.employee.employee_id} - {self.category}"



class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "endpoint")