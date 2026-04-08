from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Sum, Q
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import Transaction, EmailVerificationToken
from .forms import CustomRegisterForm, ProfileUpdateForm, TransactionForm
from datetime import datetime, date
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io
import csv


# Create your views here.
#------- REGISTER ----->
def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # block login until verified
            user.save()

            # generate and save token
            token = get_random_string(6)
            EmailVerificationToken.objects.create(user=user, token=token)

            # send email
            send_mail(
                subject='Verify your FETracker account',
                message=f'Your verification token is: {token}',
                from_email='noreply@fetracker.com',
                recipient_list=[user.email],
            )

            messages.info(request, 'Account created. Check your email for your verification token.')
            return redirect('verify_token')
    else:
        form = CustomRegisterForm()
    return render(request, 'tracker/register.html', {'form': form})

# <------- VERIFY TOKEN ------->
def verify_token(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        try:
            verification = EmailVerificationToken.objects.get(token=token)
            user = verification.user
            user.is_active = True  # activate the account
            user.save()
            verification.delete()  # token is used, remove it
            messages.success(request, 'Email verified! You can now log in.')
            return redirect('login')
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, 'Invalid token. Please try again.')
    return render(request, 'tracker/verify_token.html')

# <------- DASHBOARD ---------->
@login_required
def dashboard(request):

    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # ------- Search -------------------------
    search = request.GET.get('search', '').strip()
    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )

    # ------ Date filtering ------------------
    start_date = request.GET.get('start_date', '').strip()
    end_date   = request.GET.get('end_date', '').strip()
    month      = request.GET.get('month', '').strip()

    # Apply filters
    if month:
        try:
            parsed = datetime.strptime(month, '%Y-%m')
            transactions = transactions.filter(
                date__year=parsed.year,
                date__month=parsed.month
            )
        except ValueError:
            pass
    elif start_date and end_date:
        transactions = transactions.filter(
            date__gte=start_date,
            date__lte=end_date
        )
    elif start_date:
        transactions = transactions.filter(date__gte=start_date)
    elif end_date:
        transactions = transactions.filter(date__lte=end_date)
        
    # -------calculate totals first ---------- 
    total_income = transactions.filter(transaction_type='income').aggregate(
        Sum('amount'))['amount__sum'] or 0
    total_allocated = transactions.filter(
        transaction_type='allocated').aggregate(
        Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(transaction_type='expense').aggregate(
        Sum('amount'))['amount__sum'] or 0
    remaining_allocated = total_allocated - total_expenses

    #Step 3 — category breakdown        ← ADD THIS BLOCK HERE
    category_breakdown = (
        transactions
        .filter(transaction_type='expense')
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    # Pagination — 10 transactions per page
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_allocated': total_allocated,
        'total_expenses': total_expenses,
        'remaining_allocated': remaining_allocated,
        'category_breakdown': category_breakdown,
        'start_date':         start_date or '',
        'end_date':           end_date or '',
        'month':              month or '',
        'search':             search or '',
    }
    return render(request, 'tracker/dashboard.html', context)

# -------- TRANSACTION FORM ----------
@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user  # link to logged-in user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm()
    return render(request, 'tracker/add_transaction.html', {'form': form})

# -------- DELETE ------------
@login_required
def delete_transaction(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id, user=request.user)
    transaction.delete()
    messages.success(request, 'Transaction deleted successfully!')
    return redirect('dashboard')

# -------- EDIT ----------------
@login_required
def edit_transaction(request, transaction_id):
    transaction = Transaction.objects.get(
        id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm(instance=transaction)
    
    return render(request, 'tracker/edit_transaction.html', {
        'form': form,
        'transaction': transaction
    })

# ----------- ALLOCATED FUNDS ----------------
@login_required
def allocated_funds(request):
    search = request.GET.get('search', '').strip()
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='allocated'
    ).order_by('-date')

    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )

    total_allocated = transactions.aggregate(
        Sum('amount'))['amount__sum'] or 0

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'tracker/allocated_funds.html', {
        'transactions': transactions,
        'total_allocated': total_allocated,
        'search': search,
    })

# --------------- EXPENSES --------------------
@login_required
def expenses(request):
    search = request.GET.get('search', '').strip()
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense'
    ).order_by('-date')

    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )

    total_expenses = transactions.aggregate(
        Sum('amount'))['amount__sum'] or 0

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'tracker/expenses.html', {
        'transactions': transactions,
        'total_expenses': total_expenses,
        'search': search,
    })

# ------- LOGOUT ---------
def custom_logout(request):
    auth_logout(request)
    return redirect('login')

# ------- LOGIN ----------
def income(request):
    search = request.GET.get('search', '').strip()
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='income'
    ).order_by('-date')

    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )

    total_income = transactions.aggregate(
        Sum('amount'))['amount__sum'] or 0

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'tracker/income.html', {
        'transactions': transactions,
        'total_income': total_income,
        'search': search,
    })

