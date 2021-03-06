#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2011-2013 Luca Wehrstedt <luca.wehrstedt@gmail.com>
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

import simplejson as json
import os
import sys
import pkg_resources


class Config(object):
    """An object holding the current configuration.

    """
    def __init__(self):
        """Fill this object with the default values for each key.

        """
        # Connection.
        self.bind_address = ''
        self.http_port = 8890
        self.https_port = None
        self.https_certfile = None
        self.https_keyfile = None
        self.timeout = 600  # 10 minutes (in seconds)

        # Authentication.
        self.realm_name = 'Scoreboard'
        self.username = 'usern4me'
        self.password = 'passw0rd'

        # Buffers
        self.buffer_size = 100  # Needs to be strictly positive.

        # Logging.
        self.log_color = True

        # File system.
        self.installed = sys.argv[0].startswith("/usr/") and \
            sys.argv[0] != '/usr/bin/ipython' and \
            sys.argv[0] != '/usr/bin/python2' and \
            sys.argv[0] != '/usr/bin/python'

        self.web_dir = pkg_resources.resource_filename("cmsranking", "static")
        if self.installed:
            self.log_dir = os.path.join("/", "var", "local", "log",
                                        "cms", "ranking")
            self.lib_dir = os.path.join("/", "var", "local", "lib",
                                        "cms", "ranking")
            paths = [os.path.join("/", "usr", "local", "etc",
                                  "cms.ranking.conf"),
                     os.path.join("/", "etc", "cms.ranking.conf")]
        else:
            self.log_dir = os.path.join("log", "ranking")
            self.lib_dir = os.path.join("lib", "ranking")
            paths = [os.path.join(".", "examples", "cms.ranking.conf"),
                     os.path.join("/", "usr", "local", "etc",
                                  "cms.ranking.conf"),
                     os.path.join("/", "etc", "cms.ranking.conf")]

        try:
            os.makedirs(self.lib_dir)
        except OSError:
            pass  # We assume the directory already exists...

        try:
            os.makedirs(self.web_dir)
        except OSError:
            pass  # We assume the directory already exists...

        try:
            os.makedirs(self.log_dir)
        except OSError:
            pass  # We assume the directory already exists...

        self._load(paths)

    def get(self, key):
        """Get the config value for the given key.

        """
        return getattr(self, key)

    def _load(self, paths):
        """Try to load the config files one at a time, until one loads
        correctly.

        """
        for conf_file in paths:
            try:
                self._load_unique(conf_file)
            except IOError:
                pass
            except json.decoder.JSONDecodeError as error:
                print "Unable to load JSON configuration file %s " \
                      "because of a JSON decoding error.\n%r" % (conf_file,
                                                                 error)
            else:
                print "Using configuration file %s." % conf_file
                return
        print "Warning: no configuration file found."

    def _load_unique(self, path):
        """Populate the Config class with everything that sits inside
        the JSON file path (usually something like /etc/cms.conf). The
        only pieces of data treated differently are the elements of
        core_services and other_services that are sent to async
        config.

        path (string): the path of the JSON config file.

        """
        # Load config file
        dic = json.load(open(path))

        # Put everything.
        for key in dic:
            setattr(self, key, dic[key])


# Create an instance of the Config class.
config = Config()
