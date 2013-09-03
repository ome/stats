import datetime
import traceback
import logging
import json

from django import template

register = template.Library()

logger = logging.getLogger(__name__)

@register.filter
def hash(h, key):
    return h[key]