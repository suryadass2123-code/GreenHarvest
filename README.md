# GreenHarvest — Online Farm Product Management System

GreenHarvest is a Django + MySQL agricultural marketplace that connects farmers directly with customers. This package is redesigned to match the provided modern GreenHarvest farmer dashboard visual: clean white navigation, dark-green accents, farm hero imagery, rounded cards, product panels, quick links and sales analytics.

## Technology

- Frontend: HTML5, CSS3, Bootstrap 5, Bootstrap Icons, JavaScript
- Backend: Python, Django 5.2
- Database: MySQL 8+
- Payments: Razorpay Standard Checkout (gateway-ready, server-side order creation and signature verification)
- Images: Pillow
- Environment variables: python-dotenv
- Charts: Chart.js CDN

## Included features

- Farmer registration/login and farmer dashboard
- Customer registration/login and customer dashboard
- Role-based access
- Category management
- Farmer product CRUD and image uploads
- Product search and category filters
- Shopping cart and wishlist
- Checkout and delivery address
- Cash on Delivery
- Razorpay online payment flow with server-side signature verification
- Product reviews and 1–5 star ratings
- Coupons and discounts
- Reward points
- Return/refund requests
- Notifications
- Farmer order management and status tracking
- Admin analytics dashboard
- Django admin

## Folder structure

```text
GreenHarvest_Complete_Project/
└── GreenHarvest/
    ├── manage.py
    ├── requirements.txt
    ├── .env.example
    ├── RUN_GREENHARVEST.bat
    ├── accounts/
    ├── products/
    ├── orders/
    ├── payments/
    ├── reviews/
    ├── dashboard/
    ├── greenharvest/
    ├── templates/
    ├── static/
    │   ├── css/style.css
    │   ├── js/script.js
    │   └── images/farmer-hero.png
    └── media/
```

## Windows setup — recommended

### 1. Extract the ZIP

Extract the package and open the `GreenHarvest` folder in VS Code. The folder containing `manage.py` is the Django project directory.

### 2. Create the MySQL database

Open **MySQL Workbench → Local instance → SQL Editor** and run:

```sql
CREATE DATABASE IF NOT EXISTS greenharvest_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 3. Create `.env`

Copy `.env.example` to `.env`.

PowerShell:

```powershell
copy .env.example .env
```

Then open `.env` and set your real MySQL root password:

```env
DB_NAME=greenharvest_db
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=3306

RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

Do not upload `.env` to GitHub.

### 4. Create and activate the virtual environment

From the folder containing `manage.py`:

```powershell
python -m venv venv
```

PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

Or use Command Prompt:

```cmd
venv\Scripts\activate.bat
```

### 5. Install packages

```powershell
pip install -r requirements.txt
```

### 6. Create migrations and database tables

```powershell
python manage.py makemigrations accounts products orders payments reviews
python manage.py migrate
```

### 7. Create the admin account

```powershell
python manage.py createsuperuser
```

### 8. Check the project

```powershell
python manage.py check
```

Expected result:

```text
System check identified no issues (0 silenced).
```

### 9. Run the website

```powershell
python manage.py runserver
```

Open:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/accounts/register/
- http://127.0.0.1:8000/dashboard/farmer/
- http://127.0.0.1:8000/dashboard/customer/
- http://127.0.0.1:8000/dashboard/admin/
- http://127.0.0.1:8000/admin/

## One-click Windows option

You can also run `RUN_GREENHARVEST.bat` from the `GreenHarvest` folder.

The batch file creates a local virtual environment if needed, installs requirements, checks Django, runs migrations and starts the development server. It never receives or stores your MySQL password; configure `.env` first.

## Demo accounts

You can create demo data after migrations using:

```powershell
python manage.py shell < seed_demo.py
```

Demo credentials created by the seed script:

```text
Farmer:   demo_farmer / Farmer@123
Customer: demo_customer / Customer@123
```

Change demo passwords for any real or shared deployment.

## Razorpay

The payment module creates a Razorpay order on the Django server and verifies the returned signature before marking an order as paid. Keep the Razorpay secret in `.env`, never in JavaScript or HTML.

For local testing without keys, COD works normally and the online payment page explains that gateway keys are not configured.

For real online payments, use Razorpay test keys first and configure the webhook endpoint after deployment:

```text
/payments/webhook/
```

The webhook must use a public HTTPS URL in a deployed environment.

## Visual design implemented

The farmer dashboard follows the supplied design direction:

- GreenHarvest logo/brand system
- White sticky navbar with farmer profile area
- Large farmer hero banner
- “Add New Product” and “View My Products” actions
- Direct Market Access / Better Prices / Wide Reach / Secure & Trusted / Sustainable Farming strip
- Your Products card grid
- Farm Overview KPI panel
- Weekly sales line chart
- Quick Links panel
- Sustainability promotion card
- Recent Customer Orders table
- Top Products performance panel
- Responsive mobile layout

## Important MySQL note

If Django shows:

```text
Access denied for user 'root'@'localhost'
```

then the MySQL password in `.env` does not match the root password accepted by MySQL Workbench. Fix `DB_PASSWORD` and run `python manage.py migrate` again.
