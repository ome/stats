#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2012 Glencoe Software, Inc. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Launch the staging server.
"""

import subprocess
import traceback
import signal
import os

defaults = {
        "venv": os.path.join(os.path.expanduser("~"), "qa-virtualenv"),
        "file": "staging.pid",
        "conf": "staging-settings.py",
        "skip": "false",
        "dump": "feedback-backup.dump",
        "port": "10002",
        }


def _(*args, **kwargs):
    kwargs["shell"] = True
    return subprocess.check_call(*args, **kwargs)


def stop(pid):
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError:
        print "Failure deactivating!"
        traceback.print_exc()


def lookup(envname, defname):
    return os.environ.get(envname, defaults[defname])


def activate():
    venv = lookup("QA_VIRTUALENV", "venv")
    print "Turn on virtualenv", venv
    activate = os.path.join(venv, "bin", "activate_this.py")
    execfile(activate, dict(__file__=activate))


def cleanup():
    pidfile = lookup("QA_STAGING_FILE", "file")
    if os.path.exists(pidfile):
        f = open(pidfile)
        pid = f.read()
        f.close()
        print "Deactivating", pid
        stop(pid)
    else:
        print "No such file: ", pidfile
    return pidfile


def configure():
    config = lookup("QA_STAGING_SETTINGS", "conf")
    print "Configuring with", config
    _('cp "%s" omero_qa/settings.py' % config)


def restore():
    skip = lookup("QA_SKIP_RESTORE", "skip")
    if skip.lower() == "true":
        print "Skipping restore"
        return  # EARLY EXIT

    db = lookup("QA_DB_DUMP", "dump")
    print "Restoring database", db

    _('dropdb feedback-staging')
    _('createdb feedback-staging')
    _('pg_restore -O -Fc -d feedback-staging "%s"' % db)


def run(pidfile):
    port = lookup("QA_STAGING_PORT", "port")
    cmd = 'python manage.py runfcgi workdir=./ '
    cmd += 'method=prefork host=localhost port=%s ' % port
    cmd += 'maxchildren=5 minspare=1 maxspare=5 '
    cmd += 'daemonize=true pidfile="%s"' % pidfile
    _(cmd)


if __name__ == "__main__":
    activate()
    pidfile = cleanup()
    configure()
    restore()
    run(pidfile)
