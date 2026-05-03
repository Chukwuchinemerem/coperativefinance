from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.profile, name='profile'),
    path('dashboard/transfer/', views.transfer, name='transfer'),
    path('dashboard/transactions/', views.transactions, name='transactions'),
    path('dashboard/deposit/', views.deposit, name='deposit'),
    path('dashboard/kyc/', views.kyc_upload, name='kyc'),
    path('dashboard/card/', views.virtual_card, name='virtual_card'),
    path('dashboard/card-order/', views.card_order, name='card_order'),
    path('dashboard/loans/', views.loans, name='loans'),
    path('dashboard/notifications/', views.notifications_view, name='notifications'),
    path('dashboard/receipt/<uuid:txn_id>/', views.receipt, name='receipt'),

    # Admin Dashboard
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_dashboard/users/', views.admin_users, name='admin_users'),
    path('admin_dashboard/users/create/', views.admin_create_user, name='admin_create_user'),
    path('admin_dashboard/users/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('admin_dashboard/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin_dashboard/users/<int:user_id>/funds/', views.admin_add_funds, name='admin_add_funds'),
    path('admin_dashboard/kyc/', views.admin_kyc, name='admin_kyc'),
    path('admin_dashboard/kyc/<int:kyc_id>/<str:action>/', views.admin_kyc_action, name='admin_kyc_action'),
    path('admin_dashboard/transfers/', views.admin_transfers, name='admin_transfers'),
    path('admin_dashboard/transfers/<uuid:txn_id>/<str:action>/', views.admin_transfer_action, name='admin_transfer_action'),
    path('admin_dashboard/deposits/', views.admin_deposits, name='admin_deposits'),
    path('admin_dashboard/deposits/<uuid:txn_id>/<str:action>/', views.admin_deposit_action, name='admin_deposit_action'),
    path('admin_dashboard/loans/', views.admin_loans, name='admin_loans'),
    path('admin_dashboard/loans/<int:loan_id>/<str:action>/', views.admin_loan_action, name='admin_loan_action'),
    path('admin_dashboard/wallets/', views.admin_wallets, name='admin_wallets'),
    path('admin_dashboard/card-orders/', views.admin_card_orders, name='admin_card_orders'),
    path('admin_dashboard/card-orders/<int:order_id>/<str:action>/', views.admin_card_order_action, name='admin_card_order_action'),

    # AJAX
    path('api/mark-notification-read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
]
