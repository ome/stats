import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'omerostats.settings-prod'

import django

from django.db.models import Q
from django.conf import settings
from omerostats.registry.models import IP, Hit

IPLOCALREGEX = settings.IPLOCALREGEX

LINE_BREAK = """------------------------------------"""

lonlatnone = IP.objects.filter(latitude=None, longitude=None).exclude(ip__regex=IPLOCALREGEX).count()
countinentnone = IP.objects.filter(continent=None).exclude(ip__regex=IPLOCALREGEX).count()
countrynone = IP.objects.filter(country=None).exclude(ip__regex=IPLOCALREGEX).count()
citynone = IP.objects.filter(city=None).exclude(ip__regex=IPLOCALREGEX).count()
orgnone = IP.objects.filter(organisation=None).exclude(ip__regex=IPLOCALREGEX).count()


print LINE_BREAK
print """General Summary"""
print LINE_BREAK
print """%i unrecognized IPs""" % lonlatnone
print """%i IPs with no Country assigned""" % (countrynone)
print """%i IPs with no Continent assigned""" % (countinentnone)
print """%i IPs with no City assigned""" % (citynone)
print """%i IPs with no Organisation assigned""" % (orgnone)

print LINE_BREAK

euonly = IP.objects.filter(continent__name="Europe").exclude(ip__regex=IPLOCALREGEX).count()
naonly = IP.objects.filter(continent__name="North America").exclude(ip__regex=IPLOCALREGEX).count()

ukonly = IP.objects.filter(country__name="United Kingdom").exclude(ip__regex=IPLOCALREGEX).count()
usonly = IP.objects.filter(country__name="United States").exclude(ip__regex=IPLOCALREGEX).count()

print """%i IPs in Europe """ % (euonly)
print """%i IPs in North America """ % (naonly)
print """%i IPs in UK """ % (ukonly)
print """%i IPs in US """ % (usonly)

