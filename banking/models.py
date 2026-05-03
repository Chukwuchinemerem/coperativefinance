import uuid
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


def generate_account_number():
    return ''.join(random.choices(string.digits, k=10))

def generate_card_number():
    return ' '.join([''.join(random.choices(string.digits, k=4)) for _ in range(4)])

def generate_cvv():
    return ''.join(random.choices(string.digits, k=3))

def generate_routing():
    return ''.join(random.choices(string.digits, k=9))


CURRENCY_CHOICES = [('USD','US Dollar ($)'),('EUR','Euro (€)'),('GBP','British Pound (£)')]
ACCOUNT_TYPE_CHOICES = [('checking','Checking Account'),('savings','Savings Account')]
KYC_STATUS_CHOICES = [('pending','Pending'),('approved','Approved'),('rejected','Rejected'),('not_submitted','Not Submitted')]
TRANSACTION_STATUS_CHOICES = [('pending','Pending'),('approved','Approved'),('rejected','Rejected')]
TRANSACTION_TYPE_CHOICES = [
    ('transfer','Transfer'),('deposit','Deposit'),('crypto_deposit','Crypto Deposit'),
    ('card_order','Card Order'),('loan_disbursement','Loan Disbursement'),
    ('loan_repayment','Loan Repayment'),('admin_credit','Admin Credit'),('admin_debit','Admin Debit'),
]
CRYPTO_CHOICES = [('BTC','Bitcoin (BTC)'),('USDT_TRC20','USDT TRC20'),('ETH','Ethereum (ETH)'),('SOL','Solana (SOL)')]
LOAN_STATUS_CHOICES = [('pending','Pending'),('approved','Approved'),('rejected','Rejected'),('repaid','Repaid')]

EMPLOYMENT_STATUS_CHOICES = [
    ('employed','Employed'),('self_employed','Self-Employed'),
    ('business_owner','Business Owner'),('unemployed','Unemployed'),('retired','Retired'),
]
LOAN_PURPOSE_CHOICES = [
    ('personal','Personal'),('business','Business'),('education','Education'),
    ('car','Car / Vehicle'),('mortgage','Mortgage / Real Estate'),('medical','Medical'),
    ('travel','Travel'),('debt_consolidation','Debt Consolidation'),('other','Other'),
]
GENDER_CHOICES = [('male','Male'),('female','Female'),('other','Other / Prefer not to say')]
MARITAL_STATUS_CHOICES = [('single','Single'),('married','Married'),('divorced','Divorced'),('widowed','Widowed')]
ID_TYPE_CHOICES = [('passport','International Passport'),('national_id','National ID Card'),('drivers_license',"Driver's License")]
REPAYMENT_CHOICES = [('monthly','Monthly'),('bi_weekly','Bi-Weekly'),('weekly','Weekly')]


class User(AbstractUser):
    user_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='checking')
    account_number = models.CharField(max_length=20, unique=True, blank=True)
    routing_number = models.CharField(max_length=20, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='not_submitted')
    date_joined = models.DateTimeField(default=timezone.now)
    phone = models.CharField(max_length=30, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    card_number = models.CharField(max_length=25, blank=True)
    card_cvv = models.CharField(max_length=5, blank=True)
    card_expiry = models.CharField(max_length=10, blank=True)
    card_issued = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_account_number()
        if not self.routing_number:
            self.routing_number = generate_routing()
        if not self.card_number:
            self.card_number = generate_card_number()
            self.card_cvv = generate_cvv()
            import datetime
            exp = datetime.date.today() + datetime.timedelta(days=3*365)
            self.card_expiry = exp.strftime('%m/%y')
        super().save(*args, **kwargs)

    def get_currency_symbol(self):
        return {'USD':'$','EUR':'€','GBP':'£'}.get(self.currency,'$')

    def __str__(self):
        return f"{self.full_name or self.username} ({self.account_number})"


class KYCDocument(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    id_document = models.FileField(upload_to='kyc/id/', blank=True, null=True)
    address_proof = models.FileField(upload_to='kyc/address/', blank=True, null=True)
    selfie = models.FileField(upload_to='kyc/selfie/', blank=True, null=True)
    ssn = models.CharField(max_length=20, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    admin_note = models.TextField(blank=True)

    def __str__(self):
        return f"KYC - {self.user.username}"


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=50, unique=True, blank=True)
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_bank = models.CharField(max_length=200, blank=True)
    recipient_account = models.CharField(max_length=100, blank=True)
    recipient_iban = models.CharField(max_length=100, blank=True)
    recipient_routing = models.CharField(max_length=50, blank=True)
    recipient_country = models.CharField(max_length=100, blank=True)
    crypto_type = models.CharField(max_length=20, blank=True)
    crypto_tx_hash = models.CharField(max_length=200, blank=True)
    crypto_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    admin_note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'TXN' + ''.join(random.choices(string.digits + string.ascii_uppercase, k=12))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.user.username} - {self.amount}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    notification_type = models.CharField(max_length=30, default='info')

    class Meta:
        ordering = ['-created_at']


class CryptoWallet(models.Model):
    crypto_type = models.CharField(max_length=20, choices=CRYPTO_CHOICES, unique=True)
    wallet_address = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.crypto_type}: {self.wallet_address}"


class CardOrderWallet(models.Model):
    crypto_type = models.CharField(max_length=20, choices=CRYPTO_CHOICES, unique=True)
    wallet_address = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class CardOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='card_orders')
    payment_crypto = models.CharField(max_length=20, choices=CRYPTO_CHOICES)
    tx_hash = models.CharField(max_length=200, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    delivery_address = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    admin_note = models.TextField(blank=True)


class LoanApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')

    # 1. Personal Info
    full_name = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    residential_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # 2. Identity
    id_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    id_expiry = models.DateField(null=True, blank=True)

    # 3. Employment
    employment_status = models.CharField(max_length=30, choices=EMPLOYMENT_STATUS_CHOICES, blank=True)
    employer_name = models.CharField(max_length=200, blank=True)
    employer_address = models.TextField(blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    years_employed = models.PositiveIntegerField(null=True, blank=True)
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # 4. Financial Info
    other_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    monthly_expenses = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    has_existing_loans = models.BooleanField(default=False)
    total_existing_debt = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # 5. Loan Details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    purpose = models.CharField(max_length=50, choices=LOAN_PURPOSE_CHOICES, default='personal')
    purpose_description = models.TextField(blank=True)
    duration_months = models.IntegerField(default=12)
    repayment_plan = models.CharField(max_length=20, choices=REPAYMENT_CHOICES, default='monthly')

    # 6. Supporting Documents
    proof_of_income = models.FileField(upload_to='loans/income/', blank=True, null=True)
    bank_statement = models.FileField(upload_to='loans/statements/', blank=True, null=True)
    utility_bill = models.FileField(upload_to='loans/utility/', blank=True, null=True)

    # 8. Credit & Consent
    credit_history = models.TextField(blank=True)
    consent_review = models.BooleanField(default=False)
    consent_accurate = models.BooleanField(default=False)

    # 9. Next of Kin
    kin_full_name = models.CharField(max_length=200, blank=True)
    kin_relationship = models.CharField(max_length=100, blank=True)
    kin_phone = models.CharField(max_length=30, blank=True)
    kin_address = models.TextField(blank=True)

    # System fields
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    admin_note = models.TextField(blank=True)
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Loan - {self.user.username} - {self.amount}"
