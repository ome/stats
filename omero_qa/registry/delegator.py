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

import os
import logging
import traceback
import time

from django.conf import settings
from django.db import models
from django.db import connection

from omero_qa.qa.models import TestFile, TestEngineResult, FileFormat
from omero_qa.registry.models import Hit, IP
from datetime import datetime, date, timedelta

logger = logging.getLogger('delegator-registry')


try:
    import time
    import omero
    import omero.clients
    from omero import client_wrapper
    from omero.rtypes import *
except Exception, x:
    logger.debug(traceback.format_exc())

class IPforXML(models.Model):
    ip = models.CharField(max_length=20)
    latitude = models.FloatField(max_length=50, blank=True, null=True)
    longitude = models.FloatField(max_length=250, blank=True, null=True)
    agent_name = models.CharField(max_length=250)


def file_stat():
    logger.debug("file stat")
    formats = FileFormat.objects.all()
    files = dict()
    for f in formats:
        c = TestFile.objects.filter(file_format=f).count()
        if c > 0:
            files[f.format_name] = c
    logger.debug(files)
    return files


def file_stat_percent():
    logger.debug("file stat percent")
    formats = FileFormat.objects.all()
    total = TestFile.objects.filter(file_format__isnull=False).count()
    logger.debug("Total %s" % str(total))
    files = dict()
    for f in formats:
        c = TestFile.objects.filter(file_format=f).count()
        if c > 0:
            files[f.format_name] = 100*float(c)/float(total)
    logger.debug(files)
    return files


def total_results():
    files = TestFile.objects.all().count()
    results = TestEngineResult.objects.all().count()
    failure = TestEngineResult.objects.all().exclude(error=None).count()
    logger.debug("total_files: '%i'" % files)
    logger.debug("total_results: '%i'" % results)
    logger.debug("total_failur: '%i'" % failure)
    return {'files':files, 'results':results, 'failure':failure}
    

def custom_date_results(custom_date=None):
    if custom_date is not None:
        try:
            custom_date = datetime(*(time.strptime(("%s 00:00:00" % (custom_date)), "%Y-%m-%d %H:%M:%S")[0:6]))
        except:
            custom_date = date.today()
    else:
        custom_date = date.today()
    logger.debug("Custom date: '%s'" % custom_date)
    
    files = TestFile.objects.filter(upload_date__gte=custom_date).count()        
    results = TestEngineResult.objects.filter(started__gte=custom_date).count()
    failure = TestEngineResult.objects.filter(started__gte=custom_date).exclude(error=None).count()
    logger.debug("files: '%i'" % files)
    logger.debug("results: '%i'" % results)
    logger.debug("failur: '%i'" % failure)
    return {'files':files, 'results':results, 'failure':failure}


def save_hit(ip, agent, agent_version=None, poll=None, os_name=None, os_arch=None, os_version=None, java_vendor=None, java_version=None, python_version=None, python_compiler=None, python_build=None, header=None):
    os_name = os_name is not None and os_name[:250] or None
    os_arch = os_arch is not None and os_arch[:250] or None
    os_version = os_version is not None and os_version[:250] or None
    java_vendor = java_vendor is not None and java_vendor[:250] or None
    java_version = java_version is not None and java_version[:250] or None
    python_version = python_version is not None and python_version[:50] or None
    python_compiler = python_compiler is not None and python_compiler[:50] or None
    python_build = python_build is not None and python_build[:50] or None
    
    hit = Hit(ip=ip, agent=agent, agent_version=agent_version, poll=poll, os_name=os_name, os_arch=os_arch, os_version=os_version, java_vendor=java_vendor, java_version=java_version, python_version=python_version, python_compiler=python_compiler, python_build=python_build, header=header)
    hit.save()

