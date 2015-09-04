OMERO.qa
========

OMERO.qa is the web application which helps support community by OMERO team.

Requirements
============

* PostgreSQL 8.2+
* Python 2.6+

Development Installation
========================

1. Clone the repository

        git clone git@github.com:openmicroscopy/stats.git

2. Set up a virtualenv (http://www.pip-installer.org/) and activate it

        pip install virtualenv
        virtualenv --system-site-packages stats-virtualenv
        source stats-virtualenv/bin/activate

3. Install dependencies

        pip install matplotlib
        pip install psycopg2
        pip install mercurial
        pip install -r requirements.txt

4. Dump and restore database.

5. Download and extract GeoIP databases

        GeoIP2-Domain.mmdb, GeoIPOrg.dat, GeoLite2-City.mmdb

Configuration
=============

* Create new settings-prod.py and import default settings

        from settings import *

* Set `DEBUG`

        DEBUG=False
        TEMPLATE_DEBUG = DEBUG

* Set `ADMINS`

        ADMINS = (
            ('Full Name', 'email@example.com'),
        )

* Change database settings

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                                                # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
                'NAME': 'stats_database',       # Or path to database file if using sqlite3.
                'USER': 'stats_user',           # Not used with sqlite3.
                'PASSWORD': 'secret',           # Not used with sqlite3.
                'HOST': 'localhost',            # Set to empty string for localhost. Not used with sqlite3.
                'PORT': '5432',                 # Set to empty string for default. Not used with sqlite3.
            }
        }

* Set up email server
    
        # Application allows to notify user
        EMAIL_HOST = 'localhost'
        EMAIL_HOST_PASSWORD = ''
        EMAIL_HOST_USER = ''
        EMAIL_PORT = 25
        EMAIL_SUBJECT_PREFIX = '[OMERO.stats] '
        EMAIL_USE_TLS = False
        SERVER_EMAIL = 'email@example.com' # email address

* WSGI config file for virtual environment (omerostats/django.wsgi):

        import os
        import sys
        import site

        # Add the site-packages of the chosen virtualenv to work with
        site.addsitedir('/path/to/stats-virtualenv/lib64/python2.6/site-packages')

        # Add the app's directory to the PYTHONPATH
        sys.path.append('/path/to/stats.git/')
        sys.path.append('/path/to/stats.git/omerostats')

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omerostats.settings-prod")

        # Activate your virtual env
        activate_env=os.path.expanduser('/path/to/stats-virtualenv/bin/activate_this.py')
        execfile(activate_env, dict(__file__=activate_env))

        import django.core.handlers.wsgi
        application = django.core.handlers.wsgi.WSGIHandler()

* Synchronise the database

        export DJANGO_SETTINGS_MODULE=omerostats.settings-prod
        python manage.py syncdb
        python manage.py sqlcustom registry | python manage.py dbshell

* Populated GEO details about IPs
        python upgrade/ip.py

* Collect statics

        python manage.py collectstatic

* Setup apache

    <VirtualHost *:80>

        ServerAlias stats.openmicroscopy.org
        ServerName stats.openmicroscopy.org
        ServerAdmin sysadmin@openmicroscopy.org

        ErrorLog /var/log/httpd/stats.openmicroscopy.org.err
        CustomLog /var/log/httpd/stats.openmicroscopy.org.log combined

        DocumentRoot /home/omero-stats/stats.git

        WSGIDaemonProcess omerostats processes=2 threads=15 display-name=%{GROUP} python-path=/home/omero-stats/stats.git:/home/omero-stats/reg-virtualenv/lib/python2.6/site-packages
        WSGIProcessGroup omerostats

        WSGIScriptAlias / /home/omero-stats/stats.git/omerostats/django.wsgi

        <Directory /home/omero-stats/stats.git/omerostats/>
            Order allow,deny
            Allow from all
        </Directory>

        Alias /static /home/omero-stats/stats.git/static
        <Location "/static/">
            Options -Indexes
        </Location>

    </VirtualHost>
    WSGISocketPrefix run/wsgi


Legal
=====

The source for OMERO.stats is released under the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

OMERO.stats is Copyright (C) 2008-2015 University of Dundee
