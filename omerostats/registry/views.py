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

import traceback
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseServerError
from django.http import HttpResponseRedirect
from django.conf import settings
from django.template.loader import get_template
from django.template import RequestContext as Context
from django.contrib.auth import login as django_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Q
from django.db.models import Count

from omerostats.registry.forms import LoginForm
from omerostats.registry.models import IP, Hit, Continent
from omerostats.registry.models import Version, AgentVersion
from omerostats.registry.models import MapForm, VersionForm
from omerostats.registry.delegator import IPforXML, month_year_table
from omerostats.registry.delegator import sorted_table

logger = logging.getLogger(__name__)

# VIEWS ###


@login_required
def logout_view(request):
    django_logout(request)
    logger.debug("User was logged out successfully.")
    return HttpResponseRedirect(reverse(viewname="index"))


@login_required
def index(request, **kwargs):
    template = "registry/index.html"
    context = {}

    defaultversion = Version.objects.get(pk=1)
    context['defaultversion'] = defaultversion

    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


def login(request, **kwargs):
    template = "registry/login.html"
    error = None
    context = {'next': request.REQUEST.get('next', None)}

    if request.method == 'POST':
        login_form = LoginForm(data=request.REQUEST.copy())
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    django_login(request, user)
                    logger.debug("User logged in successfully.")
                    return HttpResponseRedirect(request.GET['next'])
                else:
                    error = "User is not active."
                    logger.debug("User is not active.")
            else:
                error = "Wrong username or password."
                logger.debug("Wrong username or password.")
        else:
            logger.debug(login_form.errors.as_text())
    else:
        login_form = LoginForm()

    context['login_form'] = login_form

    context['error'] = error

    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


@login_required
def big_geomap(request, **kwargs):
    template = "registry/big_geomap.html"

    try:
        cont = Continent.objects.get(pk=request.REQUEST.get('continent'))
    except:
        cont = Continent.objects.get(name="Europe")
    initial = {
        "version": request.REQUEST.get('version'),
        "continent": cont,
        'country': request.REQUEST.getlist('country'),
        'agents': request.REQUEST.getlist('agent')
    }
    map_form = MapForm(initial=initial)

    context = {}
    context['map_form'] = map_form
    context['defaultversion'] = Version.objects.get(pk=1)
    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


