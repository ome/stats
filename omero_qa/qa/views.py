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
import shutil
import traceback
import logging
import time
import base64
import os
import random
from random import choice
import urlparse
from datetime import date, datetime, timedelta
from django.views.decorators.csrf import csrf_exempt

from pygeoip import GeoIP, STANDARD
from ipaddr import IPv4Address

import urllib
try:
    from xml.etree.ElementTree import XML, ElementTree, tostring
except ImportError:
    from elementtree.ElementTree import XML, ElementTree, tostring

# Use the system (hardware-based) random number generator if it exists.
if hasattr(random, 'SystemRandom'):
    randrange = random.SystemRandom().randrange
else:
    randrange = random.randrange

from django.core.urlresolvers import resolve, reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.template import RequestContext as Context
from django.template.loader import get_template
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.hashcompat import md5_constructor
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from omero_qa.feedback.views import handlerInternalError
from omero_qa.qa.models import JUnitResult, TestNGXML, TestFile2, MetadataTest, MetadataTestResult, \
    Feedback, AppType, FileFormat, FeedbackStatus, AdditionalFile, TestEngineResult, \
    NotificationList
from omero_qa.qa.forms import LoginForm, UserForm, UploadFileForm, \
    FileTypeForm, EmailForm,  FeedbackForm, StatusForm, TestEngineResultForm, \
    CommentForm, UserCommentForm, TicketForm, ExistingTicketForm, FilterFeedbackForm

from omero_qa.qa.delegator import UploadProccessing, prepare_comparation, create_ticket, add_comment


logger = logging.getLogger('views-qa')

logger.info("INIT '%s'" % os.getpid())

# DECORATORS
def load_session_from_request(handler):
    """Read the session key from the GET/POST vars instead of the cookie.

    Centipedes, in my request headers?
    Yes! We sometimes receive the session key in the POST, because the
    multiple-file-uploader uses Flash to send the request, and the best Flash
    can do is grab our cookies from javascript and send them in the POST.
    """
    def func(request, *args, **kwargs):
        session_key = request.REQUEST.get(settings.SESSION_COOKIE_NAME, None)
        if not session_key:
            # TODO(rnk): Do something more sane like ask the user if their
            #            session is expired or some other weirdness.
            logger.error("Session key does not exist.")
            raise Http404()
        # This is how SessionMiddleware does it.
        session_engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
        try:
            request.session = session_engine.SessionStore(session_key)
        except Exception, e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return html_error(e)
        logger.debug("Session from request loaded successfully.")
        return handler(request, *args, **kwargs)
    return func


### HELPER ###
def doPaging(page, page_size, total_size, limit):
    total = list()
    t = total_size/limit
    if total_size > (limit*10):
        if page > 10 :
            total.append(-1)
        for i in range((1, page-9)[ page-9 >= 1 ], (t+1, page+10)[ page+9 < t ]):
            total.append(i)
        if page < t-9:
            total.append(-1)

    elif total_size > limit and total_size <= (limit*10):
        for i in range(1, t+2):
            total.append(i)
    else:
        total.append(1)
    next = None
    if page_size == limit and (page*limit) < total_size:
        next = page + 1
    prev = None
    if page > 1:
        prev = page - 1
    return {'page': page, 'total':total, 'next':next, "prev":prev}


def create_response(request):
    redirect = request.REQUEST.get('redirect')
    if redirect is not None:
        response = HttpResponseRedirect(redirect)
    else:
        next = request.REQUEST.get('next')
        if next is not None:
            response = HttpResponseRedirect(next)
        else:
            next = request.META and request.META.get('HTTP_REFERER', None) or '/'
            response = HttpResponseRedirect(next)

        #view, args, kwargs = resolve(urlparse.urlparse(next)[2])
        #kwargs['request'] = request
        #try:
        #    view(*args, **kwargs)
        #except Http404:
        #    response = HttpResponseRedirect('/')
    logger.debug(response)
    return response


def create_or_retrieve_token(request):
    max_key = 18446744073709551616L
    
    if request.REQUEST.get('token') == request.session.get('token') and request.session.get('token') is not None:
        pass
    elif request.REQUEST.get('token') is not None:
        logger.debug("Token from request: '%s'" % (request.REQUEST.get('token')))
        request.session['token'] = request.REQUEST.get('token')
    else:
        logger.debug("Token could not be retrieved from request.")
        if not request.session.has_key('token'):
            logger.debug("Create new token.")
            pid = 1
            token_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            while 1:
                token = md5_constructor("%s%s%s%s"
                        % (randrange(0, max_key), pid, time.time(), token_key)).hexdigest()
                try:
                    if len(Feedback.objects.filter(token=token)) > 0:
                        pass
                    else:
                        request.session['token'] = token
                        break
                except:
                    request.session['token'] = token
                    break
            logger.debug("New token: '%s'" % (request.session['token']))
        else:
            logger.debug("Token already exist in session: '%s'" % (request.session.get('token')))
    return request.session.get('token')


def reset_token(request):
    try:
        del request.session['token']
    except KeyError:
        pass
    except:
        logger.error(traceback.format_exc())
    
    return create_or_retrieve_token(request)


def reset_token_view(request):
    try:
        del request.session['token']
    except KeyError:
        pass
    except:
        logger.error(traceback.format_exc())
    try:
        del request.session['file_format']
    except KeyError:
        pass
    except:
        logger.error(traceback.format_exc())
    return HttpResponseRedirect("/qa/upload/")


