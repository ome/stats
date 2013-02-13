#!/usr/bin/env python
# 
# 
# 
# Copyright (c) 2008 University of Dundee. 
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

''' A view functions is simply a Python function that takes a Web request and 
returns a Web response. This response can be the HTML contents of a Web page, 
or a redirect, or the 404 and 500 error, or an XML document, or an image... 
or anything.'''

import os
import traceback
import logging

from django.core.urlresolvers import resolve, reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.template import RequestContext as Context
from django.template.loader import get_template
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.hashcompat import md5_constructor
from django.contrib.auth.models import AnonymousUser

from omero_qa.validator.delegator import UploadProccessing, FileValidation
from omero_qa.qa.views import check_if_error, load_session_from_request
from omero_qa.qa.forms import LoginForm, UploadFileForm

logger = logging.getLogger('views-validator')

logger.info("INIT '%s'" % os.getpid())


### VIEWS ###
def upload(request, **kwargs):
    # temp
    return HttpResponseRedirect("http://validator.openmicroscopy.org.uk/")
    
    error = check_if_error(request)
    
    template = "validator/upload.html"
    login_form = LoginForm() 
    
    file_format = "*.ome;*.tif;*.tiff;*.xml"
    file_format_name = "OME, TIFF, XML files only"
    
    current_files = 0
    try:
        c = FileValidation(request.session.session_key)
        c.count_files()
        current_files = c.counter
    except:
        logger.error(traceback.format_exc())
        
    context = {'login_form':login_form, 'file_format':file_format, 'file_format_name':file_format_name, "current_files":current_files}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)

@load_session_from_request
def upload_from_web_processing(request, **kwargs):
    # temp
    return HttpResponseRedirect("http://validator.openmicroscopy.org.uk/")
    
    logger.debug("Upload from web processing...")
    try:
        sid = request.session.session_key
        if request.method == 'POST':
            logger.debug("Web POST data sent:")
            logger.debug(request.POST)
            logger.debug(request.FILES)
                        
            # upload_processing src duplication
            form_file = UploadFileForm(request.POST, request.FILES)
            if form_file.is_valid():                
                logger.debug("Data is saving to the new directory %s" % sid)
                delegator = UploadProccessing(request.FILES['Filedata'], sid)
                delegator.saveFile()
                logger.debug("Upload complete")
                return HttpResponse("Done")
            else:
                logger.error(form_file.errors.as_text())
                raise AttributeError(form_file.errors.as_text())
        else:
            raise AttributeError("Only POST accepted")
    except Exception, x:
        logger.error(traceback.format_exc())
        return HttpResponse(x)

def file_list(request, **kwargs):
    # temp
    return HttpResponseRedirect("http://validator.openmicroscopy.org.uk/")
    
    error = check_if_error(request)
    
    template = "validator/file_list.html"
    login_form = LoginForm()    
    
    controller = FileValidation(request.session.session_key)
    controller.read_files()
    file_name = request.REQUEST.get("file")
    if file_name is not None:
        try:
            logger.debug("File: %s" % file_name)
            controller.validate(file_name)            
            logger.debug(controller.schema)
            logger.debug(controller.result)
        except Exception, x:
            error = x
            logger.error(traceback.format_exc())
            
    context = {'error':error, 'login_form':login_form, 'controller':controller}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)

def delete_file(request, file_name, **kwargs):
    # temp
    return HttpResponseRedirect("http://validator.openmicroscopy.org.uk/")
    
    error = None
    controller = FileValidation(request.session.session_key)
    
    if file_name is not None:
        try:
            controller.delete(file_name)
        except Exception, x:
            error = x
    else:
        error = "File was not chosen."
    
    logger.error(error)
    request.session['error'] = error
    return HttpResponseRedirect(reverse("validator_file_list"))       
