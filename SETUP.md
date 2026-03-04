# First-time Setup (Windows)

These steps create a virtual environment, install dependencies, initialize the database, and start the Django dev server.

## 1) Create/Update the virtual environment

From the repository root:

```powershell
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\setup_venv.ps1
```

If you need to wipe and recreate the venv:

```powershell
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\setup_venv.ps1 -ForceRecreate
```

## 2) Start the server (first run)

```powershell
cd paragon_scheduler

# If you did NOT run setup_venv.ps1 in the current terminal session:
..\.venv\Scripts\Activate.ps1

python manage.py migrate
python manage.py runserver
```

Then open:

- http://127.0.0.1:8000/

## 3) (Optional) Create an admin user

```powershell
cd paragon_scheduler
..\.venv\Scripts\Activate.ps1

python manage.py createsuperuser
```

## Notes

- Frontend libraries (Bootstrap + FullCalendar) are loaded via CDN in templates, so they do not need to be installed with `pip`.
- If PowerShell blocks scripts in your environment, you can either use the `-ExecutionPolicy Bypass` commands above or set an appropriate execution policy for your user.
