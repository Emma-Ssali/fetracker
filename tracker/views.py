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
from .forms import CustomRegisterForm, TransactionForm
from datetime import datetime, date


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
