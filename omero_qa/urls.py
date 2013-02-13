#!/usr/bin/env python
# 
# 
# 
# Copyright (c) 2009 University of Dundee. 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2008.
# 
# Version: 1.0
#

import os.path

from django.conf.urls import url, patterns, include
from django.contrib import admin

# error handler
handler404 = "omero_qa.feedback.views.handler404"
handler500 = "omero_qa.feedback.views.handler500"

from omero_qa.qa import views
from omero_qa.registry.views import big_geomap
from django.http import HttpResponse

admin.autodiscover()

# url patterns
urlpatterns = patterns('',

    # TODO: not implemented yet
    url(r'^$', views.index, name="index"),
    url(r'^map/$', big_geomap, name="big_geomap"),
    
    # admin panel support
    url(r'^admin/', include(admin.site.urls)),
    
    # applications
    url(r'^(?i)qa/', include('omero_qa.qa.urls')),
    url(r'^(?i)registry/', include('omero_qa.registry.urls')),
    url(r'^(?i)feedback/', include('omero_qa.feedback.urls')),
    url(r'^(?i)validator/', include('omero_qa.validator.urls')),
    
    # ROBOTS: go away
    (r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /*", mimetype="text/plain"))
    
)
