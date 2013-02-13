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

from django.conf.urls.defaults import *
from django.conf import settings

from omero_qa.registry import views

# url patterns
urlpatterns = patterns('',

    url( r'^geomap/$', views.geomap, name='registry_geomap'),
    url( r'^geoxml/$', views.get_markers_as_xml, name='registry_geoxml'),
    
    url( r'^hit/$', views.hit, name='registry_hit'),
    
    url( r'^demo_account/(?:(?P<action>((?i)enquiry|(?i)thanks))/)?$', views.demo_account, name='registry_demoaccount'),
    
    url( r'^statistic/$', views.statistic, name='registry_statistic'),
    url( r'^local_statistic/$', views.local_statistic, name='registry_local_statistic'),
    url( r'^local_stat_chart/$', views.local_statistic_chart, name='registry_local_statistic_chart'),
    url( r'^check_country/$', views.ip2country, name='ip2country'),
    url( r'^stat_chart/$', views.statistic_chart, name='registry_statistic_chart'),
    url( r'^file_stat_chart/$', views.file_statistic_chart, name='registry_file_statistic_chart'),
    
)

