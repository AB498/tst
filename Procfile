web: python manage.py migrate && python manage.py collectstatic --noinput && python reset_db.py --yes && gunicorn --workers=2 --threads=4 wms_project.wsgi
