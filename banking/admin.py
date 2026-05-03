from django.contrib import admin
from .models import User, KYCDocument, Transaction, Notification, CryptoWallet, CardOrderWallet, CardOrder, LoanApplication
admin.site.register(User)
admin.site.register(KYCDocument)
admin.site.register(Transaction)
admin.site.register(Notification)
admin.site.register(CryptoWallet)
admin.site.register(CardOrderWallet)
admin.site.register(CardOrder)
admin.site.register(LoanApplication)
