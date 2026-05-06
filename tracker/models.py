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
        # -------- Food --------
        ('food', 'Food'),
        ('restaurants', 'Restaurants & Dining'),
        ('drinks', 'Drinks & Beverages'),

        # -------- Transport --------
        ('transport', 'Transport & Fuel'),
        ('vehicle', 'Vehicle Maintenance'),
        ('public_transport', 'Public Transport'),
        ('parking', 'Parking & Tolls'),

        # ------- Housing --------
        ('rent', 'Rent'),
        ('mortgage', 'Mortgage'),
        ('home_maintenance', 'Home Maintenance'),
        ('home_decor', 'Home Decor & Furniture'),

        # ------- Utilities --------
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('internet', 'Internet Cable'),
        ('phone', 'Phone & Data'),

        # ------- Health --------
        ('health', 'Health & Medical'),
        ('pharmacy', 'Pharmacy & Medicine'),
        ('gym', 'Gym & Fitness'),

        # --------- Personal Care ------------
        ('haircut', 'Haircuts & Grooming'),
        ('skincare', 'Skincare & Beauty'),

        # -------- Education & Skills --------------
        ('tuition',   'School Fees & Tuition'),
        ('courses',   'Courses & Certifications'),
        ('books',     'Books & Stationery'),
        ('workshops', 'Workshops & Training'),

        # --------- Shopping -----------------------
        ('clothing', 'Clothing & Shoes'),
        ('gadgets',  'Gadgets & Electronics'),
        ('shopping', 'General Shopping'),

        # --------- Entertainment -----------------------
        ('entertainment', 'Entertainment & Leisure'),
        ('streaming', 'Streaming & Subscriptions'),
        ('travel', 'Travel & Holidays'),

        # --------- Gifts & Donations ----------------------
        ('gifts', 'Gifts & Presents'),
        ('donations', 'Donations & Charity'),
        ('weddings', 'Weddings & Events'),

        # ------------ Fees & Taxes -------------------------
        ('taxes',     'Taxes'),
        ('insurance', 'Insurance'),
        
        # --------------- Income ---------------------
        ('salary', 'Salary & Wages'),
        ('business', 'Business Income'),
        ('freelance', 'Freelance & Side Hustle'),
        ('farm_sales', 'Farm Sales'),
        ('rental_income', 'Rental Income'),
        ('investment', 'Investment Returns'),

    # --------------- Other -------------------------- 
        ('savings', 'Savings'),
    ]

    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('allocated', 'Allocated Funds'),
        ('income', 'Income'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - UGX {self.amount}"

class Category(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    name       = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']

