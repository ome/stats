#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#
# Copyright (c) 2009-2013 University of Dundee.
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
from django.contrib import admin

from omerostats.registry.models import Version, Hit, Agent, AgentVersion, \
    OSName, OSArch, OSVersion, JavaVendor, JavaVersion, \
    PythonVersion, PythonCompiler, PythonBuild, \
    IP, Continent, Country, City, Organisation, Host, Domain, Suffix


admin.site.register(Version)

admin.site.register(Hit)

admin.site.register(Agent)
admin.site.register(AgentVersion)
admin.site.register(OSName)
admin.site.register(OSArch)
admin.site.register(OSVersion)
admin.site.register(JavaVendor)
admin.site.register(JavaVersion)
admin.site.register(PythonVersion)
admin.site.register(PythonCompiler)
admin.site.register(PythonBuild)

admin.site.register(IP)
admin.site.register(Continent)
admin.site.register(Country)
admin.site.register(City)
admin.site.register(Organisation)
admin.site.register(Host)
admin.site.register(Domain)
admin.site.register(Suffix)
