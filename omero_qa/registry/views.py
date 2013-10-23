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
import time
import base64
import os
import random
import re 
from random import choice
import urlparse
from cStringIO import StringIO
from itertools import *
from datetime import datetime, date, timedelta

from pygeoip import GeoIP, STANDARD, MEMORY_CACHE

UPGRADE_CHECK_URL = "http://www.openmicroscopy.org/site/support/omero4/sysadmins/UpgradeCheck.html"

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
from django.db import connection, transaction
from django.core import serializers
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.cache import cache

from omero_qa.feedback.views import handlerInternalError
from omero_qa.registry.models import Agent, IP, Hit, Version, Continents, ContinentsForm, AgentForm, DemoAccountForm
from omero_qa.qa.models import TestFile
from omero_qa.qa.forms import LoginForm
from omero_qa.qa.views import check_if_error
from omero_qa.registry.delegator import *
    
logger = logging.getLogger('views-registry')

logger.info("INIT '%s'" % os.getpid())

try:
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import numpy as np
    import matplotlib.pyplot as plt
    from pylab import *    
except:
    logger.error(traceback.format_exc())


connectors = {}

### VIEWS ###

def demo_account(request, action=None, **kwargs):
    error = check_if_error(request)
    template = "registry/enquiry.html"
    
    thanks = None
    demo_form = None
    if action == "enquiry":
        logger.info("Demo account data sent:")
        logger.info(request.POST)
        demo_form = DemoAccountForm(data=request.REQUEST.copy())
        if demo_form.is_valid():
            demo_form.save()
            title = 'OMERO.qa - Demo account'            
            text_content = " \n".join([("%s: '%s'" % (key.replace("_", " "),val)) for key,val in request.POST.iteritems()])
            html_content = "<br/>".join([("%s: '%s'" % (key.replace("_", " "),val)) for key,val in request.POST.iteritems()])
            recipients = ["demo-requests@openmicroscopy.org.uk"]
            try:
                msg = EmailMultiAlternatives(title, text_content, settings.SERVER_EMAIL, recipients)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                logger.info('Email was sent.')
            except:
                logger.error(traceback.format_exc())
            error = "Thank you for your interest in an OMERO Demo Account - one of our consultants will be in contact with you shortly. Please be patient as it may take a few days to process your application after we receive it."
            request.session['error'] = error
            logger.error(error)
            # TODO might be request.path
            return HttpResponseRedirect(reverse(viewname="registry_demoaccount", args=['thanks']))
    elif action == "thanks":
        if error:
            thanks = error
        else:
            demo_form = DemoAccountForm()
    else:
        demo_form = DemoAccountForm()
    
    login_form = LoginForm()
    context = {"login_form":login_form, 'demo_form':demo_form, 'thanks':thanks}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def big_geomap(request, **kwargs):        
    template = "registry/big_geomap.html"
    
    center = None
    zoom = None
    ips = None
    cont_form = None
    agent_form = None
    continent = request.REQUEST.get('continent')
    agent = request.REQUEST.get('agent')
    if continent is not None:
        cont_form = ContinentsForm(data=request.REQUEST.copy())
        if cont_form.is_valid():
            cont = Continents.objects.get(pk=continent)
            logger.debug("N: '%s', S: '%s', W: '%s', E: '%s'" % (cont.n, cont.s, cont.w, cont.e))
            
            if continent == "1":
                logger.debug("Every continents...")
                center = (cont.centerx, cont.centery)
                zoom = cont.zoom
            else:                
                center = (cont.centerx, cont.centery)
                zoom = cont.zoom
        agent_form = AgentForm()
    elif agent is not None:
        agent_form = AgentForm(data=request.REQUEST.copy())
        if agent_form.is_valid():
            ag = Agent.objects.get(pk=agent)            
            center = (0, 30)
            zoom = 2
        cont_form = ContinentsForm()
    else:
        cont_form = ContinentsForm()
        agent_form = AgentForm()
    login_form = LoginForm()
    context = {"cont_form":cont_form, 'agent_form':agent_form, 'continent':continent, 'agent':agent, 'center':center, "zoom":zoom, "login_form":login_form}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def geomap(request, **kwargs):        
    template = "registry/geomap.html"
    
    center = None
    zoom = None
    ips = None
    cont_form = None
    agent_form = None
    continent = request.REQUEST.get('continent')
    agent = request.REQUEST.get('agent')
    if continent is not None:
        cont_form = ContinentsForm(data=request.REQUEST.copy())
        if cont_form.is_valid():
            cont = Continents.objects.get(pk=continent)
            logger.debug("N: '%s', S: '%s', W: '%s', E: '%s'" % (cont.n, cont.s, cont.w, cont.e))
            
            if continent == "1":
                logger.debug("Every continents...")
                center = (cont.centerx, cont.centery)
                zoom = cont.zoom
            else:                
                center = (cont.centerx, cont.centery)
                zoom = cont.zoom
        agent_form = AgentForm()
    elif agent is not None:
        agent_form = AgentForm(data=request.REQUEST.copy())
        if agent_form.is_valid():
            ag = Agent.objects.get(pk=agent)            
            center = (0, 30)
            zoom = 2
        cont_form = ContinentsForm()
    else:
        cont_form = ContinentsForm()
        agent_form = AgentForm()
    login_form = LoginForm()
    context = {"cont_form":cont_form, 'agent_form':agent_form, 'continent':continent, 'agent':agent, 'center':center, "zoom":zoom, "login_form":login_form}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def get_markers_as_xml(request):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cache_continent = request.REQUEST.get('continent') is not None and ("continent%s" % request.REQUEST.get('continent')) or None
    cache_agent = request.REQUEST.get('agent') is not None and ("agent%s" % request.REQUEST.get('agent')) or None
    ips = list()
    data = None
    
    if cache_continent is not None:
        data = cache.get(cache_continent)
        logger.info("XML data for '%s' loaded from chache" % cache_continent)
    elif cache_agent is not None:
        data = cache.get(cache_agent)
        logger.info("XML data for '%s' loaded from chache" % cache_agent)
        
    if data is None:
        if request.REQUEST.get('continent') is not None:
            cont = Continents.objects.get(pk=request.REQUEST.get('continent'))
            logger.debug("N: '%s', S: '%s', W: '%s', E: '%s'" % (cont.n, cont.s, cont.w, cont.e))
            cursor = connection.cursor()

            if request.REQUEST.get('continent') == "1":
                logger.debug("Every continents...")
                allips = list(IP.objects.exclude(latitude=None).exclude(longitude=None))      
                logger.debug("Total number of IPs is: %i" % len(allips))

                query = 'SELECT DISTINCT registry_hit.ip_id, registry_ip.ip, registry_ip.latitude, registry_ip.longitude, registry_agent.display_name \
                FROM registry_ip, registry_agent, registry_hit \
                WHERE registry_hit.ip_id = registry_ip.id \
                AND registry_hit.agent_id = registry_agent.id \
                AND (registry_ip.longitude is not null AND registry_ip.latitude is not null ) \
                ORDER BY registry_hit.ip_id ASC'
                try:
                    cursor.execute(query)
                except:
                    logger.debug(traceback.format_exc())
                logger.debug("query executed")
            else:
                allips = list(IP.objects.filter(latitude__gte=cont.s, latitude__lte=cont.n,\
                                            longitude__gte=cont.w, longitude__lte=cont.e).exclude(ip__startswith="10."))
                logger.debug("Total number of IPs is: %i" % len(allips))

                query = 'SELECT DISTINCT registry_hit.ip_id, registry_ip.ip, registry_ip.latitude, registry_ip.longitude, registry_agent.display_name \
                FROM registry_ip, registry_agent, registry_hit \
                WHERE registry_hit.ip_id = registry_ip.id \
                AND registry_hit.agent_id = registry_agent.id \
                AND (registry_ip.longitude <= %s AND registry_ip.longitude >= %s \
                AND registry_ip.latitude >= %s AND registry_ip.latitude <= %s ) \
                ORDER BY registry_hit.ip_id ASC'
                try:
                    cursor.execute(query, [cont.e, cont.w, cont.s, cont.n])
                except:
                    logger.debug(traceback.format_exc())
                logger.debug("query executed")
            temp = None
            try:
                logger.debug("building objects IPforXML")
                result = cursor.fetchall()
                for row in result:
                    if temp is not None and temp.id == row[0]:
                        p = ips[len(ips)-1]
                        ips.remove(p)
                        p.agent_name = "%s, %s" %  (p.agent_name, row[4])
                    else:
                        p = IPforXML(id=row[0], ip=row[1], latitude=row[2], longitude=row[3], agent_name=row[4])
                        temp = p

                    flag = False
                    for ip in allips:
                        if ip.id == row[0]:
                            allips.remove(ip)
                            flag = True
                        if flag:
                            break
                    ips.append(p)
            except:
                logger.debug(traceback.format_exc())

            # add rest of ips
            for ip in allips:
                p = IPforXML(id=ip.id, ip=ip.ip, latitude=ip.latitude, longitude=ip.longitude, agent_name="unknown")
                ips.append(p)
            logger.debug("IPS: %s" % len(ips))
        elif request.REQUEST.get('agent') is not None:
            agent = Agent.objects.get(pk=request.REQUEST.get('agent'))
            logger.debug("Agent '%s' on every continents..." % agent.agent_name)
            cursor = connection.cursor()

            query = """SELECT DISTINCT registry_hit.ip_id, registry_ip.ip, registry_ip.latitude, registry_ip.longitude, registry_agent.display_name \
            FROM registry_ip, registry_agent, registry_hit \
            WHERE registry_hit.ip_id = registry_ip.id \
            AND registry_hit.agent_id = registry_agent.id \
            AND (registry_ip.longitude is not null AND registry_ip.latitude is not null ) \
            AND registry_hit.agent_id = %s \
            ORDER BY registry_hit.ip_id ASC"""
            try:
                cursor.execute(query, [agent.id])
            except:
                logger.debug(traceback.format_exc())

            temp = None
            try:
                result = cursor.fetchall()
                for row in result:
                    if temp is not None and temp.id == row[0]:
                        p = ips[len(ips)-1]
                        ips.remove(p)
                        p.agent_name = "%s, %s" %  (p.agent_name, row[4])
                    else:
                        p = IPforXML(id=row[0], ip=row[1], latitude=row[2], longitude=row[3], agent_name=row[4])
                        temp = p
                    ips.append(p)
            except:
                logger.debug(traceback.format_exc())
            logger.debug("IPS: %s" % len(ips))

        data = serializers.serialize('xml', ips, fields=('latitude', 'longitude', 'agent_name'))
        if cache_continent is not None:
            cache.set(cache_continent, data, settings.CACHE_TIMEOUT)
        elif cache_agent is not None:
            cache.set(cache_agent, data, settings.CACHE_TIMEOUT)
            
    return HttpResponse(data, mimetype='application/xml')


