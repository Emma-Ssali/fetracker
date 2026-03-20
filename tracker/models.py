from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.username}"
    
class Transaction(models.Model):

    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('housing', 'Housing'),
        ('health', 'Health'),
        ('entertainment', 'Entertainment'),
        ('income', 'Income'),
        ('other', 'Other'),
    ]

    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('allocated', 'Allocated Funds'),
        ('income', 'Income'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - UGX {self.amount}"