def notify(feedback, comment=None, email_template=None):
    try:
        from omero_qa.feedback.models import EmailTemplate
        message = None
        message_html = None
        message_staff = None
        message_html_staff = None
        template = EmailTemplate.objects.get(template=email_template)
        emial_template_staff = "%s_staff" % email_template
        try:
            template_staff = EmailTemplate.objects.get(template=emial_template_staff)
        except EmailTemplate.DoesNotExist:
            template_staff = None
        except:
            logger.error(traceback.format_exc())
            template_staff = None
        title = None
        if email_template == "upload_message":
            if feedback is not None:
                if feedback.app_name is not None:
                    title = 'OMERO.qa - new feedback for %s ' % (feedback.app_name)
                message = template.content_txt % (settings.APPLICATION_HOST, feedback.id, feedback.token)
                message_html = template.content_html % (settings.APPLICATION_HOST, feedback.id, feedback.token,settings.APPLICATION_HOST, feedback.id, feedback.token)
                if template_staff is not None:
                    message_staff = template_staff.content_txt % (settings.APPLICATION_HOST, feedback.id, feedback.token, feedback.comment, feedback.error)
                    message_html_staff = template_staff.content_html % (settings.APPLICATION_HOST, feedback.id, feedback.token,settings.APPLICATION_HOST, feedback.id, feedback.token, feedback.comment, feedback.error)
        elif email_template == "status_message":
            if feedback is not None:
                title = 'OMERO.qa - status changed'
                message = template.content_txt % (feedback.status.status, settings.APPLICATION_HOST, feedback.id, feedback.token)
                message_html = template.content_html % (feedback.status.status, settings.APPLICATION_HOST, feedback.id, feedback.token,settings.APPLICATION_HOST, feedback.id, feedback.token)
                if template_staff is not None:
                    message_staff = template_staff.content_txt % (feedback.status.status, settings.APPLICATION_HOST, feedback.id, feedback.token)
                    message_html_staff = template_staff.content_html % (feedback.status.status, settings.APPLICATION_HOST, feedback.id, feedback.token,settings.APPLICATION_HOST, feedback.id, feedback.token)
        elif email_template == "comment_message":
            if feedback is not None:
                title = 'OMERO.qa - new comment'
                message = template.content_txt % (settings.APPLICATION_HOST, feedback.id, feedback.token, comment)
                message_html = template.content_html % (settings.APPLICATION_HOST, feedback.id, feedback.token,settings.APPLICATION_HOST, feedback.id, feedback.token, comment)
                if template_staff is not None:
                    message_staff = template_staff.content_txt % (settings.APPLICATION_HOST, feedback.id, feedback.token, comment)
                    message_html_staff = template_staff.content_html % (settings.APPLICATION_HOST, feedback.id, feedback.token,settings.APPLICATION_HOST, feedback.id, feedback.token, comment)
        
        # recipiests
        recipients = list()
        staff_recipients = list()
            
        if feedback.user is not None:
            recipients.append(str(feedback.user.email))
        elif len(feedback.email) > 5:
            recipients.append(str(feedback.email))
                    
        for n in NotificationList.objects.filter(app_name=feedback.app_name):
            if n.user is not None:
                staff_recipients.append(str(n.user.email))
            elif len(n.email) > 5:
                staff_recipients.append(str(n.email))
        
        if comment is not None:
            try:
                email = comment.user and comment.user.email or comment.email
                logger.debug("Comment email '%s'" % email)
                recipients.remove(email)
            except:
                pass
            
        if len(recipients) > 0 :
            logger.debug("Recipiest list %i" % len(recipients))
            logger.info(recipients)
            if title is None:
                title = 'OMERO.qa - feedback'
            
            text_content = message
            html_content = message_html
            msg = EmailMultiAlternatives(title, text_content, settings.SERVER_EMAIL, recipients)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info('Email was sent.')
            
            logger.debug("Staff Recipiest list %i" % len(staff_recipients))
            logger.info(staff_recipients)
            
            if title is None:
                title = 'OMERO.qa - feedback'
            
            text_content = message_staff is not None and message_staff or message
            html_content = message_html_staff is not None and message_html_staff or message_html
            
            msg = EmailMultiAlternatives(title, text_content, settings.SERVER_EMAIL, staff_recipients)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            logger.info('Email was sent.')
        else:
            logger.debug("No recipients were notified")
    except:
        logger.error('Email could not be sent')
        logger.error(traceback.format_exc())


def check_if_error(request):
    error = None
    try:
        if request.session['error']:
            error = request.session['error']
            request.session['error'] = None
    except:
        request.session['error'] = None
    logger.debug("Error: %s" % error)
    return error


def get_lng_and_lat(ip_address):
    latitude = None
    longitude = None
    if IPv4Address(ip_address).is_private:
        logger.debug("Local ip: '%s'" % ip_address)
        latitude = 56.457670
        longitude = -2.986810 
    else:
        logger.debug("Checking ip: '%s' ..." % ip_address)
        geoip = GeoIP(settings.GEODAT, STANDARD)
        gir = geoip.record_by_addr(ip_address)
        if gir is not None:
            latitude = gir["latitude"]
            longitude = gir["longitude"]
        
    if latitude is None or longitude is None:
        return None
    logger.debug("IP: %s, latitude: '%s', longitude: '%s'" % (ip_address, latitude, longitude))
    return (latitude, longitude)

    
