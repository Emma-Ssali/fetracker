from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Transaction, Category

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

        def __init__(self, *args, user=None, **kwargs):
            super().__init__(*args, **kwargs)
            if user:
                custom = [
                    (c.name.lower().replace(' ', '_'), c.name)
                    for c in Category.objects.filter(user=user)
                ]
                if custom:
                    all_choices = (
                        Transaction.CATEGORY_CHOICES +
                        [('── Your Custom Categories ──', []), ] +
                        custom
                    )
                else:
                    all_choices = Transaction.CATEGORY_CHOICES
                self.fields['category'].choices = all_choices

class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email']