def hit(request):
    stable_omero_downloads = 'http://downloads.openmicroscopy.org/latest-stable/omero'
    agent = None
    try:
        agt = request.META.get('HTTP_USER_AGENT', '')
        if agt is not None and agt.startswith("OMERO."):
            try:
                agent = Agent.objects.get(agent_name=agt)
            except Agent.DoesNotExist:
                return HttpResponseRedirect(UPGRADE_CHECK_URL)
            except:
                logger.error(traceback.format_exc())
                return HttpResponseRedirect(UPGRADE_CHECK_URL)
        else:
                return HttpResponseRedirect(UPGRADE_CHECK_URL)
    except:
        logger.error(traceback.format_exc())
        return HttpResponseRedirect(UPGRADE_CHECK_URL)
    logger.debug("Agent %s" % agent)
    
    agent_version = ''
    update = None
    try:
        agent_version = request.REQUEST.get('version')
        ver = Version.objects.get(pk=1)
        if agent_version is not None:
            try:
                regex = re.compile("^.*?[-]?(\\d+[.]\\d+([.]\\d+)?)[-]?.*?$")

                agent_cleaned = regex.match(agent_version).group(1)
                agent_split = agent_cleaned.split(".")

                local_cleaned = regex.match(ver.version).group(1)
                local_split = local_cleaned.split(".")

                rv = (agent_split < local_split)
            except:
                rv = True
            if rv:
                update = 'Please upgrade to %s. See %s for the latest version.' % (ver, stable_omero_downloads)
        else:
            update = 'Please upgrade to %s. See %s for the latest version.' % (ver, stable_omero_downloads)
    except:
        logger.debug(traceback.format_exc())
    logger.debug("Agent version %s" % agent_version)
    
    ip = None
    try:
        real_ip = None
        try:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs. The
            # client's IP will be the first one.
            # http://code.djangoproject.com/ticket/3872
            real_ip = request.META['HTTP_X_FORWARDED_FOR']
            logger.debug("HTTP_X_FORWARDED_FOR: %s" % real_ip) 
            real_ip = real_ip.split(",")[-1].strip()
        except KeyError:
            real_ip = request.META.get('REMOTE_ADDR')
            
        if real_ip is not None:
            try:
                ip = IP.objects.get(ip=real_ip)
            except IP.DoesNotExist:
                latitude = None
                longitude = None
                country = None
                geoip = GeoIP(settings.GEODAT, STANDARD)
                gir = geoip.record_by_addr(real_ip)
                if gir is not None:
                    latitude = gir["latitude"]
                    longitude = gir["longitude"]
                geoip = GeoIP(settings.GEOIP, MEMORY_CACHE)
                country = geoip.country_name_by_addr(real_ip)
                    
                logger.debug("IP: %s, latitude: '%s', longitude: '%s'" % (real_ip, latitude, longitude))
                ip = IP(ip=real_ip, latitude=latitude, longitude=longitude, country=country)
                ip.save()
    except Exception, x:
        logger.debug(traceback.format_exc())
        raise x
    logger.debug("IP %s" % ip)
    
    if agent.id == 5:
        try:
            from datetime import datetime
            now = datetime.now()
            h = Hit.objects.filter(ip=ip, creation_date__gte=now.strftime("%Y-%m-%d 00:00:00.000000")).count()
            if h > 0:
                logger.debug("To many hits from the ip %s by the agent %s" % (ip,agent.agent_name))
                return HttpResponse()
            else:
                logger.debug("Hits from the ip %s hasn't been logged yet by the agent %s" % (ip,agent.agent_name))
        except Exception, x:
            logger.debug(traceback.format_exc())
    
    poll = None
    try:
        p = request.REQUEST.get('poll')
        if p is not None:
            poll = int(p)
    except:
        logger.debug(traceback.format_exc())
    logger.debug("Poll %s" % poll)
    
    java_vendor = request.REQUEST.get('java.vm.vendor')
    logger.debug("Java vendor %s" % java_vendor)
    
    java_version = request.REQUEST.get('java.runtime.version')
    logger.debug("Java version %s" % java_version)
    
    python_version = request.REQUEST.get('python.version')
    logger.debug("Python version %s" % python_version)
    
    python_compiler = request.REQUEST.get('python.compiler')
    logger.debug("Python compiler %s" % python_compiler)
    
    python_build = request.REQUEST.get('python.build')
    logger.debug("Python build %s" % python_build)
    
    os_name = request.REQUEST.get('os.name')
    logger.debug("OS name %s" % os_name)
    
    os_arch = request.REQUEST.get('os.arch')
    logger.debug("OS arch %s" % os_arch)
    
    os_version = request.REQUEST.get('os.version')
    logger.debug("OS version %s" % os_version)
    
    header = str(request.META)
    logger.debug("HttpRequest.META %s" % header)
    
    try:
        save_hit(ip=ip, agent=agent, agent_version=agent_version, poll=poll, os_name=os_name, os_arch=os_arch, os_version=os_version, java_vendor=java_vendor, java_version=java_version, python_version=python_version, python_compiler=python_compiler, python_build=python_build, header=header)
    except Exception, x:
        logger.debug(traceback.format_exc())
        HttpResponse(x)
    
    if update is not None:
        logger.debug("Update %s" % update)
        return HttpResponse(update)
    else:
        return HttpResponse()
    