### VIEWS ###
def index(request, **kwargs):        
    error = check_if_error(request)
    redirect = request.REQUEST.get('redirect', None)
    template = "qa/index.html"
    
    login_form = LoginForm()
    context = {'login_form':login_form, 'error':error}
    if redirect is not None:
        context['redirect'] = redirect
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def register(request, **kwargs):
    template = "qa/register.html"
    error = check_if_error(request)
    if request.method == 'POST':
        form_reg = UserForm(data=request.REQUEST.copy())
        if form_reg.is_valid():
            username = request.REQUEST.get('username')
            first_name = request.REQUEST.get('first_name')
            last_name = request.REQUEST.get('last_name')
            email = request.REQUEST.get('email')
            password = request.REQUEST.get('password')
            user = User(username=username,first_name=first_name,last_name=last_name,email=email)
            user.is_staff = False
            user.is_superuser = False
            user.set_password(password)
            user.save()
            request.session['error'] = "You have been registered successful. Log in now!"
            logger.debug("New user was created: '%s'" % (user.username))
            return HttpResponseRedirect("/")
    else:
        form_reg = UserForm()
    context = {'form':form_reg, 'error':error}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def login_processsing(request):
    error = check_if_error(request)
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                logger.debug("User logged in successfully.")
                return create_response(request)
            else:
                request.session['error'] = "User is not active."
                logger.error("User is not active.")
                return create_response(request)
        else:
            request.session['error'] = "Wrong username or password."
            logger.error("Wrong username or password.")
            return create_response(request)
    else:
        return create_response(request)


def logout_view(request):
    logout(request)
    logger.debug("User was logged out successfully.")
    return HttpResponseRedirect("/")


def save_email_view(request):
    resp = ""
    if request.REQUEST.get('email'):
        email_form = EmailForm(data=request.REQUEST.copy())
        if email_form.is_valid():
            request.session['email'] = request.REQUEST.get('email')
            logger.debug("Email '%s' was save in session." % request.session.get('email'))
        else:   
            resp = "Error: %s" % str(email_form.errors.get('email'))
    else:
        logger.debug("Email could not be retrived from request.")
        resp = "Error: Email could not be retrived from request."
    return HttpResponse(resp)


def upload(request, **kwargs):
    error = check_if_error(request)
    token = None
    
    template = "qa/upload.html"
    login_form = LoginForm() 
    if request.REQUEST.get('email'):
        request.session['email'] = request.REQUEST.get('email')
    
    email_form = EmailForm(data={'email':request.session.get('email')})
    ftype = request.REQUEST.get('file_format')
    token = reset_token(request)
    
    current_files = 0
    current_feedback = None
    try:
        current_files = Feedback.objects.get(token=token).test_files.count()
        current_feedback = Feedback.objects.get(token=token)
    except:
        pass

    extra = request.META.get('HTTP_USER_AGENT', '')
    context = {'token': token, 'current_files':current_files, 'current_feedback':current_feedback, 'login_form':login_form, 'email_form':email_form, 'extra':extra}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)  

@csrf_exempt
def upload_from_web_processing(request, **kwargs):
    logger.debug("Upload from web processing...")
    try:
        token = create_or_retrieve_token(request)
        if request.method == 'POST':
            logger.debug("Web POST data sent:")
            logger.debug(request.POST)
            logger.debug(request.FILES)
            try:
                feedback = Feedback.objects.get(token=token)
                logger.debug("Feedback exist. ID: '%i'" % feedback.id)
            except:
                logger.debug("New Feedback is being creating")

                form_feedback = FeedbackForm(data={'token':token})
                if form_feedback.is_valid():       
                    temp_form = form_feedback.save(commit=False)
                    temp_form.ip_address = request.META.get('REMOTE_ADDR', '')
                    temp_form.user_agent = request.META.get('HTTP_USER_AGENT', '')
                    temp_form.extra = request.REQUEST.get('extra')
                    
                    if request.user.is_authenticated():
                        temp_form.user = request.user
                    elif request.session.get('email'):
                        temp_form.email = request.session.get('email')
                    try:
                        app_name = AppType.objects.get(pk=request.POST.get('app_name'))
                        temp_form.app_name = app_name
                    except:
                        pass
                    temp_form.save()
                    feedback=temp_form                    
                    logger.debug("New Feedback saved. ID: '%i'" % feedback.id)
                
                    try:
                        notify(feedback=feedback, email_template="upload_message")
                        logger.debug("Notification for upload_message")
                    except:
                        logger.error("NOTIFICATION NOT SENT")
                        logger.error(traceback.format_exc())
                else:
                    logger.error(form_file.errors.as_text())
                    raise AttributeError(form_file.errors.as_text())
            
            # upload_processing src duplication
            form_file = UploadFileForm(request.POST, request.FILES)
            if form_file.is_valid():                
                try:
                    if feedback is not None:
                        exist = False
                        for f in feedback.test_files.all():
                            if f.file_name == request.FILES['Filedata'].name:
                                exist = True
                                break
                        if not exist:
                            logger.debug("Data is adding to the existing feedback.")

                            delegator = UploadProccessing(request.FILES['Filedata'], feedback.id)
                            try:
                                file_format = FileFormat.objects.get(pk=int(request.POST['file_format']))
                            except:
                                try:
                                    file_format = FileFormat.objects.get(reader=request.POST['file_format'])
                                except:
                                    file_format = None

                            test_files = delegator.saveFile(file_format)

                            feedback.test_files.add(test_files)
                            feedback.save()
                            
                            delegator.create_init_from_feedback()
                            
                            logger.debug("Feedback complete.")
                            return HttpResponse("Done")
                        else:
                            logger.debug("File was not saved because already exist.")
                            return HttpResponse("File already exist")
                    else:
                        raise AttributeError("Feedback does not exist.")
                except Exception, x:
                    logger.error(traceback.format_exc())
                    return HttpResponse(x)
            else:
                logger.error(form_file.errors.as_text())
                raise AttributeError(form_file.errors.as_text())
        else:
            raise AttributeError("Only POST accepted")
    except Exception, x:
        logger.error(traceback.format_exc())
        return HttpResponse(x)
    

