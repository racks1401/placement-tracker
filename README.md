# Placement & Job Application Tracker

Campus & Off-Campus Recruitment Pipeline Manager built with **Python 3.13+**, **Django 5.1+**, **SQLite** (with environment-variable toggle for PostgreSQL), **Django Templates**, local CSS, and vanilla JS.

---

## Highlights (Version 1)

- **100% Offline Compatible**: All CSS, JS, and static assets are bundled locally inside `static/`. Zero external CDN links.
- **Strict Multi-Tenant Isolation**: Every database entity is strictly scoped to `owner=request.user`. Cross-user access attempts raise `Http404` to prevent primary key enumeration.
- **Relational Data Model**:
  - `Company`: Target employers with per-user unique name constraint.
  - `ResumeVersion`: Tailored resume profiles with auto-updating default flag.
  - `JobApplication`: Core pipeline tracking with compound database indexes `(owner, status)` and `(owner, applied_date)`.
  - `InterviewRound`: Sequential rounds (1–5 self-rating, status, scheduled date/time).
  - `ApplicationNote`: Free-form timestamped notes.
- **Service-Layer Architecture**: Dedicated `tracker/services.py` for dashboard metrics, multi-criteria filtering, and 7-day upcoming rounds calculation.
- **Full CRUD & Filters**: Search across roles/companies, filter by status, source, work mode, and sort by date or expected CTC.
- **Idempotent Demo Seeder**: Custom management command (`seed_data`) creates realistic demo data without duplicating records on re-runs.
- **Comprehensive Automated Test Suite**: 22 automated tests covering isolation, constraints, CRUD, filters, and dashboard calculations.

---

## Quick Start (< 2 Minutes)

### 1. Clone & Set Up Virtual Environment

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install pinned dependencies
pip install -r requirements.txt
```

### 2. Apply Migrations

```powershell
python manage.py migrate
```

### 3. Seed Demo Data

```powershell
python manage.py seed_data
```

**Demo Accounts Created:**
| Username | Password | Applications | Active Pipeline | Offers | Target Companies |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `alex_dev` | `DemoPassword123!` | 15 | 9 | 1 (Microsoft) | 6 |
| `priya_swe` | `DemoPassword123!` | 9 | 5 | 1 (Amazon) | 4 |

### 4. Run Automated Tests

```powershell
pytest -v
```

### 5. Launch the Development Server

```powershell
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Clean Archive Packaging

To create a clean release archive containing only tracked source code (excluding `.git/`, `.venv/`, `db.sqlite3`, and caches):

```powershell
git archive --format=zip --prefix=placement-tracker/ -o ..\placement-tracker.zip HEAD
```

Verify archive integrity:
```powershell
tar -tf ..\placement-tracker.zip
```
