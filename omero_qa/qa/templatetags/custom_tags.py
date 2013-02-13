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


import datetime
import re
import urlparse

from django.conf import settings
from django import template
from django.template import Library
from django.template.defaulttags import URLNode, url
from django.contrib.sites.models import Site
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy

register = Library()

@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)


@register.filter
def classpathlinebreaks(value):
    """
    Replaces separator in python class path a single
    newline becomes an HTML line break (``<br />``).
    """
    value = re.sub(r'\[|\]|\'', ',', force_unicode(value)) # normalize newlines
    paras = re.split(',', value)
    paras = [u'<p>%s</p>' % p.strip().replace(',', '<br />') for p in paras]
    return u'\n\n'.join(paras)
classpathlinebreaks = allow_lazy(classpathlinebreaks, unicode)


@register.filter
def short_name(value):
    """
    Replaces separator in python class path a single
    newline becomes an HTML line break (``<br />``).
    """
    l = len(force_unicode(value))
    if l > 65:
        name = value[:35] + "..." + value[l - 25:]
    else:
        name = value
    return unicode(name)
short_name = allow_lazy(short_name, unicode)


class AbsoluteURLNode(URLNode):
    def render(self, context):
        path = super(AbsoluteURLNode, self).render(context)
        domain = "http://%s" % Site.objects.get_current().domain
        return urlparse.urljoin(domain, path)

def absurl(parser, token, node_cls=AbsoluteURLNode):
    """Just like {% url %} but ads the domain of the current site."""
    node_instance = url(parser, token)
    return node_cls(view_name=node_instance.view_name,
        args=node_instance.args,
        kwargs=node_instance.kwargs,
        asvar=node_instance.asvar)
absurl = register.tag(absurl)        


# makes settings available in template
@register.tag
def setting ( parser, token ): 
    try:
        tag_name, option = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents[0]
    return SettingNode( option )

class SettingNode ( template.Node ): 
    def __init__ ( self, option ): 
        self.option = option

    def render ( self, context ): 
        # if FAILURE then FAIL silently
        try:
            return str(settings.__getattr__(self.option))
        except:
            return ""
