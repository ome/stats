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

import logging

from django.db import models

logger = logging.getLogger(__name__)


class IPforXML(models.Model):
    ip = models.CharField(max_length=20)
    latitude = models.FloatField(max_length=50, blank=True, null=True)
    longitude = models.FloatField(max_length=250, blank=True, null=True)
    agent_name = models.CharField(max_length=250)
    org = models.CharField(max_length=250)


def month_year_table(startdate, enddate, agents):

    def month_year_iter(start_month, start_year, end_month, end_year):
        ym_start = 12*start_year + start_month - 1
        ym_end = 12*end_year + end_month
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            yield y, m+1

    table = dict()

    for year, month in month_year_iter(
            startdate.month, startdate.year, enddate.month, enddate.year):
        month = month < 10 and ("0%i" % (month)) or str(month)
        idx = "%s-%s" % (year, month)
        table[idx] = dict()
        table[idx]['All*'] = {'total': 0, 'unique': 0}
        for a in agents:
            if a.id in (7, 13):
                name = "BF (7,13)"
            else:
                name = "%s (%i)" % (a.display_name, a.id)
            table[idx][name] = {'total': 0, 'unique': 0}

    return table


def year_table(startdate, enddate, agents):

    def year_iter(start_year, end_year):
        y_start = start_year
        y_end = end_year
        for y in range(y_start, y_end):
            yield y

    table = dict()

    for year in year_iter(startdate.year, enddate.year):
        idx = "%s" % (year)
        table[idx] = dict()
        table[idx]['All*'] = {'total': 0, 'unique': 0}
        for a in agents:
            if a.id in (7, 13):
                name = "BF (7,13)"
            else:
                name = "%s (%i)" % (a.display_name, a.id)
            table[idx][name] = {'total': 0, 'unique': 0}

    return table


def sorted_table(table):
    keys = list(table)
    keys.sort()
    keys.reverse()
    result = list()
    for k in keys:
        tk = table[k]
        t = [(key, tk[key]) for key in sorted(tk.iterkeys())]
        result.append((k, t))
    logger.info('Statistics monthly data (total: %i)' % (len(result)))

    column_names = list()
    for row in result[0][1]:
        column_names.append(row[0])

    return result, column_names
