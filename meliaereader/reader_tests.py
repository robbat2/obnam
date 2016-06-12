# Copyright 2016  Lars Wirzenius
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =*= License: GPL-3+ =*=


import json
import os
import shutil
import tempfile
import unittest

import meliaereader


class MeliaeReaderTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_file(self, *objs):
        fd, filename = tempfile.mkstemp(dir=self.tempdir)
        os.close(fd)
        with open(filename, 'w') as f:
            for obj in objs:
                f.write('{}\n'.format(json.dumps(obj)))
        return filename

    def make_object(self, **kwargs):
        return kwargs

    def test_has_no_objects_initially(self):
        mr = meliaereader.MeliaeReader()
        self.assertEqual(len(mr), 0)

    def test_reads_an_empty_file(self):
        mr = meliaereader.MeliaeReader()
        mr.read('/dev/null')
        self.assertEqual(len(mr), 0)

    def test_reads_file_with_one_object(self):
        filename = self.make_file(self.make_object())
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(len(mr), 1)

    def test_get_object_raises_exception_if_not_found(self):
        mr = meliaereader.MeliaeReader()
        self.assertRaises(Exception, mr.get_object, 1)

    def test_get_object_returns_object_if_found(self):
        obj = self.make_object(type='foo', address=1)
        filename = self.make_file(obj)
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(mr.get_object(obj['address']), obj)

    def test_reports_total_size_correctly(self):
        obj = self.make_object(type='foo', address=1, size=42)
        filename = self.make_file(obj)
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(mr.get_total_size(), 42)

    def test_report_size_for_list_of_objects_correctly(self):
        obj = self.make_object(type='foo', address=1, size=42)
        filename = self.make_file(obj)
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(mr.get_size([obj]), 42)

    def test_readings_adds_to_existing_objs(self):
        filename_1 = self.make_file(self.make_object())
        filename_2 = self.make_file(self.make_object())
        mr = meliaereader.MeliaeReader()
        mr.read(filename_1)
        mr.read(filename_2)
        self.assertEqual(len(mr), 2)

    def test_reports_object_types(self):
        filename = self.make_file(self.make_object(type='foo'))
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(mr.get_types(), set(['foo']))

    def test_reports_objs_of_type(self):
        obj_1 = self.make_object(type='foo')
        obj_2 = self.make_object(type='bar')
        filename = self.make_file(obj_1, obj_2)
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(sorted(mr.get_types()), ['bar', 'foo'])
        self.assertEqual(mr.get_objs_of_type('foo'), [obj_1])
        self.assertEqual(mr.get_objs_of_type('bar'), [obj_2])
        self.assertEqual(mr.get_objs_of_type('nonononono'), [])

    def test_reports_closure_for_object(self):
        obj_1 = self.make_object(type='foo', address=1, refs=[2])
        obj_2 = self.make_object(type='bar', address=2, refs=[])
        filename = self.make_file(obj_1, obj_2)
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(mr.get_closure(obj_1), [obj_1, obj_2])
        self.assertEqual(mr.get_closure(obj_2), [obj_2])

    def test_reports_closure_for_type(self):
        obj_1 = self.make_object(type='foo', address=1, refs=[2])
        obj_2 = self.make_object(type='bar', address=2, refs=[])
        filename = self.make_file(obj_1, obj_2)
        mr = meliaereader.MeliaeReader()
        mr.read(filename)
        self.assertEqual(list(mr), [obj_1, obj_2])
        self.assertEqual(mr.get_closure_of_type('foo'), [obj_1, obj_2])
        self.assertEqual(mr.get_closure_of_type('bar'), [obj_2])