def upload_processing(request, **kwargs):
    logger.debug("Upload processing...")
    try:
        token = create_or_retrieve_token(request)
        if request.method == 'POST':
            logger.debug("File POST data sent:")
            logger.debug(request.POST)
            logger.debug(request.FILES)
            form_file = UploadFileForm(request.POST, request.FILES)
            if form_file.is_valid():                
                try:
                    feedback = Feedback.objects.get(token=token)
                    logger.debug("Data is adding to the existing feedback.")
                    
                    delegator = UploadProccessing(request.FILES['Filedata'], feedback.id)
                    delegator.create_init(feedback.selected_file)
                    try:
                        file_format = FileFormat.objects.get(pk=int(request.POST['file_format']))
                    except:
                        try:
                            file_format = FileFormat.objects.get(reader=request.POST['file_format'])
                        except:
                            file_format = None
                    
                    test_files = delegator.saveFile(file_format)
                    
                    feedback.test_files.add(test_files)
                    feedback.save()
                    logger.debug("Feedback complete.")
                    return HttpResponse("Upload complete.")
                    
                except Exception, x:
                    logger.error(traceback.format_exc())
                    return HttpResponse(x)
            else:
                logger.error(form_file.errors.as_text())
                raise AttributeError(form_file.errors.as_text())
        else:
            raise AttributeError("Only POST accepted.")
    except Exception, x:
        logger.error(traceback.format_exc())
        return HttpResponse(x)
        
             
def initial_processing(request, **kwargs):
    logger.debug("Initial processing...")
    try:
        token = create_or_retrieve_token(request)
        if request.method == 'POST':
            logger.debug("Initial feedback POST data sent:")
            logger.debug(request.POST)
            
            # TODO: temporary work arround to make form valid
            # there may be another way to add custom data
            from django.http import QueryDict
            q = QueryDict('', mutable=True)
            q.update({'token': token})
            request.REQUEST.dicts += (q,)
            
            form_feedback = FeedbackForm(data=request.REQUEST.copy())
            if form_feedback.is_valid():       
                temp_form = form_feedback.save(commit=False)
                temp_form.ip_address = request.META.get('REMOTE_ADDR', '')
                temp_form.user_agent = request.META.get('HTTP_USER_AGENT', '')
                # for some reason extra is not save as the rest of the request
                # simple work arround
                temp_form.extra = request.REQUEST.get('extra')
                
                if request.user.is_authenticated():
                    temp_form.user = request.user
                try:
                    app_name = AppType.objects.get(pk=request.POST.get('app_name'))
                    temp_form.app_name = app_name
                except:
                    pass
                temp_form.save()
                feedback=temp_form
                
                # Additional files
                logger.debug("Additional files saving...")
                af = request.REQUEST.getlist('additional_files')
                afp = request.REQUEST.getlist('additional_files_path')
                afs = request.REQUEST.getlist('additional_files_size')
                af_len = len(af)
                afs_len = len(afs)
                afp_len = len(afp)
                if af_len > 0 and af_len == afs_len:
                    additional_files=list()
                    for i in range(0, af_len):
                        logger.debug("Additional file: %s/%s (%s)" % (afp[i], af[i], afs[i]))
                        add_file = AdditionalFile(file_path=afp[i], file_name=af[i], file_size=afs[i])
                        add_file.save()
                        additional_files.append(add_file)
                    if len(additional_files) > 0:
                        feedback.additional_files = additional_files
                        feedback.save()
                    logger.debug("Additional files list was saved.")
                else:
                    logger.debug("Additional files list could not be saved. Arrays are not equal.")
                
                logger.debug("New Feedback saved. ID: '%i'" % feedback.id)
                request.session['error'] = "Feedback was creates successfully."
                
                try:
                    notify(feedback=feedback, email_template="upload_message")
                    logger.debug("Notification for upload_message")
                except:
                    logger.error("NOTIFICATION NOT SENT")
                    logger.error(traceback.format_exc())
                
                logger.error("Return token: '%s'" % token)
                return HttpResponse(token)
            else:
                error = form_feedback.errors.as_text()
                logger.error(error)
                raise AttributeError(error)
        else:
            raise AttributeError("Only POST accepted")
    except Exception, x:
        logger.error(traceback.format_exc())
        return HttpResponse(x)