class Statistics(object):

    cursor = None
    agents = None
    
    
    def __init__(self, agents):
        logger.debug("Statistics initial")
        self.cursor = connection.cursor()
        self.agents = agents
    
    
    def last_30_days(self):
        start = date.today() + timedelta(days=-30)
        sql = """SELECT date(registry_hit.creation_date), count(date(registry_hit.creation_date)) \
                FROM registry_hit, registry_ip \
                WHERE registry_hit.ip_id=registry_ip.id \
                AND registry_ip.latitude IS NOT NULL \
                AND registry_ip.longitude IS NOT NULL \
                AND registry_hit.creation_date >= '%s' \
                AND registry_hit.agent_id = %i \
                GROUP BY date(registry_hit.creation_date) """
        
        total = 0
        table = dict()
        for i in range(0,31):
            key = str(date.today() + timedelta(days=-i))
            table[key] = {'Total':0}
            for a in self.agents:
                table[key][a.display_name]=0

        for a in self.agents:
            self.cursor.execute(sql % (start, a.id))
            result = self.cursor.fetchall()
            for res in result:
                table[str(res[0])][a.display_name] = res[1]
                table[str(res[0])]['Total'] += res[1]
                total += res[1]
        
        keys = list(table)
        keys.sort()
        keys.reverse()
        result = list()
        for k in keys:
            tk = table[k]
            t = [(key, tk[key], (key=='Total' and (tk['Total']*100.0/total) or None)) for key in sorted(tk.iterkeys())]
            result.append((k,t))
        logger.info('Statistics last_30_days data (total: %i)' % (len(result)))
        
        return result
    
    
    def weekly(self, starting_year=2008):
        start = date(starting_year,1,1)
        sql = """SELECT date(registry_hit.creation_date), count(date(registry_hit.creation_date)) \
                FROM registry_hit, registry_ip \
                WHERE registry_hit.ip_id=registry_ip.id \
                AND registry_ip.latitude IS NOT NULL \
                AND registry_ip.longitude IS NOT NULL \
                AND registry_hit.creation_date >= '%s' \
                AND registry_hit.agent_id = %i \
                GROUP BY date(registry_hit.creation_date) """
        
        total = 0
        table = dict()
        diff = date.today() - start
        weeks_range = divmod(diff.days, 7)[0]
        
        for i in range(0, weeks_range+2):
            week = i%53 < 10 and ("0%i" % (i%53)) or str(i%53)
            key = "%s %s" % (str(starting_year + i/53), week)
            table[key] = {'Total':0}
            for a in self.agents:
                table[key][a.display_name]=0

        for a in self.agents:
            self.cursor.execute(sql % (start, a.id))
            result = self.cursor.fetchall()
            for res in result:
                idx = res[0].strftime('%Y %W')
                if table.has_key(idx):
                    table[idx][a.display_name] += res[1]
                    table[idx]['Total'] += res[1]
                    total += res[1]
                else:
                    logger.info('Key %s does not exist' % idx)
                    
        keys = list(table)
        keys.sort()
        keys.reverse()
        result = list()
        for k in keys:
            tk = table[k]
            t = [(key, tk[key], (key=='Total' and (tk['Total']*100.0/total) or None)) for key in sorted(tk.iterkeys())]
            result.append((k,t))
        logger.info('Statistics weekly data (total: %i)' % (len(result)))
        
        return result
    
    
    def by_country(self):
        sql = """SELECT registry_ip.country, count(registry_hit.ip_id) \
                FROM registry_hit, registry_ip \
                WHERE registry_hit.ip_id=registry_ip.id \
                AND registry_ip.latitude IS NOT NULL \
                AND registry_ip.longitude IS NOT NULL \
                AND registry_hit.agent_id = %i \
                GROUP BY registry_ip.country """
        
        total = 0
        table = {'Unknown': {'Total':0}}
        for a in self.agents:
            table['Unknown'][a.display_name] = 0
        
        for a in self.agents:
            self.cursor.execute(sql % a.id)
            result = self.cursor.fetchall()
            for res in result:
                c = res[0]
                if c is None:
                    c = 'Unknown'
                if table.has_key(c):
                    table[c][a.display_name] += res[1]
                    table[c]['Total'] += res[1]
                else:
                    table[c] = {'Total':0}
                    for ag in self.agents:
                        table[c][ag.display_name] = 0
                    table[c][a.display_name] = res[1]
                    table[c]['Total'] = res[1]
                total += res[1]
        
        keys = list(table)
        keys.sort()
        result = list()
        for k in keys:
            tk = table[k]
            t = [(key, tk[key], (key=='Total' and (tk['Total']*100.0/total) or None)) for key in sorted(tk.iterkeys())]
            result.append((k,t))
        logger.info('Statistics by_country data (total: %i)' % (len(result)))
        
        return result
    
    
    def by_ip(self):
        sql = """SELECT registry_ip.ip, count(registry_hit.ip_id) \
                FROM registry_hit, registry_ip \
                WHERE registry_hit.ip_id=registry_ip.id \
                AND registry_ip.latitude IS NOT NULL \
                AND registry_ip.longitude IS NOT NULL \
                AND registry_hit.agent_id = %i \
                GROUP BY registry_ip.ip """
        
        table = dict()
        total = 0
        total_table = dict()
        unique_table = dict()
        for a in self.agents:
            total_table[a.display_name] = 0
            unique_table[a.display_name] = 0
        for a in self.agents:            
            self.cursor.execute(sql % a.id)
            result = self.cursor.fetchall()
            for res in result:
                if table.has_key(res[0]):
                    table[res[0]][a.display_name] += res[1]
                    table[res[0]]['Total'] += res[1]
                else:
                    table[res[0]] = {'Total':res[1]} 
                    for ag in self.agents:
                        table[res[0]][ag.display_name] = 0
                    table[res[0]][a.display_name] += res[1]
                unique_table[a.display_name] += 1
                total_table[a.display_name] += res[1]
                total += res[1]
        
        keys = list(table)
        
        def ipsort(a,b):
            a = [int(i) for i in a.split(".")]
            b = [int(i) for i in b.split(".")]
            for i in range(0,4):
                t = cmp(a[i],b[i])
                if t != 0:
                    return t
            return 0
        
        keys.sort(ipsort)
        result = list()
        result.append(('Total',[(key, total_table[key]) for key in sorted(total_table.iterkeys())]))
        result.append(('Unique',[(key, unique_table[key]) for key in sorted(unique_table.iterkeys())]))
        for k in keys:
            tk = table[k]
            t = [(key, tk[key], (key=='Total' and (tk['Total']*100.0/total) or None)) for key in sorted(tk.iterkeys())]
            result.append((k,t))
        
        logger.info('Statistics by_ip data (total: %i)' % (len(result)))
        return result
    
    
    def by_os(self):
        sql = """SELECT registry_hit.os_name, count(registry_hit.os_name), \
                registry_hit.os_arch, registry_hit.os_version \
                FROM registry_hit, registry_ip \
                WHERE registry_hit.ip_id=registry_ip.id \
                AND registry_ip.latitude IS NOT NULL \
                AND registry_ip.longitude IS NOT NULL \
                GROUP BY registry_hit.os_name, registry_hit.os_arch, registry_hit.os_version """
        
        table = {'Others': 0}
        table_d = {'Others': 0}
        total = 0
        
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for res in result:
            if res[0] is not None:
                if table.has_key(res[0]):
                    table[res[0]] += res[1]
                else:
                    table[res[0]] = res[1]
                key = "%s %s %s" % (res[0], res[2], res[3])
                key = len(key) > 70 and ("%s..." % key[:70]) or key
                if table_d.has_key(key):
                    table_d[key] += res[1]
                else:
                    table_d[key] = res[1]
            else:
                table['Others'] += 1
                table_d['Others'] += 1
            total += res[1]
        
        logger.info('Statistics by_os (total:%i)' % total)
        logger.info('Statistics by_os detailed (total:%i)' % total)
        
        items = [(v, k) for k, v in table.items()]
        items.sort()
        items.reverse()
        result = [(k, v, (v*100.0/total)) for v, k in items]
        
        items = [(v, k) for k, v in table_d.items()]
        items.sort()
        items.reverse()
        result_d = [(k, v, (v*100.0/total)) for v, k in items]
        
        logger.info('Statistics by_os data (total: %i, details: %i)' % (len(result), len(result_d)))
        return (result, result_d)
    
    
    def by_env(self):
        sql = """SELECT registry_hit.java_version, count(registry_hit.java_version), \
                registry_hit.java_vendor, \
                registry_hit.python_version, count(registry_hit.python_version), \
                registry_hit.python_compiler, registry_hit.python_build \
                FROM registry_hit, registry_ip \
                WHERE registry_hit.ip_id=registry_ip.id \
                AND registry_ip.latitude IS NOT NULL \
                AND registry_ip.longitude IS NOT NULL \
                GROUP BY registry_hit.java_version, registry_hit.java_vendor, \
                registry_hit.python_version, registry_hit.python_compiler, registry_hit.python_build """
        
        table_j = dict()
        table_p = dict()
        total_j = 0
        total_p = 0
            
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for res in result:
            if res[0] is not None and res[0] != "":
                key = "%s %s" % (res[0], res[2])
                key = len(key) > 50 and ("%s..." % key[:50]) or key
                if table_j.has_key(key):
                    table_j[key] += res[1]
                else:
                    table_j[key] = res[1]
                total_j += res[1]
            elif res[3] is not None and res[3] != "":
                key = "%s %s %s" % (res[3], res[5], res[6])
                key = len(key) > 50 and ("%s..." % key[:50]) or key
                if table_p.has_key(key):
                    table_p[key] += res[4]
                else:
                    table_p[key] = res[4]
                total_p += res[4]
        
        items = [(v, k) for k, v in table_j.items()]
        items.sort()
        items.reverse()
        result_j = [(k, v, (v*100.0/total_j)) for v, k in items]
        
        items = [(v, k) for k, v in table_p.items()]
        items.sort()
        items.reverse()
        result_p = [(k, v, (v*100.0/total_p)) for v, k in items]
        
        logger.info('Statistics by_env data (JAVA: %i, PYTHON: %i)' % (total_j, total_p))
        
        return (result_j, result_p)


