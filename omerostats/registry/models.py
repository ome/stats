#!/usr/bin/env python
# 
# 
# 
# Copyright (c) 2009 University of Dundee. 
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

from datetime import date, datetime, timedelta

from django.db import models
from django import forms
from django.forms import ModelForm
from django.conf import settings

### MODELS ###

class Version(models.Model):
    version = models.CharField(max_length=50)

    def __unicode__(self):
        return self.version


class Continent(models.Model):
    name = models.CharField(max_length=20, unique=True)
    centerx = models.FloatField()
    centery = models.FloatField()
    zoom = models.IntegerField()

    def __unicode__(self):
        return "%s" % (self.name)


class Country(models.Model):
    name = models.CharField(max_length=250, unique=True)
    continent = models.ForeignKey(Continent, blank = True, null=True)

    def __unicode__(self):
        return "%s" % (self.name)


class City(models.Model):
    name = models.CharField(max_length=250, unique=True)
    country = models.ForeignKey(Country, blank = True, null=True)

    def __unicode__(self):
        return "%s" % (self.name)


class Organisation(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __unicode__(self):
        return "%s" % (self.name)


class Domain(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __unicode__(self):
        return "%s" % (self.domain)


class Host(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __unicode__(self):
        return "%s" % (self.host)


class Suffix(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __unicode__(self):
        return "%s" % (self.suffix)


class IP(models.Model):
    
    ip = models.GenericIPAddressField(unique=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    city = models.ForeignKey(City, blank = True, null=True)
    country = models.ForeignKey(Country, blank = True, null=True)
    continent = models.ForeignKey(Continent, blank = True, null=True)
    organisation = models.ForeignKey(Organisation, blank = True, null=True)
    domain = models.ForeignKey(Domain, blank = True, null=True)
    host = models.ForeignKey(Host, blank = True, null=True)
    suffix = models.ForeignKey(Suffix, blank = True, null=True)
    
    def __unicode__(self):
        c = "%s" % (self.ip)
        return c




class Agent(models.Model):
    """
    Agent
    """
    agent_name = models.CharField(max_length=250, unique=True)
    display_name = models.CharField(max_length=250)

    def __unicode__(self):
        return "%s (%d)" % (self.display_name, self.id)


class AgentVersion(models.Model):
    version = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.version)


class OSName(models.Model):
    name = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.name)


class OSArch(models.Model):
    name = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.name)


class OSVersion(models.Model):
    version = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.version)


class JavaVendor(models.Model):
    name = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.name)


class JavaVersion(models.Model):
    version = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.version)


class PythonVersion(models.Model):
    version = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.version)


class PythonCompiler(models.Model):
    name = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.name)


class PythonBuild(models.Model):
    name = models.CharField(max_length=250, unique=True)
    def __unicode__(self):
        return "%s" % (self.name)


class Hit(models.Model):
     
    ip = models.ForeignKey(IP)
    creation_date = models.DateTimeField(default=datetime.now)
    agent = models.ForeignKey(Agent)
    agentversion = models.ForeignKey(AgentVersion, blank = True, null=True)
    osname = models.ForeignKey(OSName, blank = True, null=True)
    osarch = models.ForeignKey(OSArch, blank = True, null=True)
    osversion = models.ForeignKey(OSVersion, blank = True, null=True)
    javavendor = models.ForeignKey(JavaVendor, blank = True, null=True)
    javaversion = models.ForeignKey(JavaVersion, blank = True, null=True)
    pythonversion = models.ForeignKey(PythonVersion, blank = True, null=True)
    pythoncompiler = models.ForeignKey(PythonCompiler, blank = True, null=True)
    pythonbuild = models.ForeignKey(PythonBuild, blank = True, null=True)

    def __unicode__(self):
        c = "%s %s: %s" % (self.ip, self.agent.agent_name, self.agentversion.version)
        return c


### FORMS ###

version_help = "OMERO version should be in format of 5.1.0. To display the family just use 5.1. Do not use ? or x as a replacement for a number. Only numbers."

class MapForm(forms.Form):

    version = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size':10, 'title':version_help}))
    continent = forms.ModelChoiceField(queryset=Continent.objects.all(), empty_label="Whole World", label="Select region", widget=forms.Select(), required=False)
    country = forms.ModelMultipleChoiceField(queryset=Country.objects.all().order_by('name'), label="Select country", required=False)
    agent = forms.ModelMultipleChoiceField(queryset=Agent.objects.all(), label="Select agent")
    startdate = forms.DateField(initial=datetime(datetime.now().year, 1, 1))
    enddate = forms.DateField(initial=datetime.now().date())
    cluster = forms.BooleanField(initial=True, required=False)

class VersionForm(ModelForm):

    date_help = "Date should be in format of YYYY-MM-DD."
    version = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size':10, 'title':version_help}))
    startdate = forms.DateField(initial=date(datetime.now().year, 1, 1), widget=forms.TextInput(attrs={'title':date_help}))
    enddate = forms.DateField(initial=datetime.now().date(), widget=forms.TextInput(attrs={'title':date_help}))
    agent = forms.ModelMultipleChoiceField(queryset=Agent.objects.all(), label="Select agent")

    class Meta:
        model = Version