def feedback(request, fid=None, action=None, **kwargs):
    error = check_if_error(request)
    token = create_or_retrieve_token(request)

    template = "qa/feedback_user.html"
    login_form = None
    feedback = None
    apps = None
    
    status_form = None
    filter_form = None
    fileset = None
    test_results = None
    format = None
    geo = None
    app_name = None
    paging = dict()
    params = dict()
    
    comment_form = None
    user_comment_form = None
    
    if not request.user.is_authenticated():    
        login_form = LoginForm()
    
    if fid is not None:
        logger.debug("Feedback id %s" % fid)
        # specific feedback
        try:
            if request.user.is_authenticated():
                if request.user.is_staff:
                    feedback = Feedback.objects.get(pk=fid)
                else:
                    feedback = Feedback.objects.get(Q(pk=fid,user=request.user) | Q(pk=fid,email=request.user.email))
            else:
                if (request.REQUEST.get('token') == None):
                    redirect = reverse('qa_feedback_id', args=[fid])
                    login_url = '%s?redirect=%s' % (reverse("index"), redirect)
                    return HttpResponseRedirect(login_url)
                feedback = Feedback.objects.get(pk=fid, token=token)
            test_results = TestEngineResult.objects.filter(test_file__in=feedback.test_files.all()).order_by("-started")
            # compare additional and attached files
            fileset = prepare_comparation(feedback)
            if request.user.is_staff:
                template = "qa/feedback_id_staff.html"
            else:
                template = "qa/feedback_id_user.html"
        except:
            logger.error(traceback.format_exc())
        if feedback is None:
            raise Http404()
        
        geo = get_lng_and_lat(feedback.ip_address)
        
        format = None
        if feedback.test_files.all().count() > 0:
            if feedback.selected_file is not None and feedback.selected_file != "":
                try:
                    format = feedback.test_files.get(file_name=feedback.selected_file).file_format.id
                except:
                    pass
            else:
                try:
                    format = feedback.test_files.all()[0].file_format.id
                except:
                    pass

        # Check if action
        if request.method == 'POST':
            if action == 'add_comment':
                comment_form = CommentForm(data=request.REQUEST.copy())
                if comment_form.is_valid():
                    if (request.user.is_authenticated() and feedback.user is not None and feedback.user.id == request.user.id) or \
                        (not request.user.is_authenticated() and feedback.email == request.session.get('email')):
                        feedback.comment = request.REQUEST.get('comment')
                        feedback.save()    
                    else:
                        request.session['error'] = "Comment cannot be created."
                        logger.error("Comment cannot be created.")
                    logger.debug("Comment was created successful.")
                    return create_response(request)
                else:
                    logger.error(user_comment_form.errors.as_text())
            # Since the status_update POST now also contains 'comment' from StatusForm, 
            # we can handle that here AND go on to handle status_update below
            elif action == 'add_user_comment' or action == "status_update":
                user_comment_form = UserCommentForm(data=request.REQUEST.copy())
                if user_comment_form.is_valid():
                    temp_form = user_comment_form.save(commit=False)
                    if request.user.is_authenticated(): 
                        temp_form.user = request.user
                    temp_form.save()
                    comment = temp_form
                    feedback.user_comment.add(comment)
                    feedback.save()
                    request.session['error'] = "Comment was created successful."
                    logger.debug("Comment was created successful.")
                    
                    try:
                        notify(feedback=feedback, comment=comment, email_template="comment_message")
                        logger.debug("Notification for comment_message")
                    except:
                        logger.error("NOTIFICATION NOT SENT")
                        logger.error(traceback.format_exc())
                    if action == 'add_user_comment':
                        return create_response(request)
                else:
                    logger.error(user_comment_form.errors.as_text())

            if action == "status_update":
                if request.user.is_staff:
                    status_form = StatusForm(data=request.REQUEST.copy())
                    if status_form.is_valid():
                        try:
                            feedback.status = FeedbackStatus.objects.get(pk=status_form.data.get('status'))
                            feedback.save()
                            logger.debug("Feedback '%i' was updated" % (feedback.id))
                            #try:
                            #    notify(feedback=feedback, email_template="status_message")
                            #    logger.debug("Notification for status_message")
                            #except:
                            #    logger.error("NOTIFICATION NOT SENT")
                            #    logger.error(traceback.format_exc())
                            request.session['error'] = "Status was changed successful."
                        except:
                            logger.error(traceback.format_exc())
                            request.session['error'] = "Status cannot be changed."
                        return create_response(request)
                    else:
                        logger.error(status_form.errors.as_text())
                else:
                    logger.error("Only staff can change the status.")
        else:
            if request.user.is_staff:
                status_form = StatusForm(data={'status':feedback.status.id})
            
            if feedback.comment is not None and len(feedback.comment) > 0:
                if request.user.is_authenticated() and feedback.user is not None and feedback.user.id == request.user.id:
                    comment_form = CommentForm(data={'comment':feedback.comment})
                elif not request.user.is_authenticated() and feedback.email == request.session.get('email'):
                    comment_form = CommentForm(data={'comment':feedback.comment})
            else:
                if request.user.is_authenticated() and feedback.user is not None and feedback.user.id == request.user.id:
                    comment_form = CommentForm()
                elif not request.user.is_authenticated() and feedback.email == request.session.get('email'):
                    comment_form = CommentForm()
        
        if user_comment_form is None:
            user_comment_form = UserCommentForm()

    else:
        if request.REQUEST.get('page') is not None:
            try:
                page = int(request.REQUEST.get('page'))
                if page <= 0: 
                    page = 1
            except:
                page = 1
        else:
            page = 1

        offset = (page-1)*settings.PERPAGE
        limit = settings.PERPAGE+offset
        # all feedbacks
        if request.user.is_staff:
            template = "qa/feedback_staff.html"
            count = 0
            apps = AppType.objects.all()
            app_name = request.REQUEST.get('type')
            
            if request.REQUEST.get('do_filter') is None:
                from django.http import QueryDict
                q = QueryDict('', mutable=True)
                q.update({'date': (date.today()-timedelta(days=30)).strftime("%Y-%m-%d")})
                request.REQUEST.dicts += (q,)
            
            q_status = None
            q_date = None
            q_useremail = None
            q_text = None
            
            filter_form = FilterFeedbackForm(data=request.REQUEST.copy())
            if filter_form.is_valid():
                if request.REQUEST.get('status') is not None and request.REQUEST.get('status') != "":
                    q_status = FeedbackStatus.objects.get(pk=filter_form.data.get('status'))
                if request.REQUEST.get('date') is not None and request.REQUEST.get('date') != "":
                    try:
                        q_date = datetime(*(time.strptime(filter_form.data.get('date'), "%Y-%m-%d")[0:6]))
                    except:
                        logger.error(traceback.format_exc())
                        q_date = None
                if request.REQUEST.get('text') is not None and request.REQUEST.get('text') != "":
                    q_text = filter_form.data.get('text')
                if request.REQUEST.get('useremail') is not None and request.REQUEST.get('useremail') != "":
                    try:
                        q_useremail = Users.objects.get(email=filter_form.data.get('useremail'))
                    except:
                        q_useremail = filter_form.data.get('useremail')                
            else:
                filter_form = FilterFeedbackForm()
            
            args = list()
            if q_status is not None:
                params['status'] = str(q_status.id)
                args.append(Q(status=q_status))
            if q_date is not None:
                params['date'] = q_date.strftime("%Y-%m-%d")
                args.append(Q(creation_date__gte=q_date))
            if q_text is not None and q_text != "":
                params['text'] = q_text
                args.append(Q(app_version__contains=q_text) | Q(comment__contains=q_text) | Q(error__contains=q_text) | Q(selected_file__contains=q_text))
            if q_useremail is not None and q_useremail != "":
                params['useremail'] = q_useremail
                args.append(Q(email__contains=q_useremail) | Q(user__email__contains=q_useremail) | Q(user__username__contains=q_useremail) | Q(user__first_name__contains=q_useremail) | Q(user__last_name__contains=q_useremail))
            if app_name is not None:
                args.append(Q(app_name=app_name))
            
            if len(args) > 0:
                count = Feedback.objects.filter(*args).count()
                feedback = Feedback.objects.filter(*args).order_by("-id")[offset:limit]
            else:
                count = Feedback.objects.all().count()
                feedback = Feedback.objects.all().order_by("-id")[offset:limit]
            
            paging = doPaging(page, settings.PERPAGE, count,  settings.PERPAGE)
        elif request.user.is_authenticated():
            template = "qa/feedback_user.html"            
            feedback = Feedback.objects.filter(Q(user=request.user) | Q(email=request.user.email))
        else:
            try:
                feedback = Feedback.objects.filter(token=token)
            except:
                logger.error(traceback.format_exc())
        
        if feedback is None:
            raise Http404()
    
    if len(params.keys()) > 0:
        params = "&".join([("%s=%s" % (k,v)) for k,v in params.items()])
    context = {'error':error, 'app_name':app_name, 'paging':paging, 'params':params, 'login_form':login_form, 'apps':apps, 'feedback':feedback, 'comment_form':comment_form, 'status_form':status_form, 'filter_form':filter_form, 'user_comment_form':user_comment_form, 'format':format, 'test_results':test_results, 'fileset':fileset, 'geo':geo}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def feedback_action(request, action, **kwargs):
    error = check_if_error(request)
    logger.debug(request.POST)
    if request.user.is_authenticated():
        if action == 'add':
            token = create_or_retrieve_token(request)
            if token is not None:
                try:
                    feedback = Feedback.objects.get(token=token)
                except:
                    error = "This feedback does not exist."
                else:
                    if feedback.user is None:
                        feedback.user = request.user
                        feedback.save()
                        error = "Feedback %i added to your list." % (feedback.id)
                    else:
                        error = "Feedback already asigned to you"
            else:
                error = "Token required."
                logger.error(error)
        elif action == 'test_result':
            if request.user.is_staff:
                feedback = Feedback.objects.get(pk=request.REQUEST.get('feedback_id'))
                if feedback.status.id != 3:
                    feedback.status = FeedbackStatus.objects.get(pk=3)
                    feedback.save()
                    logger.debug("Feedback status was changed")
                    try:
                        notify(feedback=feedback, email_template="status_message")
                        logger.debug("Notification for status_message")
                    except:
                        logger.error("NOTIFICATION NOT SENT")
                        logger.error(traceback.format_exc())
                selected_file = feedback.test_files.get(file_name=request.REQUEST.get('selected_file'))
                test_form = TestEngineResultForm(data=request.REQUEST.copy())
                if test_form.is_valid():
                    temp_form = test_form.save(commit=False)
                    temp_form.test_file = selected_file
                    temp_form.save()   
                    error = "Test result was saved."  
                else:
                    error = test_form.errors
            else:
                error = "Action '%s' not suppoted" % (action)
            logger.error(error)
            return HttpResponse(error)
        else:
            error = "Action '%s' not suppoted" % (action)

        request.session['error'] = error
        logger.error(error)
        # TODO might be request.path
        return HttpResponseRedirect(urlparse.urljoin(request.get_full_path(), '../'))       
    else:
        request.session['error'] = "First log in."
        return create_response(request)


