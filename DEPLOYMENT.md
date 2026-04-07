# Deployment Guide for IPL Dream11 App

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   python app.py
   ```

3. Access at: `http://127.0.0.1:5000`

4. Default password for input page: `admin123`
   - Change it in app.py or set environment variable: `APP_PASSWORD`

## PythonAnywhere Deployment

### Step 1: Upload Files
1. Log in to PythonAnywhere
2. Go to "Files" tab
3. Create a new directory (e.g., `ipl-dream11-2025`)
4. Upload all files:
   - app.py
   - requirements.txt
   - templates/ folder
   - static/ folder

### Step 2: Install Dependencies
1. Open a Bash console in PythonAnywhere
2. Navigate to your project directory:
   ```bash
   cd ~/ipl-dream11-2025
   ```
3. Create virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 ipl-env
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Configure Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration" (not Flask wizard)
4. Select Python 3.10

### Step 4: Configure WSGI File
1. In the Web tab, click on the WSGI configuration file link
2. Replace contents with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/ipl-dream11-2025'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables (optional)
os.environ['APP_PASSWORD'] = 'your_secure_password_here'

# Import Flask app
from app import app as application
```

Replace `YOUR_USERNAME` with your PythonAnywhere username.

### Step 5: Set Virtual Environment
1. In the Web tab, find "Virtualenv" section
2. Enter: `/home/YOUR_USERNAME/.virtualenvs/ipl-env`

### Step 6: Set Static Files
In the Web tab, add static files mapping:
- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/ipl-dream11-2025/static/`

### Step 7: Initialize Database
1. Open Bash console
2. Run:
   ```bash
   cd ~/ipl-dream11-2025
   workon ipl-env
   python
   ```
3. In Python shell:
   ```python
   from app import app, db
   with app.app_context():
       db.create_all()
   exit()
   ```

### Step 8: Reload
1. Go back to Web tab
2. Click "Reload" button
3. Access your app at: `https://YOUR_USERNAME.pythonanywhere.com`

## Database Location
- The SQLite database is stored in: `instance/ipl_dream11.db`
- This directory is automatically created when the app first runs
- The database persists across restarts

## Security Notes
- Change the default password before deploying!
- Consider using environment variables for sensitive data
- SQLite works great for this use case (single user, moderate data)

## Troubleshooting

### Error: "No module named 'app'"
- Check that your project directory is correctly set in WSGI file
- Verify virtual environment is activated

### Error: "Unable to open database file"
- Make sure `instance/` directory exists and has write permissions
- Check file paths in WSGI configuration

### Database not updating
- Verify write permissions on the instance directory
- Check PythonAnywhere error logs in the Web tab

## Backup Database
To backup your database:
```bash
cp instance/ipl_dream11.db instance/ipl_dream11_backup_$(date +%Y%m%d).db
```
