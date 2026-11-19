from django import forms
from .models import Message, Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = [
            "category",
            "priority",
            "anonymous",
            "attachment",
            "description",
        ]

        widgets = {
            "category": forms.Select(attrs={
                "class": "form-control"
            }),

            "priority": forms.Select(attrs={
                "class": "form-control"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe your issue..."
            }),

            "anonymous": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

            "attachment": forms.FileInput(attrs={
                "class": "form-control"
            }),
        }



class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["message"]
        widgets = {'message': forms.Textarea(attrs={
        'class': 'mdmchat-field',
        'rows': 1,
        'placeholder': 'Type a message...',
    })
}