def error_content(request, fid, **kwargs):
    template = "qa/error_content.html"
    content = None
    login_form = None
    is_html = False
    
    if request.user.is_authenticated():
        try:
            c = Feedback.objects.get(pk=fid)
            content = c.error
        except:
            logger.error(traceback.format_exc())
            raise Http404()
    else:
        login_form = LoginForm()
        token = create_or_retrieve_token(request)
        try:
            c = Feedback.objects.get(pk=fid, token=token)
            content = c.error
        except:
            logger.error(traceback.format_exc())
            raise Http404()
    
    try:
        if c.app_name.id == 6 or c.app_name.id == 7:
            is_html = True
    except:
        pass
    
    context = {'login_form':login_form, 'content':content, 'is_html':is_html}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def test_error_content(request, tid, **kwargs):
    template = "qa/test_error_content.html"
    content = None
    login_form = LoginForm()
    try:
        content = TestEngineResult.objects.get(pk=tid)
    except:
        logger.error(traceback.format_exc())
        raise Http404()
    
    context = {'login_form':login_form, 'content':content}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


#def test_file(request, fid, tid, action, **kwargs):
#    error = check_if_error(request)
#    if request.user.is_authenticated() and request.user.is_staff:
#        if action == 'delete':
#            try:
#                feedback = Feedback.objects.get(pk=fid)
#                feedback.test_files.remove(tid)
#            except:
#                logger.error(traceback.format_exc())
#                request.session['error'] = "File cannot be deleted."
#                raise AttributeError("File cannot be deleted.")
#            return HttpResponseRedirect("/qa/feedback/%s/" % fid)
#        else:
#            pass
#    else:
#        request.session['error'] = "File cannot be deleted."
#    return create_response(request)
    

