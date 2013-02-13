#!/usr/bin/env python
#
# OMERO Registry Dump
# Copyright 2000 Glencoe Software, Inc.  All Rights Reserved.
#

HitPk = 1
IpPk = 1
Agents = [{
        "pk": 1,
        "model": "registry.agent",
        "fields": {
            "agent_name": "Importer"
        }
    },
    {
        "pk": 2,
        "model": "registry.agent",
        "fields": {
            "agent_name": "Insight"
        }
    },
    {
        "pk": 3,
        "model": "registry.agent",
        "fields": {
            "agent_name": "Editor"
        }
    },
    {
        "pk": 4,
        "model": "registry.agent",
        "fields": {
            "agent_name": "FileSystem"
        }
    },
    {
        "pk": 5,
        "model": "registry.agent",
        "fields": {
            "agent_name": "Web"
        }
    },
    {
        "pk": 6,
        "model": "registry.agent",
        "fields": {
            "agent_name": "Server"
        }
    },
    {
        "pk": 7,
        "model": "registry.agent",
        "fields": {
            "agent_name": "ImageJ"
        }
    }]
AgentLookup = {}
for a in Agents:
    AgentLookup["OMERO.%s" % a["fields"]["agent_name"].lower()]=a["pk"]

try:
    from pysqlite2 import dbapi2 as sqlite
except ImportError:
    import sqlite3 as sqlite
from pprint import pprint
import exceptions
import simplejson
import itertools
import GeoIP
import traceback
import os

class jsondump:

    def __init__(self, dbname, isolate = True):
        self.ip_map = {}
        if isolate:
            self.conn = sqlite.connect(dbname)
        else:
            self.conn = sqlite.connect(dbname, isolation_level = None)

    def close(self):
        self.conn.close()

    def __iter__(self):
        return self

    def next(self):
        if not hasattr(self, 'hits'):
            self.hits = self.conn.cursor()
            self.hits.execute("""SELECT * FROM hit WHERE agent <> 'OMERO.curl' """)
            self.ips = self.conn.cursor()
            self.ips.execute('SELECT * FROM ip ORDER BY id ')
            self.chain = itertools.chain(self.hits, self.ips)
        try:
            return ip(self.ips.next(), self.ip_map)
        except StopIteration:
            return hit(self.hits.next(), self.ip_map)
            

class item:
    def __init__(self, row, ip_map):
        self.row = row
        self.ip_map = ip_map

class hit(item):
    def __str__(self):
            
        global HitPk
        global IpPk
        ip = self.row[0]            
        date = self.row[1]
        vers = self.row[2]
        poll = self.row[3]
        if poll == "unknown":
            poll = 0
        osn = self.row[6]
        if osn == "unknown":
            osn = None
        osa = self.row[7]
        if osa == "unknown":
            osa = None
        osv = self.row[8]
        if osv == "unknown":
            osv = None
        jv = self.row[4].replace("\"","")
        if jv == "unknown":
            jv = None
        jvr = self.row[5]
        if jvr == "unknown":
            jvr = None
        h = self.row[9].replace("'","\"")
        if h == "unknown":
            h = None
        try:
            agent = AgentLookup[self.row[11]]
        except KeyError:
            return ""
        
        try:
            self.ip_map[ip]
        except:
            IpPk+=1
            self.ip_map[ip] = IpPk
            try:
                GeoIP.gi = GeoIP.open(os.path.join(os.path.join(os.path.dirname(__file__), '../'), 'GeoLiteCity.dat').replace('\\','/'),GeoIP.GEOIP_STANDARD)
                gir = GeoIP.gi.record_by_addr(ip)
                lat = gir["latitude"]
                lon = gir["longitude"]
            except:
                lat = "null"
                lon = "null"
            HitPk += 1
            return """INSERT INTO "registry_ip" VALUES(%s,'%s',%s,%s);
INSERT INTO "registry_hit" VALUES(%s,%s,%s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s);""" % (IpPk, ip, lat,lon, HitPk, self.ip_map[ip], poll, date, agent, vers, (osn and "'%s'" % osn or 'null'), (osa and "'%s'" % osa or 'null'), (osv and "'%s'" % osv or 'null'), (jv and "'%s'" % jv or 'null'), (jvr and "'%s'" % jvr or 'null'),"null", "null", "null", (h and "'%s'" % h or 'null'))
        else:
            HitPk += 1
            return """INSERT INTO "registry_hit" VALUES(%s,%s,%s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s);""" % (HitPk, self.ip_map[ip], poll, date, agent, vers, (osn and "'%s'" % osn or 'null'), (osa and "'%s'" % osa or 'null'), (osv and "'%s'" % osv or 'null'), (jv and "'%s'" % jv or 'null'), (jvr and "'%s'" % jvr or 'null'),"null", "null", "null", (h and "'%s'" % h or 'null'))
        
class ip(item):
    def __str__(self):
        global HitPk
        global IpPk
        
        ip = self.row[0]
        tIps = ip.replace(" ", "").split(",")
        if len(tIps)>1:
            ip = tIps[0]
        lat = self.row[1]
        lon = self.row[2]

        try:
            GeoIP.gi = GeoIP.open(os.path.join(os.path.join(os.path.dirname(__file__), '../'), 'GeoLiteCity.dat').replace('\\','/'),GeoIP.GEOIP_STANDARD)
            gir = GeoIP.gi.record_by_addr(ip)
            lat = gir["latitude"]
            lon = gir["longitude"]
        except:
            lat = "null"
            lon = "null"
        IpPk += 1
        self.ip_map[self.row[0]] = IpPk
        return """INSERT INTO "registry_ip" VALUES(%s,'%s',%s,%s);""" % (IpPk, ip, lat,lon)

if __name__ == "__main__":
        import sys
        if len(sys.argv) == 1:
            print "jsondump dbname"
        else:
            dbname = sys.argv[1]
        db = jsondump(dbname)
        for j in db:
            print str(j)
        print >>sys.stderr, db.ip_map
        db.close()