@login_required
def local_statistic(request):
    template = "registry/local_statistic.html"
    
    stats = int(request.REQUEST.get('stats'))
    agents = Agent.objects.all()
    result = None
    details = dict()
    column_names = list()
    
    try:
        if stats == 1:
            result = cache.get('last_30_days')
            if result is None:
                s = Statistics(agents)
                result = s.last_30_days()
                cache.set('last_30_days', result, settings.CACHE_TIMEOUT)
        elif stats == 2:
            result = cache.get('weekly')
            if result is None:
                s = Statistics(agents)
                result = s.weekly()
                cache.set('weekly', result, settings.CACHE_TIMEOUT)
        elif stats == 3:
            result = cache.get('by_country')
            if result is None:
                s = Statistics(agents)
                result = s.by_country()
                cache.set('by_country', result, settings.CACHE_TIMEOUT)
        elif stats == 4:
            result = cache.get('by_ip')
            if result is None:
                s = Statistics(agents)
                result = s.by_ip()
                cache.set('by_ip', result, settings.CACHE_TIMEOUT)
        elif stats == 5:
            full_res = cache.get('by_os')
            if full_res is None:
                s = Statistics(agents)
                full_res = s.by_os()
                cache.set('by_os', full_res, settings.CACHE_TIMEOUT)
            result = full_res[0]
            details['Operating System (Detailed)'] = full_res[1]
        elif stats == 6:
            full_res = cache.get('by_env')
            if full_res is None:
                s = Statistics(agents)
                full_res = s.by_env()
                cache.set('by_env', full_res, settings.CACHE_TIMEOUT)
            details['Java version'] = full_res[0]
            details['Python version'] = full_res[1]
        elif stats == 7:
            template = "registry/demo_statistic.html"
            #result = cache.get('demo_serv')
            #if result is None:
            s = None
            if connectors.has_key('demo'):
                s = connectors['demo']
            else:
                s = DemoStatistics()
                connectors['demo'] = s
            s.ping()            
            result = s.demostats()
            #cache.set('demo_serv', result, settings.CACHE_TIMEOUT)
                      
        if stats != 5 and stats != 6 and stats != 7:
            for row in result[0][1]:
                column_names.append(row[0])
        
    except Exception, x:
        logger.debug(traceback.format_exc())
        HttpResponse(x)
    
    login_form = LoginForm()
    context = {"login_form":login_form, 'stats':stats, 'result':result, 'details':details, 'column_names':column_names}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def local_statistic_chart(request):
    template = "registry/local_statistic.html"
    
    stats = int(request.REQUEST.get('stats'))
    agents = Agent.objects.all()
    result = None
    title = 'Omero statistic'
    try:
        if stats == 1:
            title = 'Last 30 days.'
            full_res = cache.get('last_30_days')
            if full_res is None:
                s = Statistics(agents)
                full_res = s.last_30_days()
                cache.set('last_30_days', full_res, settings.CACHE_TIMEOUT)
            result = full_res
        elif stats == 2:
            title = 'Weekly'
            full_res = cache.get('weekly')
            if full_res is None:
                s = Statistics(agents)
                full_res = s.weekly()
                cache.set('weekly', full_res, settings.CACHE_TIMEOUT)
            
            result = full_res
        elif stats == 3:
            title = 'The most popular Countries.'
            full_res = cache.get('by_country')
            if full_res is None:
                s = Statistics(agents)
                full_res = s.by_country()
                cache.set('by_country', full_res, settings.CACHE_TIMEOUT)
            
            result = {'Others': 0 }
            for res in full_res:
                for r in res[1]:
                    if r[0] == 'Total':
                        if r[2] > 3:
                            result[res[0]] = r[2]
                        else:
                            if r[2] is not None:
                                result['Others'] += r[2]
        elif stats == 5:
            title = 'The most popular Operating Systems.'
            full_res = cache.get('by_os')
            if full_res is None:
                s = Statistics(agents)
                full_res = s.by_os()
                cache.set('by_os', full_res, settings.CACHE_TIMEOUT)
            
            result = {'Others': 0 }
            for res in full_res[0]:
                if res[2] > 1:
                    result[res[0]] = res[1]
                else:
                    result['Others'] += res[1]
        
    except Exception, x:
        logger.debug(traceback.format_exc())
        HttpResponse(x)
    
    # Draw piechart
    if result is None or len(result) == 0:
        return HttpResponse("No results.")
    try:
        if stats == 3 or stats == 5:
            # make a square figure and axes
            fig = plt.figure()
            ax = axes([0.1, 0.1, 0.8, 0.8])

            labels = result.keys()
            fracs = result.values()

            plt.pie(fracs, labels=labels, autopct='%1.1f%%', shadow=True)
            plt.title(title)
        elif stats == 1 or stats == 2:
            
            bars = dict()
            labels = list()
            maximum = 0
            for res in result:
                labels.insert(0, res[0])
                for a in agents:
                    for r in res[1]:
                        if r[0] == a.display_name :
                            if bars.has_key(a.display_name):
                                bars[a.display_name].insert(0,int(r[1]))
                            else:
                                bars[a.display_name] = [int(r[1])]
            
            fig = plt.figure()
            N = len(result)
            ind = np.arange(N)    # the x locations for the groups
            width = 0.35       # the width of the bars: can also be len(x) sequence
            for a in agents:
                plt.bar(ind, tuple(bars[a.display_name]),  width)
  
            plt.ylabel('Hits')
            plt.xlabel('Days')
            plt.title(title)
            plt.xticks(ind+width, tuple(labels), rotation=90)
            #plt.legend( (p1[0], p2[0]), ('Men', 'Women') )

            
            
            
        canvas = FigureCanvas(fig)
        imdata = StringIO()
        canvas.print_figure(imdata)
        return HttpResponse(imdata.getvalue(), mimetype='image/png')
    except:
        logger.debug(traceback.format_exc())
        return HttpResponse("Drawing chart error.")


