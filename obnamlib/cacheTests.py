# Copyright (C) 2006  Lars Wirzenius <liw@iki.fi>
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


"""Unit tests for obnamlib.cache"""


import os
import shutil
import unittest

import obnamlib


class CacheBase(unittest.TestCase):

    def setUp(self):
        self.cachedir = "tmp.cachedir"
        
        config_list = (
            ("backup", "cache", self.cachedir),
        )
    
        self.config = obnamlib.cfgfile.ConfigFile()
        for section, item, value in config_list:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, item, value)

    def tearDown(self):
        if os.path.exists(self.cachedir):
            shutil.rmtree(self.cachedir)
        del self.cachedir
        del self.config


class InitTests(CacheBase):

    def testInit(self):
        cache = obnamlib.cache.Cache(self.config)
        self.failIf(os.path.isdir(self.cachedir))


class PutTests(CacheBase):

    def testPut(self):
        cache = obnamlib.cache.Cache(self.config)
        id = "pink"
        block = "pretty"
        cache.put_block(id, block)
        
        pathname = os.path.join(self.cachedir, id)
        self.failUnless(os.path.isfile(pathname))
        f = file(pathname, "r")
        self.failUnlessEqual(f.read(), block)
        f.close()


class GetTests(CacheBase):

    def testGet(self):
        cache = obnamlib.cache.Cache(self.config)
        id = "pink"
        block = "pretty"
        self.failUnlessEqual(cache.get_block(id), None)

        cache.put_block(id, block)
        self.failUnlessEqual(cache.get_block(id), block)
