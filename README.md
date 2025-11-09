# SFWE-504_Team3_SAMS
This is the group repository for Team 3's Scholarship Application Management System.

mac terminal in VSCode.
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver


Instructions for Executing a Django app using Windows OS
1. Install Python.
2. Create a Virtual Machine.
    2a. Open Command Prompt or PowerShell.
        python -m venv myenv.
    2b. Activate the environment.
        myenv\Scripts\activate.
3. Install Django.
    3a. pip install django.
    3b. django-admin --version.
4. Set Up your Existing Django App.
    4a. Navigate to the folder containing your Django project:.
        cd path\to\your\project.
    4b. Install dependencies listed in the requirements.txt.
        pip install -r requirements.txt.
5. Configure the App.
    5a. Ensure the settings.py is correctly configured:.
        check DATABASES, ALLOWED_HOSTS, and STATICFILES_DIRS.
    5b. Apply migrations.
        python manage.py migrate.
6. Run the Development Server.
    python manage.py runserver.
    6a. Visit http://127.0.0.1:8000 in your browser.