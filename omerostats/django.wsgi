
"""
WSGI config for virtual environment.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys
import site

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir(os.path.join(os.path.dirname(os.__file__),'site-packages'))

# Add the app's directory to the PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
sys.path.append(os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omerostats.settings")

# Activate your virtual env
activate_env=os.path.expanduser(os.path.join(os.path.dirname(os.__file__),'..','..','bin','activate_this.py'))
execfile(activate_env, dict(__file__=activate_env))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
