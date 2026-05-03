# 🏦 Hordstake Bank — Complete Digital Banking Platform

A production-ready full-stack Django digital banking application.

---

## ⚡ Local Setup (5 Steps)

```bash
# 1. Extract and enter the folder
cd hordstake_bank

# 2. Create & activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations & create admin
python manage.py makemigrations
python manage.py migrate
python manage.py create_superuser

# 5. Start the server
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

---

## 🔑 Default Admin Login

| Field    | Value    |
|----------|----------|
| User ID  | Admin2   |
| Password | 12345678 |
| URL      | /login/  |

---

## 🗺️ Key URLs

| URL                        | Description           |
|----------------------------|-----------------------|
| /                          | Homepage              |
| /register/                 | User Registration     |
| /login/                    | Login                 |
| /dashboard/                | User Dashboard        |
| /dashboard/profile/        | Profile + Photo       |
| /dashboard/transfer/       | Send Money            |
| /dashboard/deposit/        | Crypto Deposit        |
| /dashboard/card/           | Virtual Card          |
| /dashboard/loans/          | Loan Application      |
| /dashboard/kyc/            | KYC Upload            |
| /admin_dashboard/          | Admin Panel           |
| /admin_dashboard/users/    | Manage Users          |

---

## 🚀 Render.com Deployment Guide

### Step 1 — Push to GitHub
Push your project to a GitHub repository.

### Step 2 — Create Web Service on Render
1. Go to https://render.com → **New → Web Service**
2. Connect your GitHub repo
3. Set **Runtime** to: `Python 3`

### Step 3 — Build & Start Commands

| Field         | Value                                    |
|---------------|------------------------------------------|
| Build Command | `./build.sh`                             |
| Start Command | `gunicorn hordstake.wsgi:application`    |

### Step 4 — Environment Variables

Set these in Render → Your Service → **Environment**:

| Key               | Value                                              | Required |
|-------------------|----------------------------------------------------|----------|
| `SECRET_KEY`      | Generate one below ↓                               | ✅ YES   |
| `DEBUG`           | `False`                                            | ✅ YES   |
| `PYTHON_VERSION`  | `3.11.0`                                           | ✅ YES   |
| `RENDER_DISK_PATH`| `/var/data`  (your Render disk mount path)         | ✅ YES   |

**Generate a SECRET_KEY** — run this in Python:
```python
import secrets
print(secrets.token_urlsafe(50))
```
Or use: https://djecrety.ir/

### Step 5 — Add a Persistent Disk (for media files)
1. In your Render service → **Disks** → **Add Disk**
2. Set **Mount Path**: `/var/data`
3. Set **Size**: `1 GB` (minimum, increase as needed)
4. Set `RENDER_DISK_PATH` env variable to: `/var/data`

> ⚠️ Without the disk, uploaded images (profile photos, KYC docs) will be lost on every deploy!

### Step 6 — Deploy
Click **Deploy**. Render will run `build.sh` which:
- Installs packages
- Collects static files
- Runs migrations
- Creates the Admin2 superuser
- Creates all media subdirectories on disk

---

## 🔧 Full Environment Variables Reference

```
SECRET_KEY=your-50-char-random-secret-key-here
DEBUG=False
PYTHON_VERSION=3.11.0
RENDER_DISK_PATH=/var/data
```

---

## 📁 Project Structure

```
hordstake_bank/
├── hordstake/              # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── banking/                # Main app
│   ├── models.py           # User, Transaction, KYC, Loan, etc.
│   ├── views.py            # All views (user + admin)
│   ├── urls.py             # URL routes
│   ├── admin.py
│   ├── apps.py
│   ├── templatetags/
│   └── management/
│       └── commands/
│           └── create_superuser.py
├── templates/
│   └── banking/            # All 27 HTML templates
├── static/                 # CSS, JS assets
├── media/                  # Uploaded files (gitignored in prod)
├── manage.py
├── requirements.txt
├── Procfile
├── build.sh
└── README.md
```

---

## ✅ Features Checklist

- [x] User registration with all fields + country flags
- [x] Secure login/logout
- [x] Profile photo upload with live preview
- [x] Beautiful redesigned dashboard overview
- [x] Virtual VISA card with flip animation + CVV toggle
- [x] International transfers (IBAN/SWIFT)
- [x] Crypto deposits (BTC, ETH, USDT TRC20, SOL)
- [x] Full KYC submission (ID, address proof, selfie)
- [x] Comprehensive 9-section loan application
- [x] Physical card ordering
- [x] Transaction history with receipts
- [x] Real-time notifications system
- [x] Admin full user CRUD (create/edit/delete)
- [x] Admin credential override (User ID + Password)
- [x] Admin add/debit funds with transaction record
- [x] Admin KYC approve/reject with document viewing
- [x] Admin transfer approve/reject (auto deducts balance)
- [x] Admin crypto deposit approve/reject (auto credits)
- [x] Admin loan approve/disburse with full details view
- [x] Admin wallet configuration (deposit + card order)
- [x] Admin card order management
- [x] Custom Google Translate (60+ languages, no default widget)
- [x] Live crypto ticker (CoinGecko API)
- [x] Fully mobile responsive (homepage + all dashboards)
- [x] Persistent media files on Render disk
- [x] WhatsApp floating button
- [x] Social media icons (real brand colors)
- [x] Production-ready (gunicorn + whitenoise)
