#!/usr/bin/env python
#
# OMERO Registry Dump
# Copyright 2000 Glencoe Software, Inc.  All Rights Reserved.
#

import psycopg2
from pprint import pprint
import exceptions
import simplejson
import itertools
import GeoIP
import traceback
import os
import re
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=os.path.join(os.path.dirname(__file__), 'test.log'),
                    filemode='w')
logger = logging.getLogger('db-test')

class jsondump:

    def __init__(self):
        self.HitPk = 0
        self.IpPk = 0
        self.ip_map = dict()
        self.hit_map = dict()
        try:
           self.conn = psycopg2.connect("dbname='feedback' user='feedback' host='localhost' password='feedback'");
        except:
           print (traceback.format_exc())
           print "I am unable to connect to the database"
        

    def close(self):
        self.conn.close()

    def do_ips(self):
        a = self.conn.cursor()
        a.execute('select count(id) from registry_ip')    
        logger.debug("total hits %i" % a.fetchone()[0])
        logger.debug("'SELECT ip FROM registry_ip group by ip' ...")
        self.ips = self.conn.cursor()
        self.ips.execute('SELECT ip FROM registry_ip group by ip')
        result = self.ips.fetchall()
        logger.debug("results = %i" % len(result))
        for row in result:
            ip = row[0]
            if self.ip_map.has_key(ip):
                logger.debug("that ip already exist in array '%s'" % ip)
                continue
            try:
                GeoIP.gi = GeoIP.open(os.path.join(os.path.join(os.path.dirname(__file__), '../'), 'GeoLiteCity.dat').replace('\\','/'),GeoIP.GEOIP_STANDARD)
                gir = GeoIP.gi.record_by_addr(ip)
                GeoIP.gi = GeoIP.open(os.path.join(os.path.join(os.path.dirname(__file__), '../'), 'GeoIP.dat').replace('\\','/'),GeoIP.GEOIP_MEMORY_CACHE)
                country = GeoIP.gi.country_name_by_addr(ip)
                lat = gir["latitude"]
                lon = gir["longitude"]
            except:
                lat = "null"
                lon = "null"
                country = None
            self.IpPk += 1
            self.ip_map[ip] = self.IpPk
            self.hit_map[ip] = dict()
            print """INSERT INTO registry_ip (ip, latitude, longitude, country) VALUES('%s',%s,%s,%s);""" % (ip, lat,lon, (country and "'%s'" % country or 'null'))
        logger.debug("total ips %i" % self.IpPk)
    
    def count_hits(self):
        h = self.conn.cursor()
        h.execute('select count(id) from registry_hit')    
        res = h.fetchone()[0]
        logger.debug("total hits %i" % res)
        return res
        
        
    def do_hits(self, limit, offset=None):
        logger.debug("do hits ...")
        if limit:
            sql = """SELECT registry_ip.ip, registry_hit.poll, registry_hit.creation_date, \
registry_hit.agent_id, registry_hit.agent_version, registry_hit.os_name, \
registry_hit.os_arch, registry_hit.os_version, registry_hit.java_vendor, \
registry_hit.java_version, registry_hit.python_version, registry_hit.python_compiler, \
registry_hit.python_build, registry_hit.header FROM registry_hit, registry_ip WHERE \
registry_hit.ip_id=registry_ip.id ORDER BY registry_hit.id ASC LIMIT %s """ % limit
        if offset:
            sql = sql + (' OFFSET %s' % offset)
        
        logger.debug("sql = '%s'" % sql)
        self.hits = self.conn.cursor()
        self.hits.execute(sql)    
        result = self.hits.fetchall()
        for row in result:
                        
            ip = row[0]
            poll = row[1]           
            date = row[2]
            agent = row[3]
            vers = row[4]
            osn = row[5]
            osa = row[6]
            osv = row[7]
            jv = row[8]
            jvr = row[9]
            pv = row[10]
            pc = row[11]
            pb = row[12] is not None and row[12].replace("'","\"") or None
            h = row[13].replace("'","\"")
            
            if not self.ip_map.has_key(ip):
                logger.debug("that ip is not in array '%s'" % ip)
                self.IpPk+=1
                self.ip_map[ip] = self.IpPk
                self.hit_map[ip] = dict()
                try:
                    GeoIP.gi = GeoIP.open(os.path.join(os.path.join(os.path.dirname(__file__), '../'), 'GeoLiteCity.dat').replace('\\','/'),GeoIP.GEOIP_STANDARD)
                    gir = GeoIP.gi.record_by_addr(ip)
                    GeoIP.gi = GeoIP.open(os.path.join(os.path.join(os.path.dirname(__file__), '../'), 'GeoIP.dat').replace('\\','/'),GeoIP.GEOIP_MEMORY_CACHE)
                    country = GeoIP.gi.country_name_by_addr(ip)
                    lat = gir["latitude"]
                    lon = gir["longitude"]                
                except:
                    lat = "null"
                    lon = "null"
                    country = None
                if agent == 5 and self.hit_map[ip].has_key(date.strftime("%Y-%m-%d")):
                    if self.hit_map[ip][date.strftime("%Y-%m-%d")] > 0:
                        pass
                else:
                    self.HitPk += 1
                    if agent == 5:
                        self.hit_map[ip][date.strftime("%Y-%m-%d")] = 1
                print """INSERT INTO registry_ip (ip, latitude, longitude, country) VALUES('%s',%s,%s,%s);""" % (ip, lat,lon, (country and "'%s'" % country or 'null'))
                print """INSERT INTO registry_hit (ip_id, poll, creation_date, agent_id, agent_version, os_name, os_arch, os_version, java_vendor, java_version, python_version, python_compiler, python_build, header) VALUES((select id from registry_ip where ip='%s'), %s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s);""" % (ip, (poll and "'%s'" % poll or 'null'), date, agent, vers, (osn and "'%s'" % osn or 'null'), (osa and "'%s'" % osa or 'null'), (osv and "'%s'" % osv or 'null'), (jv and "'%s'" % jv or 'null'), (jvr and "'%s'" % jvr or 'null'), (pv and "'%s'" % pv or 'null'), (pc and "'%s'" % pc or 'null'), (pb and "'%s'" % pb or 'null'), (h and "E'%s'" % h or 'null'))
            else:
                if agent == 5 and self.hit_map[ip].has_key(date.strftime("%Y-%m-%d")) and self.hit_map[ip][date.strftime("%Y-%m-%d")] > 0:
                    pass
                else:
                    self.HitPk += 1
                    if agent == 5:
                        self.hit_map[ip][date.strftime("%Y-%m-%d")] = 1
                    print """INSERT INTO registry_hit (ip_id, poll, creation_date, agent_id, agent_version, os_name, os_arch, os_version, java_vendor, java_version, python_version, python_compiler, python_build, header) VALUES((select id from registry_ip where ip='%s'), %s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s);""" % (ip, (poll and "'%s'" % poll or 'null'), date, agent, vers, (osn and "'%s'" % osn or 'null'), (osa and "'%s'" % osa or 'null'), (osv and "'%s'" % osv or 'null'), (jv and "'%s'" % jv or 'null'), (jvr and "'%s'" % jvr or 'null'), (pv and "'%s'" % pv or 'null'), (pc and "'%s'" % pc or 'null'), (pb and "'%s'" % pb or 'null'), (h and "E'%s'" % h or 'null'))
        logger.debug("total hits '%i'" % (self.HitPk))

if __name__ == "__main__":
    import sys
    db = jsondump()
    print "BEGIN;"
    db.do_ips()
    count = db.count_hits()
    limit = 1000000
    for i in range(0,count/limit+1):
        db.do_hits(limit, i*limit)
    #db.do_hits(100)
    print "COMMIT;"
    logger.debug(sys.stderr)
    #logger.debug(db.ip_map)
    logger.debug(db.hit_map)
    db.close()