@login_required
def get_markers_as_xml(request, **kwargs):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """

    mapform = MapForm(data=request.REQUEST.copy())
    if mapform.is_valid():

        ips = list()
        unresolved = list()

        data = {}
        args = list()

        startdate = mapform.cleaned_data['startdate']
        if startdate:
            args.append(Q(creation_date__gte=startdate))
            logger.debug("StartDate '%s'" % str(startdate))

        enddate = mapform.cleaned_data['enddate']
        if enddate:
            args.append(Q(creation_date__lte=enddate))
            logger.debug("EndDate '%s'" % str(enddate))

        agents = mapform.cleaned_data['agent']
        # agent is now mandatory
        # if not agents:
        #    agents = Agent.objects.all()
        agent_ids = tuple([a.id for a in agents])
        args.append(Q(agent__id__in=agent_ids))
        logger.debug("Agents '%s'" % str(agents))

        v = mapform.cleaned_data['version']
        if v and len(v) > 0:
            subargs = list()
            if v.startswith("5.0"):
                subargs.append(
                    (
                        Q(version__startswith=v) |
                        Q(version__startswith='4.5')
                    )
                )
            elif v.startswith("4.2"):
                subargs.append(
                    (
                        Q(version__startswith=v) |
                        Q(version__startswith='Beta-4.2')
                    )
                )
            elif v.startswith("4.1"):
                subargs.append(
                    (
                        Q(version__startswith=v) |
                        Q(version__startswith='Beta-4.1')
                    )
                )
            else:
                subargs.append(Q(version__startswith=v))
            agent_version = AgentVersion.objects.filter(*subargs)
            # agent_version_ids = tuple([a.id for a in agent_version])
            args.append(Q(agentversion__in=agent_version))
        # 5.0 AND (registry_hit.agent_version LIKE %s  OR
        # registry_hit.agent_version LIKE '4.5%%')
        # 4.1 or 4.2 AND (registry_hit.agent_version LIKE %s OR
        # registry_hit.agent_version LIKE 'Beta-4.1%%')

        continent = mapform.cleaned_data['continent']
        countries = mapform.cleaned_data['country']
        if continent or countries:
            if continent:
                logger.debug("Continent '%s'" % str(continent))

            country_ids = list()
            try:
                country_ids = tuple([c.id for c in countries])
                logger.debug("Countries '%s'" % str(countries))
            except:
                logger.debug(traceback.format_exc())
                pass

            if continent and country_ids:
                args.append(
                    (
                        Q(ip__continent__id=continent.id) |
                        Q(ip__country__in=country_ids)
                    )
                )
            elif continent:
                args.append(Q(ip__continent__id=continent.id))
            elif country_ids:
                args.append(Q(ip__country__in=country_ids))

        # ip adresses
        ip_address = IP.objects.exclude(ip__regex=settings.IPLOCALREGEX)
        args.append(Q(ip__in=ip_address))

        # main query
        result = Hit.objects \
            .values_list(
                'ip__id', 'ip__ip', 'ip__latitude', 'ip__longitude',
                'agent__display_name', 'ip__organisation__name') \
            .distinct() \
            .filter(*args)

        try:
            for row in result:
                ip_id, ip, latitude, longitude, agent_name, org = row
                p = IPforXML(
                    id=ip_id, ip=ip, latitude=latitude, longitude=longitude,
                    agent_name=agent_name, org=org)
                if latitude is not None and longitude is not None:
                    ips.append(p)
                else:
                    unresolved.append(p)
        except:
            logger.debug(traceback.format_exc())
        logger.debug("IPS: %s unresolved %s " % (len(ips), len(unresolved)))

        data = serializers.serialize(
            'json', ips, fields=('latitude', 'longitude', 'ip', 'org'))
        return HttpResponse(data, mimetype='application/json')
    else:
        return HttpResponseServerError(mapform.errors.as_text())


# STATS
@login_required
def local_statistic(request):
    template = "registry/local_statistic.html"
    version = request.REQUEST.get('version', None)
    initial = {'version': version}

    context = {}
    if request.method == "POST":
        versionform = VersionForm(initial=initial, data=request.REQUEST.copy())
        if versionform.is_valid():

            args = list()

            startdate = versionform.cleaned_data['startdate']
            if startdate:
                args.append(Q(creation_date__gte=startdate))
                logger.debug("StartDate '%s'" % str(startdate))

            enddate = versionform.cleaned_data['enddate']
            if enddate:
                args.append(Q(creation_date__lte=enddate))
                logger.debug("EndDate '%s'" % str(enddate))

            agents = versionform.cleaned_data['agent']
            # agent is now mandatory
            # if not agents:
            #    agents = Agent.objects.all()
            agent_ids = tuple([a.id for a in agents])
            args.append(Q(agent__id__in=agent_ids))
            logger.debug("Agents '%s'" % str(agents))

            v = versionform.cleaned_data['version']
            if v and len(v) > 0:
                subargs = list()
                if v.startswith("5.0"):
                    subargs.append(
                        (
                            Q(version__startswith=v) |
                            Q(version__startswith='4.5')
                        )
                    )
                elif v.startswith("4.2"):
                    subargs.append(
                        (
                            Q(version__startswith=v) |
                            Q(version__startswith='Beta-4.2')
                        )
                    )
                elif v.startswith("4.1"):
                    subargs.append(
                        (
                            Q(version__startswith=v) |
                            Q(version__startswith='Beta-4.1')
                        )
                    )
                else:
                    subargs.append(Q(version__startswith=v))
                agent_version = AgentVersion.objects.filter(*subargs)
                # agent_version_ids = tuple([a.id for a in agent_version])
                args.append(Q(agentversion__in=agent_version))
            # 5.0 AND (registry_hit.agent_version LIKE %s  OR
            # registry_hit.agent_version LIKE '4.5%%')
            # 4.1 or 4.2 AND (registry_hit.agent_version LIKE %s OR
            # registry_hit.agent_version LIKE 'Beta-4.1%%')

            ip_address = IP.objects.exclude(ip__regex=settings.IPLOCALREGEX)
            args.append(Q(ip__in=ip_address))
            # main query
            result = Hit.objects \
                .filter(*args) \
                .values(
                    'ip__domain__name',
                    'ip__organisation__name',
                    'agent__display_name') \
                .annotate(hit_total_count=Count('id')) \
                .annotate(hit_unique_count=Count('ip__id', distinct=True))

            stat_dict = dict()
            try:
                for row in result:
                    domain = row['ip__domain__name']
                    org = row['ip__organisation__name']
                    ag = row['agent__display_name']
                    counter = row['hit_total_count']
                    unique = row['hit_unique_count']
                    if org in stat_dict:
                        stat_dict[org][ag]["total"] = counter
                        stat_dict[org][ag]["unique"] = unique
                    else:
                        stat_dict[org] = dict()
                        stat_dict[org]["domain"] = domain
                        for a in agents:
                            if ag == a.display_name:
                                stat_dict[org][ag] = {
                                    "total": counter, "unique": unique}
                            else:
                                stat_dict[org][a.display_name] = {
                                    "total": None, "unique": None}
            except:
                logger.debug(traceback.format_exc())
            logger.debug("Organisations: %s" % (len(stat_dict.keys())))

            context['result'] = stat_dict
            context['agents'] = agents

    else:
        versionform = VersionForm(initial=initial)

    context['version'] = version
    context['defaultversion'] = Version.objects.get(pk=1)
    context['versionform'] = versionform

    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)


@login_required
def monthly_statistics(request):
    template = "registry/monthly_statistic.html"
    version = request.REQUEST.get('version', None)
    initial = {'version': version}

    context = {}
    if request.method == "POST":
        versionform = VersionForm(initial=initial, data=request.REQUEST.copy())
        if versionform.is_valid():

            args = list()

            startdate = versionform.cleaned_data['startdate']
            if startdate:
                args.append(Q(creation_date__gte=startdate))
                logger.debug("StartDate '%s'" % str(startdate))

            enddate = versionform.cleaned_data['enddate']
            if enddate:
                args.append(Q(creation_date__lte=enddate))
                logger.debug("EndDate '%s'" % str(enddate))

            agents = versionform.cleaned_data['agent']
            # agent is now mandatory
            # if not agents:
            #     agents = Agent.objects.all()
            agent_ids = tuple([a.id for a in agents])
            args.append(Q(agent__id__in=agent_ids))
            agents_dict = dict()
            for a in agents:
                agents_dict[a.id] = a
            logger.debug("Agents '%s'" % str(agents))

            v = versionform.cleaned_data['version']
            if v and len(v) > 0:
                subargs = list()
                if v.startswith("5.0"):
                    subargs.append(
                        (
                            Q(version__startswith=v) |
                            Q(version__startswith='4.5')
                        )
                    )
                elif v.startswith("4.2"):
                    subargs.append(
                        (
                            Q(version__startswith=v) |
                            Q(version__startswith='Beta-4.2')
                        )
                    )
                elif v.startswith("4.1"):
                    subargs.append(
                        (
                            Q(version__startswith=v) |
                            Q(version__startswith='Beta-4.1')
                        )
                    )
                else:
                    subargs.append(Q(version__startswith=v))
                agent_version = AgentVersion.objects.filter(*subargs)
                # agent_version_ids = tuple([a.id for a in agent_version])
                args.append(Q(agentversion__in=agent_version))
            # 5.0 AND (registry_hit.agent_version LIKE %s  OR
            # registry_hit.agent_version LIKE '4.5%%')
            # 4.1 or 4.2 AND (registry_hit.agent_version LIKE %s OR
            # registry_hit.agent_version LIKE 'Beta-4.1%%'

            # ip adresses
            ip_address = IP.objects.exclude(ip__regex=settings.IPLOCALREGEX)
            args.append(Q(ip__in=ip_address))

            # monthly main query
            monthly_result = Hit.objects \
                .filter(*args) \
                .extra(select={
                    'datestr': "to_char(creation_date, 'YYYY-MM')"}) \
                .values('agent_id', 'datestr') \
                .annotate(hit_total_count=Count('id')) \
                .annotate(hit_unique_count=Count('ip__id', distinct=True))

            # prepare table
            table = month_year_table(startdate, enddate, agents)

            try:
                for row in monthly_result:
                    if row['agent_id'] in (7, 13):
                        display_name = "BF (7,13)"
                    else:
                        display_name = "%s (%i)" % (
                            agents_dict[row['agent_id']].display_name,
                            row['agent_id'])
                    creation_date = row['datestr']
                    total = row['hit_total_count']
                    unique = row['hit_unique_count']
                    try:
                        table[creation_date][display_name]['total'] += total
                        table[creation_date][display_name]['unique'] += unique
                    except:
                        pass
            except:
                logger.debug(traceback.format_exc())

            # All agents main query not as a sum
            all_monthly_result = Hit.objects \
                .filter(*args) \
                .extra(select={
                    'datestr': "to_char(creation_date, 'YYYY-MM')"}) \
                .values('datestr') \
                .annotate(hit_total_count=Count('id')) \
                .annotate(hit_unique_count=Count('ip__id', distinct=True))

            try:
                for row in all_monthly_result:
                    display_name = "All*"
                    creation_date = row['datestr']
                    total = row['hit_total_count']
                    unique = row['hit_unique_count']
                    try:
                        table[creation_date][display_name]['total'] += total
                        table[creation_date][display_name]['unique'] += unique
                    except:
                        pass
            except:
                logger.debug(traceback.format_exc())

            result, column_names = sorted_table(table)
            context['result'] = result
            context['column_names'] = column_names
    else:
        versionform = VersionForm(initial=initial)

    context['version'] = version
    context['defaultversion'] = Version.objects.get(pk=1)
    context['versionform'] = versionform

    t = get_template(template)
    c = Context(request, context)
    rsp = t.render(c)
    return HttpResponse(rsp)