def ticket(request, action, fid, tid=None, **kwargs):
    error = check_if_error(request)
    logger.debug(request.POST)
    if request.user.is_authenticated() and request.user.is_staff:
        template = "qa/ticket.html"
        ticket_form = None
        if action == 'new':
            feedback = Feedback.objects.get(pk=fid)
            cc = feedback.user and feedback.user.email or feedback.email
            if feedback.comment:
                description = '[%s%s]\n[[BR]]\nComment: %s\n[[BR]]\n{{{\n%s\n}}}' % (settings.APPLICATION_HOST, reverse(viewname="qa_feedback_id", args=[fid]), feedback.comment, feedback.error)
            else:
                description = '[%s%s]\n[[BR]]\n{{{\n%s\n}}}' % (settings.APPLICATION_HOST, reverse(viewname="qa_feedback_id", args=[fid]), feedback.error)
            ticket_form = TicketForm(initial={'summary':'BUG:Feedback %s' % (fid), 'description': description, 'cc':cc})
        elif action == 'add':
            ticket_form = ExistingTicketForm(initial={'comment': '[%s%s]' % (settings.APPLICATION_HOST, reverse(viewname="qa_feedback_id", args=[fid]))})
        elif action == 'save':
            ticket = request.REQUEST.get('ticket')
            if ticket is not None:
                ticket_form = ExistingTicketForm(data=request.REQUEST.copy(), initial={'fid':fid})
                if ticket_form.is_valid():
                    temp_form = ticket_form.save(commit=False)
                    comment = request.REQUEST.get('comment')
                    error = add_comment(ticket, comment, temp_form.system)
                    
                    temp_form.save()
                    ticket = temp_form
                    feedback = Feedback.objects.get(pk=fid)
                    feedback.ticket.add(ticket)
                    feedback.save()
                    
                    if error == ticket:                        
                        error = "Ticket was added."
                    else:
                        error = "Ticket was added but the following error occured: \"%s\"." % error
                    request.session['error'] = error
                    logger.error(error)
                    # TODO might be request.path
                    return HttpResponseRedirect(reverse(viewname="qa_feedback_id", args=[fid]))
            else:
                ticket_form = TicketForm(data=request.REQUEST.copy())
                if ticket_form.is_valid():
                    temp_form = ticket_form.save(commit=False)
                    summary = request.REQUEST.get('summary')
                    description = request.REQUEST.get('description')
                    owner = User.objects.get(pk=int(request.REQUEST.get('owner'))).username
                    cc = request.REQUEST.get('cc')
                    ticket_id = create_ticket(summary, description, temp_form.system, owner=owner, cc=cc)
                    if ticket_id is not None:
                        temp_form.ticket = ticket_id
                        temp_form.save()
                        ticket = temp_form
                        feedback = Feedback.objects.get(pk=fid)
                        feedback.ticket.add(ticket)
                        feedback.save()
                        error = "Ticket was created." 
                    else:
                        error = "Ticket was not created." 
                    request.session['error'] = error
                    logger.error(error)
                    # TODO might be request.path
                    return HttpResponseRedirect(reverse(viewname="qa_feedback_id", args=[fid]))
        else:
            error = "Action '%s' not suppoted" % (action)
        
        context = {'ticket_form':ticket_form, 'fid':fid}
        t = get_template(template)
        c = Context(request, context)
        rsp = t.render(c)
        return HttpResponse(rsp)      
    else:
        request.session['error'] = "First log in."
        return create_response(request)


