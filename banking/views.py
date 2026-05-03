from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from .models import (
    User, KYCDocument, Transaction, Notification,
    CryptoWallet, CardOrderWallet, CardOrder, LoanApplication
)


def is_admin(user):
    return user.is_staff or user.is_superuser


def create_notification(user, title, message, notif_type='info'):
    Notification.objects.create(user=user, title=title, message=message, notification_type=notif_type)


def safe_decimal(val, default=0):
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(str(default))


# ─── Public ────────────────────────────────────────────────────────────────────

def homepage(request):
    return render(request, 'banking/homepage.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        data = request.POST
        username = data.get('user_id', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm = data.get('confirm_password', '')
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'banking/register.html', {'post': data})
        if User.objects.filter(username=username).exists():
            messages.error(request, 'User ID already taken.')
            return render(request, 'banking/register.html', {'post': data})
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'banking/register.html', {'post': data})
        user = User.objects.create_user(
            username=username, email=email, password=password,
            full_name=data.get('full_name',''), country=data.get('country',''),
            address=data.get('address',''), postal_code=data.get('postal_code',''),
            occupation=data.get('occupation',''), currency=data.get('currency','USD'),
            account_type=data.get('account_type','checking'), phone=data.get('phone',''),
        )
        user.user_id = username
        user.save()
        create_notification(user, 'Welcome to Co-operative Finance Bank!',
            f'Hello {user.full_name}, your account has been created. Account No: {user.account_number}', 'success')
        login(request, user)
        messages.success(request, 'Account created! Welcome to Co-operative Finance Bank.')
        return redirect('dashboard')
    return render(request, 'banking/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('user_id', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('admin_dashboard') if (user.is_staff or user.is_superuser) else redirect('dashboard')
        messages.error(request, 'Invalid User ID or Password.')
    return render(request, 'banking/login.html')


def logout_view(request):
    logout(request)
    return redirect('homepage')


# ─── User Dashboard ───────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    recent_txns = request.user.transactions.order_by('-created_at')[:5]
    unread_count = request.user.notifications.filter(is_read=False).count()
    return render(request, 'banking/dashboard.html', {
        'user': request.user, 'recent_txns': recent_txns, 'unread_count': unread_count,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        u = request.user
        section = request.POST.get('form_section', 'personal')
        if section == 'photo':
            if request.FILES.get('profile_image'):
                # Delete old image if exists
                if u.profile_image:
                    try:
                        import os
                        if os.path.isfile(u.profile_image.path):
                            os.remove(u.profile_image.path)
                    except Exception:
                        pass
                u.profile_image = request.FILES['profile_image']
                u.save()
                messages.success(request, 'Profile photo updated successfully.')
            else:
                messages.error(request, 'No image file selected.')
        else:
            u.full_name = request.POST.get('full_name', u.full_name)
            u.email = request.POST.get('email', u.email)
            u.phone = request.POST.get('phone', u.phone)
            u.address = request.POST.get('address', u.address)
            u.postal_code = request.POST.get('postal_code', u.postal_code)
            u.occupation = request.POST.get('occupation', u.occupation)
            u.country = request.POST.get('country', u.country)
            u.save()
            messages.success(request, 'Profile updated successfully.')
    return render(request, 'banking/profile.html', {'user': request.user})


@login_required
def transfer(request):
    if request.method == 'POST':
        amount = safe_decimal(request.POST.get('amount', '0'))
        user = request.user
        if amount <= 0:
            messages.error(request, 'Invalid amount.')
            return redirect('transfer')
        if amount > user.balance:
            messages.error(request, 'Insufficient balance.')
            return redirect('transfer')
        txn = Transaction.objects.create(
            user=user, transaction_type='transfer', amount=amount,
            currency=user.currency, status='pending',
            recipient_name=request.POST.get('recipient_name',''),
            recipient_bank=request.POST.get('recipient_bank',''),
            recipient_account=request.POST.get('recipient_account',''),
            recipient_iban=request.POST.get('recipient_iban',''),
            recipient_routing=request.POST.get('recipient_routing',''),
            recipient_country=request.POST.get('recipient_country',''),
            description=request.POST.get('description',''),
        )
        create_notification(user, 'Transfer Submitted',
            f'Your transfer of {user.get_currency_symbol()}{amount} to {txn.recipient_name} is pending approval.', 'info')
        messages.success(request, 'Transfer submitted. Awaiting admin approval.')
        return redirect('transactions')
    return render(request, 'banking/transfer.html', {'user': request.user})


@login_required
def transactions(request):
    txns = request.user.transactions.order_by('-created_at')
    return render(request, 'banking/transactions.html', {'txns': txns, 'user': request.user})


@login_required
def deposit(request):
    wallets = CryptoWallet.objects.filter(is_active=True)
    if request.method == 'POST':
        user = request.user
        txn = Transaction.objects.create(
            user=user, transaction_type='crypto_deposit',
            amount=safe_decimal(request.POST.get('amount_usd','0')),
            currency=user.currency, status='pending',
            crypto_type=request.POST.get('crypto_type',''),
            crypto_tx_hash=request.POST.get('tx_hash',''),
            description='Crypto Deposit',
        )
        create_notification(user, 'Deposit Submitted',
            f'Your crypto deposit is pending review. Reference: {txn.reference}', 'info')
        messages.success(request, 'Deposit submitted. Admin will review shortly.')
        return redirect('transactions')
    return render(request, 'banking/deposit.html', {'wallets': wallets, 'user': request.user})


@login_required
def kyc_upload(request):
    kyc_obj = KYCDocument.objects.filter(user=request.user).first()
    if request.method == 'POST':
        if kyc_obj:
            messages.warning(request, 'KYC already submitted.')
            return redirect('kyc')
        kyc_obj = KYCDocument(user=request.user, ssn=request.POST.get('ssn',''))
        if request.FILES.get('id_document'):
            kyc_obj.id_document = request.FILES['id_document']
        if request.FILES.get('address_proof'):
            kyc_obj.address_proof = request.FILES['address_proof']
        if request.FILES.get('selfie'):
            kyc_obj.selfie = request.FILES['selfie']
        kyc_obj.save()
        request.user.kyc_status = 'pending'
        request.user.save()
        create_notification(request.user, 'KYC Submitted', 'Your KYC documents are under review.', 'info')
        messages.success(request, 'KYC documents submitted successfully.')
        return redirect('dashboard')
    return render(request, 'banking/kyc.html', {'kyc': kyc_obj, 'user': request.user})


@login_required
def virtual_card(request):
    return render(request, 'banking/virtual_card.html', {'user': request.user})


@login_required
def card_order(request):
    wallets = CardOrderWallet.objects.filter(is_active=True)
    if request.method == 'POST':
        CardOrder.objects.create(
            user=request.user,
            payment_crypto=request.POST.get('crypto_type','BTC'),
            tx_hash=request.POST.get('tx_hash',''),
            delivery_address=request.POST.get('delivery_address',''),
        )
        create_notification(request.user, 'Card Order Submitted', 'Your physical card order is being processed.', 'info')
        messages.success(request, 'Card order submitted!')
        return redirect('dashboard')
    return render(request, 'banking/card_order.html', {'wallets': wallets, 'user': request.user})


@login_required
def loans(request):
    user_loans = request.user.loans.order_by('-created_at')
    if request.method == 'POST':
        d = request.POST
        loan = LoanApplication(
            user=request.user,
            # Personal
            full_name=d.get('full_name', request.user.full_name),
            date_of_birth=d.get('date_of_birth') or None,
            gender=d.get('gender',''),
            nationality=d.get('nationality',''),
            marital_status=d.get('marital_status',''),
            phone=d.get('phone', request.user.phone),
            email=d.get('email', request.user.email),
            residential_address=d.get('residential_address', request.user.address),
            city=d.get('city',''),
            state=d.get('state',''),
            country=d.get('country', request.user.country),
            postal_code=d.get('postal_code', request.user.postal_code),
            # Identity
            id_type=d.get('id_type',''),
            id_number=d.get('id_number',''),
            id_expiry=d.get('id_expiry') or None,
            # Employment
            employment_status=d.get('employment_status',''),
            employer_name=d.get('employer_name',''),
            employer_address=d.get('employer_address',''),
            job_title=d.get('job_title',''),
            years_employed=int(d.get('years_employed',0) or 0),
            monthly_income=safe_decimal(d.get('monthly_income','0')),
            # Financial
            other_income=safe_decimal(d.get('other_income','0')),
            monthly_expenses=safe_decimal(d.get('monthly_expenses','0')),
            has_existing_loans=d.get('has_existing_loans','') == 'yes',
            total_existing_debt=safe_decimal(d.get('total_existing_debt','0')),
            # Loan
            amount=safe_decimal(d.get('amount','0')),
            purpose=d.get('purpose','personal'),
            purpose_description=d.get('purpose_description',''),
            duration_months=int(d.get('duration_months',12) or 12),
            repayment_plan=d.get('repayment_plan','monthly'),
            # Credit
            credit_history=d.get('credit_history',''),
            consent_review=bool(d.get('consent_review')),
            consent_accurate=bool(d.get('consent_accurate')),
            # Next of Kin
            kin_full_name=d.get('kin_full_name',''),
            kin_relationship=d.get('kin_relationship',''),
            kin_phone=d.get('kin_phone',''),
            kin_address=d.get('kin_address',''),
        )
        if request.FILES.get('proof_of_income'):
            loan.proof_of_income = request.FILES['proof_of_income']
        if request.FILES.get('bank_statement'):
            loan.bank_statement = request.FILES['bank_statement']
        if request.FILES.get('utility_bill'):
            loan.utility_bill = request.FILES['utility_bill']
        loan.save()
        create_notification(request.user, 'Loan Application Submitted',
            f'Your loan application for {request.user.get_currency_symbol()}{loan.amount} has been submitted.', 'info')
        messages.success(request, 'Loan application submitted successfully.')
        return redirect('loans')
    return render(request, 'banking/loans.html', {'loans': user_loans, 'user': request.user})


@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'banking/notifications.html', {'notifs': notifs, 'user': request.user})


@login_required
def receipt(request, txn_id):
    txn = get_object_or_404(Transaction, id=txn_id, user=request.user)
    return render(request, 'banking/receipt.html', {'txn': txn, 'user': request.user})


@login_required
def mark_notification_read(request, notif_id):
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):
    users = User.objects.filter(is_staff=False, is_superuser=False)
    pending_kyc = KYCDocument.objects.filter(user__kyc_status='pending').count()
    pending_transfers = Transaction.objects.filter(transaction_type='transfer', status='pending').count()
    pending_deposits = Transaction.objects.filter(transaction_type='crypto_deposit', status='pending').count()
    pending_loans = LoanApplication.objects.filter(status='pending').count()
    total_balance = sum(u.balance for u in users)
    return render(request, 'banking/admin_dashboard.html', {
        'users': users, 'user_count': users.count(),
        'pending_kyc': pending_kyc, 'pending_transfers': pending_transfers,
        'pending_deposits': pending_deposits, 'pending_loans': pending_loans,
        'total_balance': total_balance,
    })


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_users(request):
    users = User.objects.filter(is_staff=False, is_superuser=False).order_by('-date_joined')
    return render(request, 'banking/admin_users.html', {'users': users})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_create_user(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('user_id','').strip()
        email = data.get('email','').strip()
        password = data.get('password','')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'User ID already taken.')
            return render(request, 'banking/admin_create_user.html', {'post': data})
        user = User.objects.create_user(
            username=username, email=email, password=password,
            full_name=data.get('full_name',''), country=data.get('country',''),
            address=data.get('address',''), postal_code=data.get('postal_code',''),
            occupation=data.get('occupation',''), currency=data.get('currency','USD'),
            account_type=data.get('account_type','checking'), phone=data.get('phone',''),
            balance=safe_decimal(data.get('balance','0')),
        )
        user.user_id = username
        user.save()
        create_notification(user, 'Account Created', f'Your account has been created. User ID: {username}', 'success')
        messages.success(request, f'User {username} created successfully.')
        return redirect('admin_users')
    return render(request, 'banking/admin_create_user.html')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_edit_user(request, user_id):
    edit_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        data = request.POST
        section = data.get('form_section', 'personal')

        if section == 'credentials':
            new_username = data.get('user_id', edit_user.username).strip()
            new_email = data.get('email', edit_user.email).strip()
            new_password = data.get('new_password', '').strip()
            confirm_password = data.get('confirm_password', '').strip()
            if new_username != edit_user.username and User.objects.filter(username=new_username).exists():
                messages.error(request, 'That User ID is already taken.')
                return redirect('admin_edit_user', user_id=user_id)
            if new_email != edit_user.email and User.objects.filter(email=new_email).exists():
                messages.error(request, 'That email is already registered to another account.')
                return redirect('admin_edit_user', user_id=user_id)
            if new_password and new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect('admin_edit_user', user_id=user_id)
            edit_user.username = new_username
            edit_user.user_id = new_username
            edit_user.email = new_email
            if new_password:
                edit_user.set_password(new_password)
            edit_user.save()
            create_notification(edit_user, 'Credentials Updated',
                'Your login credentials have been updated by admin.', 'warning')
            messages.success(request, f'Login credentials updated for {edit_user.username}.')

        elif section == 'personal':
            edit_user.full_name = data.get('full_name', edit_user.full_name)
            edit_user.phone = data.get('phone', edit_user.phone)
            edit_user.country = data.get('country', edit_user.country)
            edit_user.occupation = data.get('occupation', edit_user.occupation)
            edit_user.postal_code = data.get('postal_code', edit_user.postal_code)
            edit_user.address = data.get('address', edit_user.address)
            edit_user.save()
            messages.success(request, 'Personal details updated.')

        elif section == 'account':
            edit_user.currency = data.get('currency', edit_user.currency)
            edit_user.account_type = data.get('account_type', edit_user.account_type)
            edit_user.kyc_status = data.get('kyc_status', edit_user.kyc_status)
            edit_user.is_verified = (edit_user.kyc_status == 'approved')
            edit_user.balance = safe_decimal(data.get('balance', str(edit_user.balance)))
            edit_user.save()
            messages.success(request, 'Account settings updated.')

        return redirect('admin_edit_user', user_id=user_id)

    return render(request, 'banking/admin_edit_user.html', {'edit_user': edit_user})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted.')
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_add_funds(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        amount = safe_decimal(request.POST.get('amount','0'))
        action = request.POST.get('action','credit')
        desc = request.POST.get('description','')
        if action == 'credit':
            user.balance += amount
            txn_type = 'admin_credit'
            create_notification(user, 'Account Credited',
                f'{user.get_currency_symbol()}{amount} credited to your account.', 'success')
        else:
            if amount > user.balance:
                messages.error(request, 'Amount exceeds user balance.')
                return redirect('admin_edit_user', user_id=user_id)
            user.balance -= amount
            txn_type = 'admin_debit'
            create_notification(user, 'Account Debited',
                f'{user.get_currency_symbol()}{amount} debited from your account.', 'warning')
        user.save()
        Transaction.objects.create(
            user=user, transaction_type=txn_type, amount=amount,
            currency=user.currency, status='approved',
            description=f'Admin {action}: {desc}',
        )
        messages.success(request, f'Funds {action}ed successfully.')
    return redirect('admin_edit_user', user_id=user_id)


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_kyc(request):
    kycs = KYCDocument.objects.select_related('user').order_by('-submitted_at')
    return render(request, 'banking/admin_kyc.html', {'kycs': kycs})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_kyc_action(request, kyc_id, action):
    kyc = get_object_or_404(KYCDocument, id=kyc_id)
    if action == 'approve':
        kyc.user.kyc_status = 'approved'
        kyc.user.is_verified = True
        kyc.user.save()
        kyc.reviewed_at = timezone.now()
        kyc.admin_note = request.POST.get('note','')
        kyc.save()
        create_notification(kyc.user, 'KYC Approved', 'Your identity has been verified!', 'success')
        messages.success(request, 'KYC approved.')
    elif action == 'reject':
        kyc.user.kyc_status = 'rejected'
        kyc.user.save()
        kyc.reviewed_at = timezone.now()
        kyc.admin_note = request.POST.get('note','Documents not satisfactory.')
        kyc.save()
        create_notification(kyc.user, 'KYC Rejected', f'KYC rejected. {kyc.admin_note}', 'error')
        messages.warning(request, 'KYC rejected.')
    return redirect('admin_kyc')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_transfers(request):
    txns = Transaction.objects.filter(transaction_type='transfer').order_by('-created_at')
    return render(request, 'banking/admin_transfers.html', {'txns': txns})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_transfer_action(request, txn_id, action):
    txn = get_object_or_404(Transaction, id=txn_id, transaction_type='transfer')
    if action == 'approve' and txn.status == 'pending':
        if txn.amount > txn.user.balance:
            messages.error(request, 'User has insufficient balance.')
            return redirect('admin_transfers')
        txn.user.balance -= txn.amount
        txn.user.save()
        txn.status = 'approved'
        txn.admin_note = request.POST.get('note','')
        txn.save()
        create_notification(txn.user, 'Transfer Approved',
            f'Your transfer of {txn.user.get_currency_symbol()}{txn.amount} to {txn.recipient_name} was successful!', 'success')
        messages.success(request, 'Transfer approved.')
    elif action == 'reject' and txn.status == 'pending':
        txn.status = 'rejected'
        txn.admin_note = request.POST.get('note','Transfer rejected by admin.')
        txn.save()
        create_notification(txn.user, 'Transfer Rejected',
            f'Transfer of {txn.user.get_currency_symbol()}{txn.amount} rejected. {txn.admin_note}', 'error')
        messages.warning(request, 'Transfer rejected.')
    return redirect('admin_transfers')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_deposits(request):
    txns = Transaction.objects.filter(transaction_type='crypto_deposit').order_by('-created_at')
    return render(request, 'banking/admin_deposits.html', {'txns': txns})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_deposit_action(request, txn_id, action):
    txn = get_object_or_404(Transaction, id=txn_id, transaction_type='crypto_deposit')
    if action == 'approve' and txn.status == 'pending':
        txn.user.balance += txn.amount
        txn.user.save()
        txn.status = 'approved'
        txn.admin_note = request.POST.get('note','')
        txn.save()
        create_notification(txn.user, 'Deposit Approved',
            f'{txn.user.get_currency_symbol()}{txn.amount} credited to your account!', 'success')
        messages.success(request, 'Deposit approved and balance updated.')
    elif action == 'reject' and txn.status == 'pending':
        txn.status = 'rejected'
        txn.admin_note = request.POST.get('note','Deposit rejected.')
        txn.save()
        create_notification(txn.user, 'Deposit Rejected', f'Your deposit was rejected. {txn.admin_note}', 'error')
        messages.warning(request, 'Deposit rejected.')
    return redirect('admin_deposits')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_loans(request):
    loans = LoanApplication.objects.select_related('user').order_by('-created_at')
    return render(request, 'banking/admin_loans.html', {'loans': loans})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_loan_action(request, loan_id, action):
    loan = get_object_or_404(LoanApplication, id=loan_id)
    if action == 'approve' and loan.status == 'pending':
        loan.status = 'approved'
        loan.reviewed_at = timezone.now()
        loan.admin_note = request.POST.get('note','')
        loan.save()
        loan.user.balance += loan.amount
        loan.user.save()
        Transaction.objects.create(
            user=loan.user, transaction_type='loan_disbursement',
            amount=loan.amount, currency=loan.user.currency, status='approved',
            description=f'Loan disbursement — {loan.get_purpose_display()}',
        )
        create_notification(loan.user, 'Loan Approved',
            f'Your loan of {loan.user.get_currency_symbol()}{loan.amount} has been approved and credited!', 'success')
        messages.success(request, 'Loan approved and disbursed.')
    elif action == 'reject' and loan.status == 'pending':
        loan.status = 'rejected'
        loan.reviewed_at = timezone.now()
        loan.admin_note = request.POST.get('note','Loan rejected.')
        loan.save()
        create_notification(loan.user, 'Loan Rejected',
            f'Your loan application was rejected. {loan.admin_note}', 'error')
        messages.warning(request, 'Loan rejected.')
    return redirect('admin_loans')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_wallets(request):
    crypto_wallets = CryptoWallet.objects.all()
    card_wallets = CardOrderWallet.objects.all()
    if request.method == 'POST':
        wallet_type = request.POST.get('wallet_type','crypto')
        crypto_type = request.POST.get('crypto_type','')
        wallet_address = request.POST.get('wallet_address','')
        if wallet_type == 'crypto':
            CryptoWallet.objects.update_or_create(
                crypto_type=crypto_type, defaults={'wallet_address': wallet_address, 'is_active': True})
        else:
            CardOrderWallet.objects.update_or_create(
                crypto_type=crypto_type, defaults={'wallet_address': wallet_address, 'is_active': True})
        messages.success(request, 'Wallet updated.')
        return redirect('admin_wallets')
    return render(request, 'banking/admin_wallets.html', {
        'crypto_wallets': crypto_wallets, 'card_wallets': card_wallets,
    })


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_card_orders(request):
    orders = CardOrder.objects.select_related('user').order_by('-created_at')
    return render(request, 'banking/admin_card_orders.html', {'orders': orders})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_card_order_action(request, order_id, action):
    order = get_object_or_404(CardOrder, id=order_id)
    if action == 'approve':
        order.status = 'approved'
        order.admin_note = request.POST.get('note','')
        order.save()
        order.user.card_issued = True
        order.user.save()
        create_notification(order.user, 'Card Order Approved',
            'Your physical card has been approved and will be delivered soon!', 'success')
        messages.success(request, 'Card order approved.')
    elif action == 'reject':
        order.status = 'rejected'
        order.admin_note = request.POST.get('note','')
        order.save()
        create_notification(order.user, 'Card Order Rejected',
            f'Your card order was rejected. {order.admin_note}', 'error')
        messages.warning(request, 'Card order rejected.')
    return redirect('admin_card_orders')
