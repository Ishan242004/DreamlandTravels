# Dreamland Travels

Dreamland Travels is a full-featured, responsive Django-based travel booking and management website. The platform enables travelers to browse tour packages, customize bookings with traveler counts and travel dates, complete payments securely via Razorpay, view invoices, track trip histories, submit feedback, and interact with support through contact messages.

It also features a robust administrative dashboard that gives administrators full control over users, packages, bookings, payments, and reviews.

---

## Technology Stack

The project is built on the following technologies:
- **Backend Framework:** Python & Django 6.0.7
- **Database:** SQLite (local development)
- **Payment Gateway:** Razorpay
- **Email Delivery:** Gmail SMTP (with secure OTP generation for booking verification and password resets)
- **Object Relational Mapper (ORM):** Django ORM
- **Frontend Technologies:** HTML5, CSS3 (including custom animation and responsive stylesheets), Vanilla JavaScript, and Bootstrap
- **Environment Management:** python-dotenv
- **Version Control:** Git & GitHub

---

## Key Features

### User Capabilities
- **Authentication & Profiles:**
  - Secure registration and login/logout.
  - Profile dashboards featuring profile photo uploads, personal details (city, state, country, DOB, gender), and profile editing.
  - Secure email-based OTP system for account password resets.
- **Tour Search & Browsing:**
  - Browse packages filtered by category (Beach, Mountain, Honeymoon, Cultural), budget ranges, and destinations.
  - Sort packages by price (low-to-high, high-to-low).
  - Detailed package pages displaying itineraries, pricing, galleries, and reviews.
- **Booking & Checkout:**
  - Interactive booking forms with automated cost calculations (based on traveler count and tax/fees).
  - High-security booking flow requiring email verification (OTP check) prior to checkout.
  - Razorpay payment gateway integration for transactions.
  - Confirmation screens and downloadable/printable invoice sheets.
- **Personal Dashboard:**
  - Track upcoming and completed trips.
  - Manage and review reservation histories.
  - Cancel bookings directly from the user dashboard.
  - Submit ratings and review feedback for completed packages.
  - Send support inquiries and view admin replies.

### Admin Capabilities
- **Custom Admin Access:**
  - Dedicated `/admin-login/` access (separate from Django's built-in `/admin/` portal) for dashboard statistics.
- **Dashboard Statistics:**
  - Monitor total revenue, pending/successful bookings, total packages, users, and contact messages in a unified screen.
- **User Management:**
  - Search, edit, and delete user profiles.
- **Package Management:**
  - Create and edit package destinations, descriptions, itineraries, inclusions, pricing, and main header images.
  - Manage multiple gallery images per travel package.
- **Booking & Payments:**
  - Overview of all user reservations and their current statuses.
  - Ability to cancel or delete bookings.
  - Review and delete transaction records.
- **Feedback & Support Messages:**
  - Approve or decline user feedback before it is shown publicly.
  - Manage customer support inquiries, reply to user tickets, mark messages as read, or delete them.

---

## Project Structure

```
DreamlandTravels/
├── manage.py                   # Django CLI utility
├── requirements.txt            # Project dependencies
├── .env                        # Local secret configurations (Ignored by Git)
├── .env.example                # Sample environment template
├── .gitignore                  # Git ignore definitions
├── README.md                   # Project documentation
├── db.sqlite3                  # SQLite Database (Ignored by Git)
├── media/                      # Uploaded media assets (Ignored by Git)
│   ├── packages/               # Package primary images
│   │   └── gallery/            # Package gallery images
│   ├── profile_photos/         # User profile photos
│   └── destinations/           # Destination category images
├── DreamlandTravels/           # Core configuration package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # Main settings loader (environment-based)
│   ├── urls.py                 # Core routing file
│   └── wsgi.py
└── Travels/                    # Main application app
    ├── admin.py                # Admin site registrations
    ├── apps.py
    ├── context_processors.py   # Context values (e.g. popular footer packages)
    ├── forms.py                # Registration and Package forms
    ├── models.py               # Main database models (Bookings, Payments, etc.)
    ├── tests.py                # Python unit & E2E tests
    ├── urls.py                 # App sub-routing configuration
    ├── views.py                # Primary business logic
    ├── migrations/             # Database migration history
    ├── static/                 # Static asset folders
    │   ├── css/                # style.css, animations.css, responsive.css
    │   ├── images/
    │   └── js/                 # main.js
    └── templates/              # HTML templates
```

---

## Installation & Setup

Follow these commands to configure the project on your machine. The instructions are optimized for Windows:

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd DreamlandTravels
```

### 2. Set Up a Virtual Environment
**Using PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Using CMD:**
```cmd
python -m venv venv
call venv\Scripts\activate.bat
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` into a new file named `.env`:
```bash
copy .env.example .env
```
Open the `.env` file and input your actual API keys, SMTP configuration, and security keys. For more information, refer to the **Environment Variables** section.

### 5. Initialize the Database
Run database migrations to prepare the local SQLite database schema:
```bash
python manage.py migrate
```

### 6. Create a Django Superuser (Optional)
If you wish to access Django's built-in administration system at `/admin/`, run:
```bash
python manage.py createsuperuser
```
*Note: The project's custom travel portal dashboard is separate and uses custom administrative login routes specified in the codebase.*

### 7. Run the Local Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

---

## Environment Variables

The project loads configurations from a `.env` file placed at the root directory. Below is the list of variables that must be configured:

| Variable | Description | Example / Recommended Value |
|---|---|---|
| `SECRET_KEY` | Django's private secret key used for session cryptographic signing. | *Generate a random hash string* |
| `DEBUG` | Enables/Disables Django debug mode (set to `False` in production). | `True` or `False` |
| `ALLOWED_HOSTS` | Comma-separated list of host/domain names this site can serve. | `127.0.0.1,localhost` |
| `RAZORPAY_KEY_ID` | Your Razorpay API Key ID. | `rzp_test_XXXXXXXXXXXXXX` |
| `RAZORPAY_KEY_SECRET` | Your Razorpay API Key Secret. | `XXXXXXXXXXXXXXXXXXXXXXXX` |
| `EMAIL_HOST` | SMTP server address. | `smtp.gmail.com` |
| `EMAIL_PORT` | Port used by the SMTP backend. | `587` |
| `EMAIL_USE_TLS` | Enables explicit TLS/SSL connection. | `True` |
| `EMAIL_HOST_USER` | Email username used to send OTP and invoices. | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | App-specific SMTP password (Gmail App Password). | `your-gmail-app-password` |
| `DEFAULT_FROM_EMAIL` | Default sender email address header. | `your-email@gmail.com` |

---

## Security Notes

1. **Never Commit Secrets:** Do not commit the `.env` file to Git. It has been pre-configured in `.gitignore`.
2. **Production Settings:** Before deploying to a production hosting platform:
   - Ensure `DEBUG=False` in your `.env`.
   - Update `ALLOWED_HOSTS` with the production domain name.
   - Configure HTTPS/SSL certificates on your web server.
   - Ensure your Razorpay variables are updated with production keys.
3. **Gmail App Password:** When setting up Gmail SMTP, do not use your standard login password. Enable 2-Step Verification and generate a dedicated **App Password** from your Google Account settings.

---

## License
License information has not yet been specified.
