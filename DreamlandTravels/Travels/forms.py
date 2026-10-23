from django import forms
from django.contrib.auth.models import User
from .models import Package

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        email = cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return cleaned_data

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = [
            "package_name",
            "destination",
            "price",
            "days",
            "nights",
            "hotel",
            "bus",
            "image",
            "description",
            "day",
            "included",
            "category",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "day": forms.Textarea(attrs={"rows": 4}),
            "included": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Image is optional on edit - existing image is kept if a new one isn't uploaded.
        self.fields["image"].required = False
