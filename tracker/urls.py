from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-token/', views.verify_token, name='verify_token'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('delete-transaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('edit-transaction/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('allocated-funds/', views.allocated_funds, name='allocated_funds'),
    path('expenses/', views.expenses, name='expenses'),
    path('logout/', views.custom_logout, name='logout'),
    path('income/', views.income, name='income'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('password-reset/',                          views.password_reset_request,     name='password_reset_custom'),
    path('password-reset/done/',                     views.password_reset_done_view,   name='password_reset_done_custom'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm_custom'),
    path('password-reset/complete/',                 views.password_reset_complete_view, name='password_reset_complete_custom'),
]