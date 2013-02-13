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
import sys
import logging
import traceback
import xmlrpclib 

from django.conf import settings

from omero_qa.qa.models import Feedback, TestFile, AdditionalFile

logger = logging.getLogger('delegator-qa')

class UploadProccessing(object):
    
    def __init__(self, new_file, sid):
        self.new_file = new_file
        self.sid = str(sid)
    
    
    def create_init(self, selected_file):
        dir_path = self.create_dir()
        location = os.path.join(dir_path, "test_setup.ini").replace('\\','/')
        
        if not os.path.isfile(location):
            logger.debug("Createing init file: '%s'" % (location))

            t = self.new_file.name.split(".")
            ext = t[len(t)-1]

            output = open(location, 'w')
            try:
                output.write("""[populate_options]
filetypes = %s
exactfilesonly = true

[%s]""" % (ext,self.new_file.name))
            finally:
                output.flush()
                output.close()
                logger.debug("Init file was created: '%s'" % (location))
        else:
            logger.debug("Init file already exists: '%s'" % (location))            
            
    
    def create_init_from_feedback(self):
        dir_path = self.create_dir()
        location = os.path.join(dir_path, "test_setup.ini").replace('\\','/')
        
        logger.error("Head file was not sent. Create from the list.")
        logger.debug("Createing init file: '%s'" % (location))

        file_list = list()
        extension = None
        for f in Feedback.objects.get(pk=self.sid).test_files.all():
            t = f.file_name.split(".")
            ext = t[len(t)-1]
            if ext in f.file_format.selected.split(","): 
                extension = ext            
                file_list.append(str(f.file_name))
        
        files = ", ".join(file_list)
        output = open(location, 'wb+')
        try:
            output.write("""[populate_options]
filetypes = %s
exactfilesonly = true

[%s]""" % (extension,files))
        finally:
            output.flush()
            output.close()
            logger.debug("Init file was created: '%s'" % (location))

    
    def create_dir(self):
        dir_path = os.path.join(settings.UPLOAD_ROOT, self.sid).replace('\\','/')
        logger.debug("File is being saving in '%s'." % (dir_path))
        if not os.path.isdir(dir_path):
            try:
                os.mkdir(dir_path)
                logger.debug("Target path was created.")
            except Exception, x:
                logger.debug("Target path could not be created.")
                logger.error(traceback.format_exc())
                import sys
                exctype, value = sys.exc_info()[:2]
                raise exctype, value
        return dir_path
    
    
    def saveFile(self, file_format=None):
        dir_path = self.create_dir()
        file_path = os.path.join(dir_path, self.new_file.name).replace('\\','/')
        
        logger.debug("Writing to the file '%s' ..." % (file_path))
        fd = open(file_path, 'wb+')           
        for chunk in self.new_file.chunks():
            fd.write(chunk)
        fd.close()
        
        testfile = TestFile(file_name=self.new_file.name, file_format=file_format)
        testfile.save()
        logger.debug("File saved. ID: '%i'" % testfile.id)
        
        return testfile


def prepare_comparation(feedback):
    # feedback.selected_file, feedback.additional_files, feedback, feedback.test_files
    fileset = {'selected':None, 'existing':list(), 'missed':list(), 'unknown':list()}
    
    if feedback.app_name.id == 7:
        for tf in feedback.test_files.all():
            fileset['unknown'].append(tf)
    else:
        try:
            additionas = feedback.additional_files.all()
            logger.debug("Additional files: %i" % len(additionas))
            tests = feedback.test_files.all()
            logger.debug("Test files: %i" % len(tests))
            if len(additionas) > 0:
                test_files_list = dict()
                for tf in tests:
                    if feedback.selected_file is not None and feedback.selected_file != "" and tf.file_name == feedback.selected_file:
                        fileset['selected'] = tf
                    test_files_list[tf.file_name]=tf

                for af in additionas:
                    tf = test_files_list.get(af.file_name)
                    if tf is not None:
                        tf.file_path = af.file_path.endswith("/") and af.file_path or af.file_path+"/"
                        fileset['existing'].append(tf)
                    else:
                        fileset['missed'].append(af)
            else:
                if len(tests) > 0:
                    for tf in tests:
                        if feedback.selected_file is not None and feedback.selected_file != "" and tf.file_name == feedback.selected_file:
                            fileset['selected'] = tf
                        else:
                            fileset['unknown'].append(tf)
                else:
                    if feedback.selected_file is not None and feedback.selected_file != "":
                        fileset['missed'].append(AdditionalFile(file_name=feedback.selected_file))
        except Exception, x:
            logger.error(traceback.format_exc())
    
    logger.debug("Fileset: %s" % fileset)
    if fileset['selected'] is None and len(fileset['existing']) == 0 and len(fileset['missed']) == 0 and len(fileset['unknown']) == 0:
        fileset = None
    return fileset


def create_ticket(summary, description, trac, owner, cc=None):
    tid = None
    try:
        track_url = '%s%s:%s@%s/login/xmlrpc' % (trac.prefix, trac.username, trac.password, trac.url)
        logger.info("track_url %s" % track_url)
        server = xmlrpclib.ServerProxy(track_url) 

        reporter = trac.username
        attributes = {'type':'task', 'reporter':reporter, 'component':'from QA', 'owner':owner, 'cc':cc }

        tid = server.ticket.create(summary, description, attributes, True)
    except Exception, x:
        logger.error(traceback.format_exc())
    return tid


def add_comment(tid, comment, trac):
    try:
        track_url = '%s%s:%s@%s/login/xmlrpc' % (trac.prefix, trac.username, trac.password, trac.url)
        logger.info("track_url %s" % track_url)
        server = xmlrpclib.ServerProxy(track_url) 

        server.ticket.get(tid)
        attributes = {}
        server.ticket.update(int(tid), comment, attributes, True)
    except xmlrpclib.Fault, e:
        if e.faultCode == 2:
            return "Ticket %s does not exist on %s%s." % (tid, trac.prefix, trac.url)
        else:
            return e.faultString
    except Exception, x:
        logger.error(traceback.format_exc())
        return x
    return tid
