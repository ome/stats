#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#
# Copyright (c) 2009-2013 University of Dundee.
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


from django.conf.urls import include, url, patterns
from django.contrib import admin


from django.conf import settings

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.http import HttpResponse


admin.autodiscover()

from omerostats.registry import views

# url patterns
urlpatterns = patterns(
    '',

    # admin panel support
    url(r'^admin/', include(admin.site.urls)),

    # TODO: not implemented yet
    url(r'^$', views.index, name="index"),
    url(r'^map/$', views.big_geomap, name="big_geomap"),

    # applications
    url(r'^(?i)registry/', include('omerostats.registry.urls')),

    # ROBOTS: go away
    (r'^robots\.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /*", mimetype="text/plain"))
)

urlpatterns += staticfiles_urlpatterns()

# Only append if urlpatterns are empty
if settings.DEBUG and not urlpatterns:
    urlpatterns += staticfiles_urlpatterns()
