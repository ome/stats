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
from django.core.urlresolvers import reverse

from omero_qa.validator import views

# url patterns
urlpatterns = patterns('',

    url( r'^upload/$', views.upload, name='validator_upload'),
    url( r'^web_upload_processing/$', views.upload_from_web_processing, name='validator_web_upload_processing'),
    url( r'^file_list/$', views.file_list, name='validator_file_list'),
    url( r'^delete_file/(?P<file_name>.*)/$', views.delete_file, name='validator_delete_file'),
    
)

