# FurniCart Backend

Django REST Framework API for the FurniCart e-commerce platform.

## Django apps

| App | Responsibility |
|-----|----------------|
| `accounts` | Users, JWT auth, OTP, profile, addresses, wallet |
| `catalog` | Products, categories, room types, variants, reviews, inventory |
| `cart` | Shopping cart and coupon application |
| `wishlist` | User wishlist |
| `orders` | Checkout, Razorpay payments, order lifecycle, returns |
| `promotions` | Coupons, offers, referral program |
| `adminpanel` | Admin authentication and dashboard APIs |

## Prerequisites

- Python 3.11+
- PostgreSQL
- Virtual environment (recommended)

Default database settings (`core/settings.py`):

| Setting | Value |
|---------|-------|
| Database name | `furnicart_db` |
| User | `postgres` |
| Host | `localhost` |
| Port | `5433` |

## Setup

```bash
cd backend
python -m venv venv312
```

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install razorpay cloudinary django-cloudinary-storage
```

**macOS / Linux:**

```bash
source venv/bin/activate
pip install -r requirements.txt
pip install razorpay cloudinary django-cloudinary-storage
```

### Environment variables

Create `backend/.env`:

```env
SECRET_KEY=your-django-secret-key
DB_PASSWORD=your-postgres-password

# Email (OTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id

# Razorpay
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_INTENT_EXPIRY_MINUTES=30

# Media (optional — set USE_CLOUDINARY=true to enable)
USE_CLOUDINARY=false
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `EMAIL_HOST_USER` | Yes | SMTP sender for OTP emails |
| `EMAIL_HOST_PASSWORD` | Yes | Gmail app password |
| `GOOGLE_CLIENT_ID` | For Google login | OAuth client ID |
| `RAZORPAY_KEY_ID` | For payments | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | For payments | Razorpay API secret |
| `USE_CLOUDINARY` | Optional | `true` to store uploads on Cloudinary |

### Database and server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Server runs at `http://localhost:8000`.

## API endpoints

### Authentication (`/api/users/`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `signup/` | Register new user |
| POST | `login/` | Login |
| POST | `verify-otp/` | Verify signup OTP |
| POST | `resend-otp/` | Resend OTP |
| POST | `forgot-password/` | Request password reset OTP |
| POST | `reset-password/` | Reset password with OTP |
| POST | `google-login/` | Google OAuth login |
| GET | `me/` | Current user |
| POST | `logout/` | Logout |
| POST | `token/refresh/` | Refresh JWT |
| GET | `csrf/` | CSRF token |

### Profile & wallet (`/api/profile/`)

| Method | Path | Description |
|--------|------|-------------|
| GET/PATCH | `` | User profile |
| GET | `wallet/` | Wallet balance |
| GET | `wallet/transactions/` | Wallet transaction history |

### Addresses (`/api/address/`)

CRUD for user shipping addresses.

### Catalog (`/api/`)

Public product listing, categories, room types, product detail, and reviews.

### Cart (`/api/cart/`)

Cart items, available coupons, and apply/remove coupon.

### Wishlist (`/api/wishlist/`)

Add, remove, and list wishlisted variants.

### Orders (`/api/orders/`)

| Area | Path | Description |
|------|------|-------------|
| Checkout | `checkout/` | Place order |
| List | `` | User orders |
| Purchases | `purchases/` | Purchase history |
| Razorpay | `razorpay/initiate/` | Start payment |
| Razorpay | `razorpay/verify/` | Verify payment |
| Returns | `returns/` | Return requests |

### Promotions

| Path | Description |
|------|-------------|
| `/api/promotions/referral/me/` | User referral code and program status |

### Admin (`/api/admin/`)

Requires a superuser account (`is_superuser=True`).

| Area | Path |
|------|------|
| Admin auth | `/api/admin/` |
| Users | `/api/admin/users/` |
| Products | `/api/admin/products/` |
| Categories | `/api/admin/categories/` |
| Room types | `/api/admin/room-types/` |
| Inventory | `/api/admin/inventory/` |
| Reviews | `/api/admin/reviews/` |
| Orders | `/api/admin/orders/` |
| Coupons | `/api/admin/coupons/` |
| Offers | `/api/admin/offers/` |
| Referral program | `/api/admin/referral-program/` |
| Sales reports | `/api/admin/reports/sales/` |
| Dashboard | `/api/admin/dashboard/` |

## Authentication

- JWT tokens are stored in **httpOnly cookies** (not localStorage).
- Frontend requests use `withCredentials: true`.
- CORS is configured for `http://localhost:5173`.

## Running tests

```bash
python manage.py test
```

Run tests for a specific app:

```bash
python manage.py test accounts
python manage.py test orders
python manage.py test cart
python manage.py test promotions
python manage.py test wishlist
```

## Referral program

1. Log in to the admin panel as a superuser.
2. Open **Refer & Earn** (`/admin/referral`).
3. Create a program and set **Program active** to on.
4. Customers will then see their referral code on the profile page.

## Payments

- Razorpay checkout is initiated via `/api/orders/razorpay/initiate/`.
- Amount is sent to Razorpay in **paise** (rupees × 100).
- Test-mode accounts have transaction limits; complete KYC for higher limits and live payments.

## Wallet refunds

When a paid order is cancelled, the refund amount is credited to the user's wallet (for Razorpay and wallet payment methods). Gateway refunds to the original payment method are not automatic in the current flow.
