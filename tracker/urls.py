from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-token/', views.verify_token, name='verify_token'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('delete-transaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('edit-transaction/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
]