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

from datetime import datetime

from django.db import models
from django import forms
from django.forms import ModelForm
from django.conf import settings

### MODELS ###

class Version(models.Model):
    
    version = models.CharField(max_length=50)

    def __unicode__(self):
        return self.version


class DemoAccount(models.Model):
    """
    Enqiry for account on Demo server
    """
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    institution = models.CharField(max_length=250)
    email = models.EmailField()

    def __unicode__(self):
        return self.email


class Agent(models.Model):
    """
    Agent
    """
    agent_name = models.CharField(max_length=250)
    display_name = models.CharField(max_length=250)
    
    def __unicode__(self):
        c = "%s" % (self.display_name)
        return c


class IP(models.Model):
    
    ip = models.CharField(max_length=20, unique=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    country = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        c = "%s" % (self.ip)
        return c

        
class Hit(models.Model):
     
    ip = models.ForeignKey(IP)
    poll = models.IntegerField(blank=True, null=True)
    creation_date = models.DateTimeField(default=datetime.now)
    agent = models.ForeignKey(Agent)
    agent_version = models.CharField(max_length=250, blank=True, null=True)
    os_name = models.CharField(max_length=250, blank=True, null=True)
    os_arch = models.CharField(max_length=250, blank=True, null=True)
    os_version = models.CharField(max_length=250, blank=True, null=True)
    java_vendor = models.CharField(max_length=250, blank=True, null=True)
    java_version = models.CharField(max_length=250, blank=True, null=True)
    python_version = models.CharField(max_length=50, blank=True, null=True)
    python_compiler = models.CharField(max_length=50, blank=True, null=True)
    python_build = models.CharField(max_length=50, blank=True, null=True)
    header = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        c = "%s %s: %s" % (self.ip, self.agent.agent_name, self.agent_version)
        return c


class Continents(models.Model):
    continent_name = models.CharField(max_length=20)
    n = models.FloatField()
    s = models.FloatField()
    w = models.FloatField()
    e = models.FloatField()
    centerx = models.FloatField()
    centery = models.FloatField()
    zoom = models.IntegerField()

    def __unicode__(self):
        c = "%s" % (self.continent_name)
        return c
        
### FORMS ###

class DemoAccountForm(ModelForm):
    
    class Meta:
        model = DemoAccount
    
    def clean_email(self):
        if len(self.cleaned_data['email']) < 5:
             raise forms.ValidationError('This is not a valid email address.')
        try:
            DemoAccount.objects.get(email=self.cleaned_data['email'])
        except DemoAccount.DoesNotExist:
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError('This email already exist.')


class ContinentsForm(forms.Form):

    continent = forms.ModelChoiceField(queryset=Continents.objects.all(), label="Select region: ", widget=forms.Select(attrs={'onchange':'window.location.href=\'?continent=\'+this.options[this.selectedIndex].value'}))


class AgentForm(forms.Form):

    agent = forms.ModelChoiceField(queryset=Agent.objects.all(), label="Select agent: ", widget=forms.Select(attrs={'onchange':'window.location.href=\'?agent=\'+this.options[this.selectedIndex].value'}))