def ip2country(request):
    ip = str(request.REQUEST.get('ip'))
    
    geoip = GeoIP(settings.GEOIP, MEMORY_CACHE)
    c = geoip.country_name_by_addr(ip)
    c+="; "
    whois = os.popen("whois %s 2>&1" % ip)
    file.close
    for ln in whois:
        '''
        inetnum:      134.36.0.0 - 134.36.255.255
        descr:        University of Dundee
        descr:        Dundee DD1 4HN
        descr:        Scotland
        netname:      DUNDEE-UNIV
        descr:        University of Dundee
        country:      GB
        '''
        if ln.startswith("inetnum") or ln.startswith("netname") or ln.startswith("descr"):
            c+=ln.split(":")[1].strip()+"; "
        if ln.startswith("country"):
            c+=ln.split(":")[1].strip()+"."
            break
        if len(c) > 400:
            break
        
    return HttpResponse(c)


def statistic(request):
    template = "registry/statistic.html"
    
    stats = request.REQUEST.get('stats')
    files, total, today, month = None, None, None, None
    if stats is None:
        today = date.today()
        beginning = "%s-%s-01" % (today.year, today.month) 
        total = total_results()
        today = custom_date_results()
        month = custom_date_results(beginning)

        from operator import itemgetter
        files = sorted(file_stat_percent().items())
    
    
    login_form = LoginForm()
    context = {'files':files, 'total':total, 'today':today, 'month':month, "login_form":login_form, 'stats':stats}
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def statistic_chart(request):
    today = date.today()
    beginning = "%s-%s-01" % (today.year, today.month)
    total = total_results()
    if total.get('files') == 0:
        return HttpResponse("No images.")
    today = custom_date_results()
    month = custom_date_results(beginning)

    N = 3
    totalMeans = (total['files'], total['results'], total['failure'])
    todayMeans = (today['files'], today['results'], today['failure'])
    monthMeans = (month['files'], month['results'], month['failure'])
    
    ind = np.arange(N)  # the x locations for the groups
    width = 0.15       # the width of the bars

    fig = plt.figure()
    plt.subplot(111)
    rects1 = plt.bar(ind, totalMeans, width, color='g')
    rects2 = plt.bar(ind+width, monthMeans, width, color='b')
    rects3 = plt.bar(ind+2*width, todayMeans, width, color='r')

    # add some
    plt.ylabel('Files')
    plt.title('')
    plt.xticks(ind+1.5*width, ('Uploaded', 'Tested', 'Failure') )

    plt.legend( (rects1[0], rects2[0], rects3[0]), ('Total', 'Month', 'Today') )

    def autolabel(rects):
        # attach some text labels
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                plt.text(rect.get_x()+rect.get_width()/2., height-3, '%d'%int(height),
                    ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    
    canvas = FigureCanvas(fig)
    
    imdata = StringIO()
    canvas.print_figure(imdata)
    return HttpResponse(imdata.getvalue(), mimetype='image/png')


def file_statistic_chart(request):
    total = file_stat()
    if len(total) == 0:
        return HttpResponse("No images.")
    try:
        # make a square figure and axes
        fig = plt.figure()
        ax = axes([0.1, 0.1, 0.8, 0.8])

        labels = total.keys()
        fracs = total.values()

        plt.pie(fracs, labels=labels, autopct='%1.1f%%', shadow=True)
        plt.title('File formats in testing')
        canvas = FigureCanvas(fig)
        imdata = StringIO()
        canvas.print_figure(imdata)
        return HttpResponse(imdata.getvalue(), mimetype='image/png')
    except:
        return HttpResponse("Drawing chart error.")

