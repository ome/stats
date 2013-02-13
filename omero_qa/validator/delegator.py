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
import time
from datetime import datetime, date

from django.conf import settings

from omero_qa.qa.models import FileFormat
from omero_qa.validator.validator import *

logger = logging.getLogger('delegator-validator')

class UploadProccessing(object):
    
    def __init__(self, new_file, sid):
        self.new_file = new_file
        self.sid = str(sid)
    

    def create_dir(self):
        dir_path = os.path.join(settings.VALIDATOR_UPLOAD_ROOT, self.sid).replace('\\','/')
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
    
    
    def saveFile(self):
        now = datetime.now()
        dir_path = self.create_dir()
        file_name = "%s_%s" % (now.strftime("%Y_%m_%d_%H_%M_%S"), self.new_file.name)
        
        file_path = os.path.join(dir_path, file_name).replace('\\','/')
        
        logger.debug("Writing to the file '%s' ..." % (file_path))
        fd = open(file_path, 'wb+')           
        for chunk in self.new_file.chunks():
            fd.write(chunk)
        fd.close()
        
        logger.debug("File saved")

class FileValidation(object):
    
    schema = None
    result = None
    file_name = None
    
    def __init__(self, sid):
        self.sid = str(sid)
        self.dir_path = os.path.join(settings.VALIDATOR_UPLOAD_ROOT, self.sid).replace('\\','/')
    
    def count_files(self):
        if os.path.isdir(self.dir_path):
            self.counter = len(os.listdir(self.dir_path))
        else:
            self.dir_list = list()
            self.counter = 0
    
    def read_files(self):
        if os.path.isdir(self.dir_path):
            self.dir_list = os.listdir(self.dir_path)
            self.counter = len(os.listdir(self.dir_path))
        else:
            self.dir_list = list()
            self.counter = 0
        
    def validate(self, file_name):
        self.file_name = file_name        
        filepath = os.path.join(self.dir_path, self.file_name).replace('\\','/')
        if not os.path.isfile(filepath):
            raise AttributeError("File does not exist.")
        else:
			sufix=file_name.split('.')
			size=len(sufix)
	
			if sufix[size-1] =='tif' or sufix[size-1] =='tiff':
				result = XmlReport().validateTiff(filepath)
			else: 
				result = XmlReport.validateFile(filepath)
		
			#more
			if result.theNamespace == 'http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd' and result.isOmeTiff:
				schema = 'http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd (OME-TIFF variant)'
			elif result.theNamespace == 'http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd' and not result.isOmeTiff:
				schema = 'http://www.openmicroscopy.org/XMLschemas/OME/FC/ome.xsd (Standard)'
			elif result.theNamespace == "http://www.openmicroscopy.org/Schemas/OME/2007-06":
				schema = "http://www.openmicroscopy.org/Schemas/OME/2007-06 (Standard V2)"
			elif result.theNamespace == "http://www.openmicroscopy.org/Schemas/OME/2008-02":
				schema = "http://www.openmicroscopy.org/Schemas/OME/2008-02 (Standard V2)"
			elif result.theNamespace == "http://www.openmicroscopy.org/Schemas/OME/2008-09":
				schema = "http://www.openmicroscopy.org/Schemas/OME/2008-09 (Standard V1)"
			else:
				schema = "No schema found - using http://www.openmicroscopy.org/Schemas/OME/2008-09 (Standard V1)"
			self.result = result
			self.schema = schema

    def delete(self, file_name):
        self.file_name = file_name        
        filepath = os.path.join(self.dir_path, self.file_name).replace('\\','/')
        if not os.path.isfile(filepath):
            raise AttributeError("File does not exist.")
        else:
            os.remove(filepath)
			