def metadata_validator(request, build_number, **kwargs):
    error = "Done"
    logger.debug("Metadata validator build %s is saving results." % build_number)
    
    try:
        TestNGXML.objects.get(hudson_build=build_number)
    except TestNGXML.DoesNotExist:
        
        junit_result = os.path.join(os.path.join(os.path.join(os.path.join(os.path.dirname(settings.OME_HUDSON_PATH), 'omero-metadata-validator'), 'builds'), build_number), 'junitResult.xml').replace('\\','/')
        testng_file = os.path.join(os.path.join(os.path.join(os.path.join(os.path.join(os.path.join(os.path.join(os.path.join(os.path.dirname(settings.OME_HUDSON_PATH), 'omero-metadata-validator'), 'workspace'), 'trunk'), 'components'), 'tools'), 'OmeroImporter'), 'target'), 'testng.xml').replace('\\','/')

        dir_path = os.path.join(settings.TESTNG_ROOT).replace('\\','/')
        logger.debug("Files '%s' and '%s' are being saving in '%s'." % (junit_result, testng_file, dir_path))
        if not os.path.isdir(dir_path):
            try:
                os.mkdir(dir_path)
                logger.debug("Target path was created.")
            except Exception, x:
                logger.debug("Target path could not be created.")
                logger.error(traceback.format_exc())
                import sys
                exctype, value = sys.exc_info()[:2]
                raise exctype, value

        if os.path.isfile (junit_result) and os.path.isfile (testng_file): 
            junit_result_copy = os.path.join(os.path.dirname(settings.TESTNG_ROOT), build_number + '-junitResult.xml').replace('\\','/')
            testng_file_copy = os.path.join(os.path.dirname(settings.TESTNG_ROOT), build_number + '-testng.xml').replace('\\','/')
            shutil.copy(junit_result, junit_result_copy)
            shutil.copy(testng_file, testng_file_copy)

            if os.path.isfile (junit_result_copy) and os.path.isfile (testng_file_copy):
                logger.debug("Metadata-validation results were copied successful.")

                fd = open(testng_file_copy)           
                textng_xml = fd.read()
                root = XML(textng_xml)
                fd.close()

                parameters = root.findall("./parameter")
                for param in parameters:
                   if param.get("name") == "omero_revision":
                       omero_build = param.get("value")
                       logger.debug("omero_revision: %s" % omero_build)
                   elif param.get("name") == "bioformats_revision":
                       bioformats_build = param.get("value")
                       logger.debug("bioformats_build: %s" % bioformats_build)

                fd2 = open(junit_result_copy)           
                junit_xml = fd2.read()
                root = XML(junit_xml)
                fd2.close()

                suites = root.find("suites").findall("./suite")
                logger.debug("suites: %i" % len(suites))
                for suite in suites:
                    file_path = suite.find("name").text
                    logger.debug("file_path: %s" % file_path)
                    try:
                        test_file = TestFile2.objects.get(file_path=file_path)
                        logger.debug("Test file '%s' already exist." % file_path)
                    except TestFile2.DoesNotExist:
                        test_file = TestFile2(file_path=file_path)
                        test_file.save()
                        logger.debug("Test file '%s' was created." % file_path)

                    test_results = list()
                    cases = suite.find("cases").findall("./case")
                    logger.debug("cases: %i" % len(cases))
                    for case in cases:

                        try:
                            error_stack = case.find("errorStackTrace").text
                            result = False
                            failed_since = case.find("failedSince").text

                            test_name = case.find("testName").text
                            class_name = case.find("className").text
                            logger.debug("Test '%s %s'" % (test_name, class_name))

                            try:
                                test = MetadataTest.objects.get(test_name=test_name, class_name=class_name)
                                logger.debug("Metadata test '%s' already exist." % test)
                            except MetadataTest.DoesNotExist:
                                test = MetadataTest(test_name=test_name)
                                test.save()
                                logger.debug("Metadata test '%s' was created." % test)

                            mtest = MetadataTestResult(test=test, result=result, failed_since=failed_since, error=error_stack)
                            mtest.save()
                            test_results.append(mtest)
                        except:
                            pass

                    test_results = test_results + list(test_file.test_result.all())
                    test_file.test_result = test_results
                    test_file.save()

                testng = TestNGXML(junit_result=junit_result_copy, testng_file=testng_file_copy, hudson_build=build_number, bioformats_build=bioformats_build, omero_build=omero_build)
                testng.save()        

                junit = JUnitResult(xml_file=testng, test_file=test_file)
                junit.save()      

            else:
                error = "Files could not being copied."
                logger.debug("Files could not being copied.")
        else:
            error = "Source files do not exist."
            logger.debug("Source files do not exist.")
            
    else:
        error = "Build %s was already saved" % build_number
        logger.debug("Build %s was saved" % build_number)

    return HttpResponse(error)
        
