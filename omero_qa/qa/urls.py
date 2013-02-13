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

from omero_qa.qa import views

# url patterns
urlpatterns = patterns('',

    url( r'^login/$', views.login_processsing, name='qa_login'),
    url( r'^reset_token/$', views.reset_token_view, name='qa_reset_token'),
    url( r'^logout/$', views.logout_view, name='qa_logout'),
    url( r'^register/$', views.register, name='qa_register'),
    url( r'^save_email/$', views.save_email_view, name='qa_save_email'),
    
    url( r'^upload/$', views.upload, name='qa_upload'),
    url( r'^upload_processing/$', views.upload_processing, name='qa_upload_processing'),
    url( r'^web_upload_processing/$', views.upload_from_web_processing, name='qa_web_upload_processing'),
    
    url( r'^initial/$', views.initial_processing, name='qa_initial_processing'),
    url( r'^feedback/$', views.feedback, name='feedback'),
    url( r'^feedback/(?P<fid>[0-9]+)/(?:(?P<action>((?i)add_comment|(?i)add_user_comment|(?i)status_update))/)?$', views.feedback, name='qa_feedback_id'),
    url( r'^feedback/(?P<action>((?i)add|(?i)test_result))/$', views.feedback_action, name='qa_feedback_action'),

    #url( r'^test_file/(?P<fid>[0-9]+)/(?P<tid>[0-9]+)/(?P<action>((?i)delete))/$', views.test_file, name='test_file_action'),
    url( r'^ticket/(?P<action>((?i)new|(?i)add|(?i)save))/(?P<fid>[0-9]+)/(?:(?P<tid>[0-9]+)/)?$', views.ticket, name='qa_ticket'),
    url( r'^error_content/(?P<fid>[0-9]+)/$', views.error_content, name='qa_error_content'),
    url( r'^test_error_content/(?P<tid>[0-9]+)/$', views.test_error_content, name='qa_test_error_content'),
    
    # extra
    url( r'^metadata_validator/(?P<build_number>[0-9]+)/$', views.metadata_validator, name='qa_metadata_validator'),
    
)

