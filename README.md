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

        git clone git@github.com:openmicroscopy/qa.git

2. Set up a virtualenv (http://www.pip-installer.org/) and activate it

        curl -O -k https://raw.github.com/pypa/virtualenv/master/virtualenv.py
        python virtualenv.py qa-virtualenv
        source qa-virtualenv/bin/activate
        pip install numpy
        pip install -r requirements.txt

3. Set up your database

        # Create a PostgreSQL user
        sudo -u postgres createuser -P -D -R -S feedback_user
        # Create a database
        sudo -u postgres createdb -O feedback_user feedback

4. Download and extract the GeoIP country and city databases

        curl -O http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
        curl -O http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
        gzip -d GeoIP.dat.gz
        gzip -d GeoLiteCity.dat.gz

5. How to migrate the existing database
    * Generate files by the script doc/dbdump.py
    * Execute select count(*) from hit;
    * edit the dbdump.py and change LIMIT if 10 000 000 is not enough :-)
    * dump the existing db to qa-2009-10-01.db file
    * python dbdump.py  qa-2009-10-01.db > hit.sql
    * copy hit.sql to your_path/omero_qa/registry/sql/

Configuration
=============

* Copy settings.py to settings-prod.py

* Set `ADMINS`

        ADMINS = (
            ('Aleksandra Tarkowska', 'A.Tarkowska@dundee.ac.uk'),
        )

* Change database settings

        ...
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'feedback',                      # Or path to database file if using sqlite3.
        'USER': 'feedback_user',                      # Not used with sqlite3.
        'PASSWORD': 'password',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
        ...

* Modify `FEEDBACK_URL = "qa.openmicroscopy.org.uk:80"` - this is the host where errors should be reported if application itself crashes

* Google key on http://code.google.com/apis/maps/signup.html 

        mage.open...    GOOGLE_KEY = "***REMOVED***"
        qa.open...      GOOGLE_KEY = "***REMOVED***"

* Please DO NOT change second key, it is registered for http://registry.openmicroscopy.org.uk

        GOOGLE_KEY2 = "***REMOVED***"
    
* Create rest of required dirs:
    * UPLOAD_ROOT = "/FileStore" <- this is equivalent of /ome/apache_repo
    * VALIDATOR_UPLOAD_ROOT = "/Validator"
    * TESTNG_ROOT = "/TestNG"
 
* Set up `OME_HUDSON_PATH = "/ome/hudson/jobs"`

* Set up `APPLICATION_HOST = "http://qa.openmicroscopy.org.uk"`- this is part of the url what appears in email. When user click it, should jump to the feedback page.

* Set up email server
    
        # Application allows to notify user
        EMAIL_HOST = 'localhost'
        EMAIL_HOST_PASSWORD = ''
        EMAIL_HOST_USER = ''
        EMAIL_PORT = 25
        EMAIL_SUBJECT_PREFIX = '[OMERO.qa] '
        EMAIL_USE_TLS = False
        SERVER_EMAIL = 'A.Tarkowska@dundee.ac.uk' # email address

* Synchronise the database

        python manage.py syncdb --settings=settings-prod
    
__WARNING:__ If you see memory issue, move hit.sql file out of application directory, run syncdb again (it will create every tables for you), then:
psql -U feedback_user feedback < hit.sql

__WARNING:__ What is qa.openmicroscopy.org.uk/map?

The purpose of that page is availability under the http://registry.openmicroscopy.org.uk. It shows up as an independent page and require the following configuration:

    <VirtualHost *:80>
            ServerAdmin webmaster@openmicroscopy.org.uk
            DocumentRoot /var/www/localhost/htdocs/
            ServerName registry.openmicroscopy.org.uk

            RewriteEngine on
            RewriteRule ^/$ http://qa.openmicroscopy.org.uk/map/ [P]
            RewriteRule ^/xml/$ http://qa.openmicroscopy.org.uk/registry/geoxml/ $

            <Directory "/var/www/localhost/htdocs">
                    AllowOverride All
                    Options None
                    Order allow,deny
                    Allow from all
            </Directory>
    </VirtualHost>

any changes require changes in the template/big_map.html

Trac systems
============

 * Configure user to create ticket in Trac
 
        trac.openmicroscopy.org.uk/ome

Site 1
======

Login to admin panel and change `Site = 1` to current qa_host qa.openmicroscopy.org.uk.

Upgrade hits
============

* Create old db backup as `r-date.db`
* Run migration script

        python doc/dbdump.py r-date.db > hit.sql

* Perform upgrade
 
        pg_dump -Fc -f ...
        drop table registry_ip;
        rm initial_data.json
        sudo -u apache -s
        python manage.py syncdb --settings=settings-prod
        psql -h localhost -U feedback feedback < hit.sql

* Restore from backup

        pg_restore -h localhost -U feedback -Fc -d feedback file_name

Upgrade 1.1
===========

* Backup db

        pg_dump -Fc -h localhost -p 5433 -U feedback -f r-date.db feedback

* Run migration script

        python doc/upgrade-1.1.py > newdb-1.1.sql

* Clean up and perform upgrade

        DROP TABLE "registry_hit";
        DROP TABLE "registry_ip";
        DROP TABLE "registry_agent";
        python manage.py syncdb --settings=settings-prod
        psql -h localhost -p 5433 -U feedback feedback < newdb-1.1.sql

Legal
=====

The source for OMERO.qa is released under the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

OMERO.qa is Copyright (C) 2008-2012 University of Dundee