# ----------- EXPORT CSV ----------------
@login_required
def export_csv(request):
    # Get filters from URL parameters to export filtered data
    search = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    month = request.GET.get('month', '').strip()

    # Apply filters to the transactions queryset
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )
    if month:
        try:
            year , mon = month.split('-')
            transactions = transactions.filter(
                date__year=int(year), date__month=int(mon))
        except ValueError:
            pass

    elif start_date and end_date:
        transactions = transactions.filter(
            date__gte=start_date, date__lte=end_date)
    elif start_date:
        transactions = transactions.filter(date__gte=start_date)
    elif end_date:
        transactions = transactions.filter(date__lte=end_date)
    
    # Create the HTTP response with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fetracker_transactions.csv"'

    writer = csv.writer(response)

    # Write header row
    writer.writerow([
        'Date', 'Description', 'Category', 'Type', 'Amount (UGX)'
    ])

    # Write data rows
    for t in transactions:
        writer.writerow([
            t.date,
            t.description,
            t.get_category_display(),
            t.get_transaction_type_display(),
            t.amount,
        ])

    return response

@login_required
def export_pdf(request):
    # Get filters
    search = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    month = request.GET.get('month', '').strip()

    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # apply same filters
    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )
    if month:
        try:
            year , mon = month.split('-')
            transactions = transactions.filter(
                date__year=int(year), date__month=int(mon))
        except ValueError:
            pass
    elif start_date and end_date:
        transactions = transactions.filter(
            date__gte=start_date, date__lte=end_date)
    elif start_date:
        transactions = transactions.filter(date__gte=start_date)
    elif end_date:
        transactions = transactions.filter(date__lte=end_date)

    # Calculate totals
    total_income = transactions.filter(
        transaction_type='income').aggregate(
        Sum('amount'))['amount__sum'] or 0
    total_allocated = transactions.filter(
        transaction_type='allocated').aggregate(
        Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(
        transaction_type='expense').aggregate(
        Sum('amount'))['amount__sum'] or 0
    remaining_allocated = total_allocated - total_expenses

    # Build PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    # --------- Title ---------
    title_style = styles['Title']
    elements.append(Paragraph('FETracker Transactions Report', title_style))
    elements.append(Paragraph(
        f"User: {request.user.username} | Generated on: {date.today().strftime('%Y-%m-%d')}", styles['Normal']
    ))
    elements.append(Spacer(1, 0.4*cm))

    # --------- Filter info ---------
    if month:
        elements.append(Paragraph(f"Filtered by Month: {month}", styles['Normal']))
    elif start_date and end_date:
        elements.append(Paragraph(f"Filtered by Date Range: {start_date} to {end_date}", styles['Normal']
        ))
    if search:
        elements.append(Paragraph(f"Search Term: {search}", styles['Normal']))

    elements.append(Spacer(1, 0.5*cm))

    # --------- Summary table ---------
    summary_data = [
        ['Summary', 'Amount (UGX)'],
        ['Total Income', f"{total_income:,.0f}"],
        ['Total Allocated Funds', f"{total_allocated:,.0f}"],
        ['Total Expenses', f"{total_expenses:,.0f}"],
        ['Remaining Allocated Funds', f"{remaining_allocated:,.0f}"],
    ]
    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING',     (0,0), (-1,-1), 6),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))    
    elements.append(summary_table)

    # --------- Build and return PDF ---------
    doc.build(elements)
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fetracker_report.pdf"'
    return response

# ----------- PASSWORD RESET -------------
def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            password_reset_form.save(
                request=request,
                use_https=False,
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
                from_email=None,
            )
            return redirect('password_reset_done_custom')
    else:
        password_reset_form = PasswordResetForm()
    return render(request, 'registration/password_reset_form.html', {'form': password_reset_form})

def password_reset_done_view(request):
    return render(request, 'registration/password_reset_done.html')

def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully!')
                return redirect('password_reset_complete_custom')
        else:
            form = SetPasswordForm(user)
        return render(request, 'registration/password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        return render(request, 'registration/password_reset_confirm.html', {'validlink': False})
    
def password_reset_complete_view(request):
    return render(request, 'registration/password_reset_complete.html')

# ----------- PROFILE VIEW -------------
@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    # Account stats
    total_transactions = Transaction.objects.filter(
        user=request.user).count()
    total_income = Transaction.objects.filter(
        user=request.user,
        transaction_type='income').aggregate(
        Sum('amount'))['amount__sum'] or 0
    total_expenses = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense').aggregate(
        Sum('amount'))['amount__sum'] or 0

    context = {
        'form': form,
        'total_transactions': total_transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'member_since': request.user.date_joined,
    }
    return render(request, 'tracker/profile.html', context)