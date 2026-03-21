# VuePoint Asset Tracker

## Overview
The VuePoint Asset Tracker is a web accessible repository of IT and office equipment that are used for hybrid and remote working.
Users can Create new assets then Read, Update and Delete existing assets. Users can then create or alter assignments that relate an asset to a user.
This was built to support VuePoints move to remote working and to provide a simple and reliable tool to keep track of who has the use of what assets. It can also be used to track if any assets on required or on order, or if they need to be PAT tested.
Database functionality also keeps track of previously assigned users to assets for auditing purposes.

## Live Application
- **URL:** [https://eprice.pythonanywhere.com](https://eprice.pythonanywhere.com)

## Test Credentials

| Role    | Username     | Password     |
|---------|-------------|-------------|
| Admin   | smorgan  | testpass123  |
| Regular | jcooper  | testpass123  |

New users can be created via the register page.
In order to create a new Admin level user the follow code must be entered into the admin code field:
[ vuepoint-admin-2026 ]

Admin users can create, read, update, and delete records. Regular users can create, read, and update only.

## Features
- Asset management with auto-generated asset IDs (e.g. HW-dell latitude 5540-01)
- Asset assignment tracking with full chain of custody history
- Current assignment displayed on asset detail page
- Role-based access control (admin and regular users)
- User registration and authentication
- Sortable columns on asset and assignment tables
- Text search across assets and assignments
- Pagination for large datasets
- Optional asset assignment during asset creation
- Reassignment workflow that closes existing assignments and creates new records
- Form validation with custom business rules
- Audit logging of all create, update, and delete operations
- Responsive design using Bootstrap 5

## Tech Stack
- **Language:** Python 3.14
- **Framework:** Django 5.2.12 (LTS)
- **Database:** SQLite
- **Frontend:** Bootstrap 5 (CDN)
- **Hosting:** PythonAnywhere

## Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

## Local Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/FilthySpartan/asset-tracker.git
cd asset-tracker
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create the logs directory
```bash
mkdir logs
```

### 5. Apply database migrations
```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)
```bash
python manage.py createsuperuser
```

### 7. Seed the database with test data
```bash
python manage.py seed_data
```

This creates 10 assets, 10 asset assignments, and 4 test users. Seed user passwords are `testpass123`.

### 8. Run the development server
```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Project Structure
```
asset-tracker/
├── apps/
│   ├── accounts/              # User authentication
│   │   ├── views.py           # Registration view
│   │   ├── urls.py            # Login, logout, register URLs
│   │   └── templates/         # Login and register templates
│   └── assets/                # Asset and assignment CRUD
│       ├── forms.py           # Custom forms with shared base class validation
│       ├── models.py          # Asset and AssetAssignment models
│       ├── views.py           # Class-based views with search, sorting, and logging
│       ├── urls.py            # URL routing for assets and assignments
│       ├── admin.py           # Admin panel registration
│       ├── management/        # Custom management commands
│       │   └── commands/
│       │       └── seed_data.py
│       └── templates/         # CRUD templates and reusable partials
│           └── assets/
├── config/                    # Django project configuration
│   ├── settings.py            # Settings including logging configuration
│   ├── urls.py
│   └── wsgi.py
├── templates/                 # Project-level templates
│   ├── base.html              # Base template with navbar and messages
│   └── includes/              # Reusable template partials
│       ├── form.html          # Shared form layout
│       └── delete_confirm.html # Shared delete confirmation
├── logs/                      # Application log files (not in version control)
├── manage.py
├── requirements.txt
└── .gitignore
```

## Database Schema
The application uses two custom models alongside Django's built-in User model:

- **Asset** — Tracks IT equipment with fields for name, type, status, cost, PAT test date, and warranty expiry. Each asset is assigned an auto-generated ID based on its type and name (e.g. HW-dell latitude 5540-01). Asset names are normalised to lowercase on save and capitalised on display.
- **AssetAssignment** — Links a user to an asset with date given and date retrieved fields. A null date_retrieved indicates the asset is currently assigned. When an asset is reassigned, the existing assignment is closed with a retrieval date and a new assignment record is created, preserving the full chain of custody.

Refer to the ERD in the accompanying report for a visual representation.

## Validation Rules
- Cost cannot be negative
- Asset name cannot be blank or whitespace only
- PAT test date cannot be in the future
- Date given cannot be in the future
- Date retrieved cannot be in the future
- Date retrieved cannot be before date given
- An asset cannot be assigned if it is already actively assigned to someone
- Assets with active assignments cannot be deleted (protected by database constraint)
- When assigning during asset creation, both user and date must be provided together

## Search
Both the asset and assignment list pages include a search bar. The asset search matches against asset name, asset ID, type, and status. The assignment search matches against asset name, asset ID, and user name.

## Sorting
All table columns support ascending and descending sort by clicking the column header. Sort indicators (▲ ▼) show the current sort column and direction. Sorting is preserved during pagination and search.

## Logging
All create, update, and delete operations are logged with timestamps, the action performed, the affected record, and the user who performed it. Unauthorised access attempts are logged at warning level. Logs are written to `logs/django.log` and the console.

## Design Decisions
- **Django's built-in User model** is used for authentication rather than a custom user model, as the brief's requirements are fully met by the existing fields (is_staff for admin/regular distinction).
- **Class-based generic views** are used for all CRUD operations to reduce boilerplate and follow Django conventions.
- **Template partials** (`includes/form.html` and `includes/delete_confirm.html`) eliminate duplication across create, update, and delete templates.
- **BaseAssetForm** provides shared validation logic inherited by both AssetForm and AssetUpdateForm, following the DRY principle.
- **on_delete=models.PROTECT** on AssetAssignment foreign keys prevents accidental deletion of assets or users that have assignment history.
