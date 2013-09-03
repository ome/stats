import os, traceback, socket

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'omerostats.settings-prod'

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q

from omerostats.registry.models import IP, Continent, Country, City, Organisation, Host, Domain, Suffix

import pygeoip
import geoip2.database

IPLOCALREGEX = settings.IPLOCALREGEX

def getHost(ip):
    """
    This method returns the 'True Host' name for a
    given IP address
    """
    try:
        data = socket.gethostbyaddr(ip)
        host = repr(data[0])[1:-1]
        return host
    except Exception:
        return None

def getExt(host):
    """
    This method returns the 'True Host' name for a
    given IP address
    """
    try:
        name, ext = host.split('.')[-2:]
        if name in ("com", "org", "net", "gov", "ac", "edu", "co", "gv","or", "info", "mil", "cable"):
            domain = "%s.%s" % (name, ext)
        elif name.startswith("uni-"):
            domain = "uni.%s" % (ext)
        else:
            domain = ext
        return domain.lower()
    except Exception:
        return None

def getContinent(continent):
    return continent

def getCountry(country):
    return country

def getCity(city):
    return city

def getOrg(org):
    return org

def getDomain(domain):
    return domain.domain

gid_domain_reader = geoip2.database.Reader(settings.GEOIPDOMAIN)
gio = pygeoip.GeoIP(settings.GEOIPORG)
gid_city_reader = geoip2.database.Reader(settings.GEOIPCITY)

counter = IP.objects.filter(
    Q(continent__isnull=True) | Q(country__isnull=True) | \
    Q(organisation__isnull=True) | Q(domain__isnull=True) \
    ).order_by('id').exclude(ip__regex=IPLOCALREGEX) \
    .count()

print """Found %d IPs""" % (counter)

allips = IP.objects.filter(
    Q(continent__isnull=True) | Q(country__isnull=True) | \
    Q(organisation__isnull=True) | Q(domain__isnull=True) \
    ).order_by('id').exclude(ip__regex=IPLOCALREGEX)

for ip in allips:
    try:
        respons = gid_city_reader.city(ip.ip)
        ip.latitude = respons.location.latitude
        ip.longitude = respons.location.longitude

        # Continent
        continent = None
        if getContinent(respons.continent.name) is not None:
            try:
                continent = Continent.objects.get(name=getContinent(respons.continent.name))
                ip.continent = continent
            except Continent.DoesNotExist:
                continent = Continent(name=getContinent(respons.continent.name), centerx=0, centery=0, zoom=3)
                continent.save()
                ip.continent = continent

        # Country
        country = None
        if getCountry(respons.country.name) is not None:
            try:
                country = Country.objects.get(name=getCountry(respons.country.name))
                ip.country = country
            except Country.DoesNotExist:
                country = Country(name=getCountry(respons.country.name))
                country.continent = continent
                country.save()
                ip.country = country

        # City
        if getCity(respons.city.name) is not None:
            try:
                city = City.objects.get(name=getCity(respons.city.name))
                ip.city = city
            except City.DoesNotExist:
                city = City(name=getCity(respons.city.name))
                city.country = country
                city.save()
                ip.city = city

        # Org
        if getOrg(gio.org_by_addr(ip.ip)) is not None:
            try:
                org = Organisation.objects.get(name=getOrg(gio.org_by_addr(ip.ip)))
                ip.organisation = org
            except Organisation.DoesNotExist:
                org = Organisation(name=getOrg(gio.org_by_addr(ip.ip)))
                org.save()
                ip.organisation = org

        # Domain
        if getDomain(gid_domain_reader.domain(ip.ip)) is not None:
            try:
                domain = Domain.objects.get(name=getDomain(gid_domain_reader.domain(ip.ip)))
                ip.domain = domain
            except Domain.DoesNotExist:
                domain = Domain(name=getDomain(gid_domain_reader.domain(ip.ip)))
                domain.save()
                ip.domain = domain

        # Host
        #if getHost(ip.ip) is not None:
        #    try:
        #        host = Host.objects.get(name=getHost(ip.ip))
        #        ip.host = host
        #    except Host.DoesNotExist:
        #        host = Host(name=getHost(ip.ip))
        #        host.save()
        #        ip.host = host

        # Suffix
        #if domain is not None:
        #    suffix = getExt(ip.domain)
        #elif host is not None:
        #    suffix = getExt(ip.host)
        #else:    
        #    ot_ips = list(IP.objects.filter(organisation=ip.organisation,longitude=ip.longitude,latitude=ip.latitude,suffix__isnull=False)
        #        .exclude(ip__regex=IPLOCALREGEX))
        #    if len(ot_ips) > 0:
        #        suffix = ot_ips[0].suffix
        #        domain = ot_ips[0].domain
        #    else:
        #        suffix = None
        #if suffix is not None and len(suffix) > 0:
        #    try:
        #        suffix = Suffix.objects.get(suffix=suffix)
        #        ip.suffix = suffix
        #    except Suffix.DoesNotExist:
        #        suffix = Suffix(suffix=suffix)
        #        suffix.save()
        #        ip.suffix = suffix

        ip.save()
        # print "IP saved ", ip.id

    except geoip2.errors.AddressNotFoundError, anfe:
        pass
    except Exception, e:
        print "Error:", e
