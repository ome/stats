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

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


### MODELS ###    

class FileFormat(models.Model):
    """
    Any file format which should be assigned to an uploaded file.
    Where possible, versions should not be put in the name string
    in order to allow grouping the formats where the name is equal.
    """
    format_name = models.CharField(max_length=250)
    selected = models.CharField(max_length=50)
    additional = models.CharField(max_length=50, null=True)
    reader = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        ext = self.selected.split(",")
        e = ",".join([("*.%s" % e) for e in ext])
        if self.additional is not None:
            add = self.additional.split(",")            
            a = ",".join([("*.%s" % a) for a in add])
            c = "%s (%s,%s)" % (self.format_name, e, a)
        else:
            c = "%s (%s)" % (self.format_name, e)
        return c

    def extention_form(self):
        if self.additional is not None:
            extentions = "%s,%s" % (self.selected, self.additional)
        else:
            extentions = self.selected
        ext = extentions.split(",")
        f = ";".join([("*.%s" % e) for e in ext])
        return f


class TestFile(models.Model):
    file_name = models.CharField(max_length=250)
    file_path = models.TextField(blank=True)
    file_format = models.ForeignKey(FileFormat, blank=True, null=True)
    upload_date = models.DateTimeField(default=datetime.now)
    
    def __unicode__(self):
        c = "%s" % (self.file_name)
        return c


class AppType(models.Model):
    app_name = models.CharField(max_length=250)
    
    def __unicode__(self):
        c = "%s" % (self.app_name)
        return c
    
    def id_as_string(self):
        return str(self.id)


class TracSystem(models.Model):
    """
    Trac installation
    """
    name = models.CharField(max_length=50)
    prefix = models.CharField(max_length=250, default="http://")
    url = models.CharField(max_length=250)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    def __unicode__(self):
        c = "%s (%s)" % (self.name, self.url)
        return c


class Trac(models.Model):
    """
    Trac installation
    """
    ticket = models.IntegerField()
    system = models.ForeignKey(TracSystem)

    def __unicode__(self):
        c = "%s in  %s" % (self.ticket, self.system)
        return c


class ImportSession(models.Model):
    
    import_id = models.CharField(max_length=50)

    def __unicode__(self):
        c = "%s" % (self.import_id)
        return c


class FeedbackStatus(models.Model):
    
    status = models.CharField(max_length=250)
    
    def __unicode__(self):
        return self.status


