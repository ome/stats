#!/usr/bin/env python
# 
# 
# 
# Copyright (c) 2012 University of Dundee. 
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

from omero_qa.feedback.models import EmailTemplate
from omero_qa.qa.models import FileFormat, TestFile, AppType, TracSystem, Trac, \
        Feedback, FeedbackStatus, TestEngineResult, ImportSession, AdditionalFile, \
        JUnitResult, TestNGXML, TestFile2, MetadataTest, MetadataTestResult, \
        NotificationList
from omero_qa.registry.models import Hit, Agent, IP, Continents, Version, DemoAccount

admin.site.register(EmailTemplate)

admin.site.register(FileFormat)
admin.site.register(TestFile)
admin.site.register(AppType)
admin.site.register(TracSystem)
admin.site.register(Trac)
admin.site.register(Feedback)
admin.site.register(FeedbackStatus)

admin.site.register(TestEngineResult)
admin.site.register(ImportSession)
admin.site.register(AdditionalFile)

admin.site.register(Hit)
admin.site.register(IP)
admin.site.register(Agent)
admin.site.register(Continents)
admin.site.register(Version)

admin.site.register(JUnitResult)
admin.site.register(TestNGXML)
admin.site.register(TestFile2)
admin.site.register(MetadataTest)
admin.site.register(MetadataTestResult)

admin.site.register(NotificationList)
admin.site.register(DemoAccount)
