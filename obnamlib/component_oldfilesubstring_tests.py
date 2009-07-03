# Copyright (C) 2009  Lars Wirzenius <liw@liw.fi>
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


import unittest

import obnamlib


class OldFileSubStringTests(unittest.TestCase):

    def setUp(self):
        self.offset = 42
        self.length = 42*2
        self.ofss = obnamlib.OldFileSubString(self.offset, self.length)
        
    def test_sets_offset_correctly(self):
        self.assertEqual(self.ofss.offset, self.offset)
        
    def test_sets_length_correctly(self):
        self.assertEqual(self.ofss.length, self.length)

