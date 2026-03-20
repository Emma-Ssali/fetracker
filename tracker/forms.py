from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Transaction

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='A verification token will be sent to this email.')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['description', 'amount', 'category', 'transaction_type', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }