# EDF_viewer

## Setup Server
```
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
mkdir d:\EDF_viewer\static
mkdir d:\EDF_viewer\viewer\migrations
```

## Start Server
```
python manage.py runserver
```

## Reset Database
```
rm db.sqlite3
python manage.py makemigrations viewer
python manage.py migrate viewer
python manage.py migrate
python manage.py shell
```