class DemoStatistics(object):
    
    conn = None
    demo_group = None
    experimenters = dict()
    
    def __init__(self):
        ds = settings.DEMO_SERVER
        self.conn = client_wrapper(ds['username'], ds['passwd'], host=ds['host'], port=ds['port'])
        self.conn.connect()
        
        self.demo_group = self.conn.lookupGroup("demo_group") 
        self.experimenters = list()
        for e in list(self.conn.containedExperimenters(self.demo_group.id)):
            if e.omeName != 'root' and e.omeName != 'root_demo':
                self.experimenters.append(e)
        
    def ping(self):
        self.conn.keepAlive()
       
    def demostats(self):
        a = self.activities()
        f = self.formats()
        result = dict()
        result['activities'] = {'keys':a[1], 'results':a[0]}
        result['formats'] = {'formats':f[0], 'per_user':f[1]}
        result['account_details'] = {'total':len(self.experimenters), 'used': len(a[0])}
        return result
    
    def formats(self):
        formats = dict()
        exp_formats = dict()
        for e in self.experimenters:
            p = omero.sys.Parameters()
            p.map = {}
            p.map["eid"] = rlong(e.id)
            sql = "select i from Image as i " \
                  "left outer join fetch i.format as f " \
                  "where i.details.owner.id=:eid order by i.id asc"

            res = self.conn.getQueryService().findAllByQuery(sql,p)
            if len(res)>0:
                exp_formats[e.id] = dict()
                for r in res:
                    if r.format is not None:
                        k = r.format.value.val.lower()
                    else:
                        sp = r.name.val.rsplit(".")
                        k = sp[len(sp)-1][:4].lower().strip()
                                            
                    #per exp
                    if formats.has_key(k):
                        formats[k]+=1
                    else:
                        formats[k] = 1

                    if exp_formats[e.id].has_key(k):
                        exp_formats[e.id][k]+=1
                    else:
                        exp_formats[e.id][k] = 1
        
        keys = list(exp_formats)
        keys.sort()
        keys.reverse()
        result = list()
        
        exps = dict()
        for e in self.experimenters:
            exps[e.id] = e
            
        for k in keys:
            tk = exp_formats[k]
            t = [(key, tk[key]) for key in sorted(tk.iterkeys())]
            e = "%s (%s)" % (exps[k].getFullName(), (exps[k].institution is None and "Unknown" or exps[k].institution ))
            result.append((e,t))
                
        formats_s = sorted(formats.iteritems(), key=lambda (k,v):(v,k), reverse=True)
        logger.info('Statistics formats data (total: %i)' % (len(formats_s)))
        return(formats_s, result)
    
    def activities(self, timestamp=None):  
        p = omero.sys.Parameters()
        p.map = {}
        p.map['eids'] = rlist(rlong(e.id) for e in self.experimenters)
        #p.map['sysUserAgent'] = rlist([rstring('ExecutionThread')])
        if timestamp is not None:
            p.map["timestamp"] = rtime(timestamp)
            sql = "select o.id, COUNT(s.closed) as total, s.userAgent "\
                  "from Session s join s.owner o "\
                  "where o.id in (:eids) "\
                  "group by o.id, s.userAgent"
        else:
            sql = "select o.id, COUNT(s.closed) as total, s.userAgent "\
                  "from Session s join s.owner o "\
                  "where o.id in (:eids) "\
                  "group by o.id, s.userAgent"
        
        res = self.conn.getQueryService().projection(sql, p, None)
        rv = unwrap(res)

        res_a = self.conn.getQueryService().projection("select DISTINCT(s.userAgent), s.userAgent from Session s )", p, None)
        agents = ['Total']
        for a in unwrap(res_a):
            agents.append(str(a[0]))
        agents.sort()
        
        total = 0
        table = dict()
        for e in self.experimenters:
            table[e.id] = {'Total':0}
            for a in agents:
                table[e.id][str(a)]=0

        for r in rv:
            table[r[0]][str(r[2])] += r[1]
            table[r[0]]['Total'] += r[1]
            total += r[1]
        
        keys = list(table)
        keys.sort()
        keys.reverse()
        result = list()
        
        exps = dict()
        for e in self.experimenters:
            exps[e.id] = e
            
        for k in keys:
            if sum([t[1] for t in table[k].items()]) > 0:
                tk = table[k]
                t = [(key, tk[key]) for key in sorted(tk.iterkeys())]
                e = "%s (%s)" % (exps[k].getFullName(), (exps[k].institution is None and "Unknown" or exps[k].institution ))
                result.append((e,t))
        logger.info('Statistics activities data (total: %i)' % (len(result)))
        return (result, agents)