class UserComment(models.Model):
    
    comment = models.TextField()
    creation_date = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey(User, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    def __unicode__(self):
        return self.comment
    
    def user_or_email(self):
        if self.user is not None:
            if self.user.first_name is not None and len(self.user.first_name) > 0 and self.user.last_name is not None and len(self.user.last_name) > 0:
                return "%s %s (%s)" % (self.user.first_name, self.user.last_name, self.user.username)
            else:
                return "%s (%s)" % (self.user.email, self.user.username)
        elif self.email is not None:
            return self.email
        else:
            return 'unknown'
    
    def short_email(self):
        try:
            if self.user is not None:
                em = self.user.email            
            elif self.email is not None and len(self.email) > 0:
                em = self.email
            em = em.split("@")
            return "%s@..." % (em[0])
        except:
            return 'unknown'

class AdditionalFile(models.Model):
    
    file_name = models.TextField()
    file_path = models.TextField(blank=True)
    file_size = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        c = "%s - %s" % (self.file_name, self.file_size)
        return c
        

class Feedback(models.Model):
    """
    Also stores upgrade checks and validation requests. Essentially any
    user connection to the QA system will be stored as a feedback. Views
    will only show certain feedback items to developers for action.
    """
    app_name = models.ForeignKey(AppType, blank=True, null=True)
    ip_address = models.CharField(max_length=20, blank=True)
    java_version = models.CharField(max_length=50, blank=True)
    java_classpath = models.TextField(blank=True)
    python_version = models.CharField(max_length=50, blank=True)
    python_classpath = models.TextField(blank=True)
    os_name = models.CharField(max_length=250, blank=True)
    os_arch = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)
    app_version = models.CharField(max_length=250, blank=True)
    extra = models.CharField(max_length=250, blank=True, null=True)
    error = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    ticket = models.ManyToManyField(Trac, blank=True, null=True)
    absolute_path = models.TextField(blank=True)
    selected_file = models.TextField(blank=True)
    additional_files = models.ManyToManyField(AdditionalFile, blank=True, null=True)
    test_files = models.ManyToManyField(TestFile, blank=True, null=True)
    creation_date = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey(User, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    token = models.CharField(max_length=50)
    status = models.ForeignKey(FeedbackStatus, default=1)
    import_session = models.ForeignKey(ImportSession, blank=True, null=True)
    user_comment = models.ManyToManyField(UserComment, blank=True, null=True)

    def __unicode__(self):
        c = "%s" % (self.token)
        return c
    
    def checkSelectedFile(self):
        test_files_list=[tf.file_name for tf in self.test_files.all()]
        for af in self.additional_files.all():
            if not af.file_name in test_files_list:
                return False
        if self.selected_file is None or len(self.selected_file)<1:
            return True
        return True
    
    def short_app_name(self):
        try:
            res = "%s %s" % (self.app_name.app_name.split(" ")[0], self.app_version.replace("Beta-", "").replace("Beta", "")[:10])
        except:
            res = self.app_name.app_name
        return res
    
    def only_email(self):
        if self.user is not None:
            return "%s" % (self.user.email)
        elif self.email is not None:
            return self.email
        else:
            return None
    
    def user_or_email(self):
        if self.user is not None:
            if self.user.first_name is not None and len(self.user.first_name) > 0 and self.user.last_name is not None and len(self.user.last_name) > 0:
                return "%s %s (%s)" % (self.user.first_name, self.user.last_name, self.user.username)
            else:
                return "%s (%s)" % (self.user.email, self.user.username)
        elif self.email is not None:
            return self.email
        else:
            return 'unknown'
    
    def short_user_or_email(self):
        if self.user is not None:
            return "%s" % (self.user.username[:12])
        elif self.email is not None and len(self.email) > 0:
            return "%s..." % self.email[:12]
        else:
            return 'unknown'
    
    def short_error(self):
        err = self.error
        l = len(err)
        if err is None or l<1:
            return None
        if l < 25:
            return err
        return err[:25] + "..."
    
    def short_comment(self):
        cm = self.comment
        l = len(cm)
        if cm is None or l<1:
            return None
        if l < 30:
            return cm
        return cm[:30] + "..."
    
    def short_selected_file(self):
        sf = self.selected_file 
        l = len(sf)
        if sf is None or l<1:
            return None
        if l < 30:
            return sf
        return "..." + sf[l - 30:]
    
class TestEngineResult(models.Model):

    test_file = models.ForeignKey(TestFile)
    started = models.DateTimeField(blank=True, null=True)
    ended = models.DateTimeField(blank=True, null=True)
    error = models.TextField(blank=True)

    repo_java_version = models.CharField(max_length=50, blank=True)
    repo_java_classpath = models.TextField(blank=True)
    repo_python_version = models.CharField(max_length=50, blank=True)
    repo_python_classpath = models.TextField(blank=True)
    repo_os_name = models.CharField(max_length=50, blank=True)
    repo_os_arch = models.CharField(max_length=50, blank=True)
    repo_os_version = models.CharField(max_length=50, blank=True)
    support_level = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        c = "%s" % (self.test_file)
        return c


## METADATA Validator ##
class MetadataTest(models.Model):

    test_name = models.CharField(max_length=250)
    class_name = models.CharField(max_length=250)
    
    def __unicode__(self):
        c = "%s %s" % (self.class_name, self.test_name)
        return c


class MetadataTestResult(models.Model):

    test = models.ForeignKey(MetadataTest)
    result = models.NullBooleanField(null=True, blank=True)
    failed_since = models.CharField(max_length=50, default=0)
    error = models.TextField(null=True, blank=True)
    
    def __unicode__(self):
        c = "%s - %s" % (self.test.test_name, self.result)
        return c


class TestFile2(models.Model):
    
    file_path = models.CharField(max_length=250)
    file_format = models.ForeignKey(FileFormat, blank=True, null=True)
    test_result = models.ManyToManyField(MetadataTestResult, blank=True, null=True)
    
    def __unicode__(self):
        c = "%s" % (self.file_path)
        return c


class TestNGXML(models.Model):
    
    junit_result = models.CharField(max_length=250)
    testng_file = models.CharField(max_length=250)
    hudson_build = models.CharField(max_length=10)
    omero_build = models.CharField(max_length=10)
    bioformats_build = models.CharField(max_length=10)
    creation_date = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        c = "%s" % (self.hudson_build)
        return c


class JUnitResult(models.Model):
    
    xml_file = models.ForeignKey(TestNGXML)
    test_file = models.ForeignKey(TestFile2)

    def __unicode__(self):
        c = "%s" % (self.xml_file)
        return c


## BEING NOTIFIED MODEL##

class NotificationList(models.Model):
    """
    Any email address or user who should be asssigned to the object 
    and notified.
    """
    app_name = models.ForeignKey(AppType, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)
    email = models.EmailField(blank=True)
        
    def __unicode__(self):
        who = self.user and self.user.email or self.email
        c = "%s %s" % (self.app_name.app_name, who)
        return c
