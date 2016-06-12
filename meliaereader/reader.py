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


import sys

import json

import obnamlib


class MeliaeReader(object):

    def __init__(self):
        self._objs = {}
        self._closures = {}

    def __iter__(self):
        return iter(self._objs.values())

    def __contains__(self, ref):
        return ref in self._objs

    def __len__(self):
        return len(self._objs)

    def read(self, filename):
        with open(filename) as f:
            for line in f:
                obj = json.loads(line)
                self._objs[obj['address']] = obj

    def get_total_size(self):
        return self.get_size(self._objs.values())

    def get_size(self, objs):
        return sum(o['size'] for o in objs)

    def get_types(self):
        return set(o['type'] for o in self)

    def get_obnam_types(self):  # pragma: no cover
        return set(o['type'] for o in self if hasattr(obnamlib, o['type']))

    def get_objs_of_type(self, typename):
        return [o for o in self if o['type'] == typename]

    def get_closure(self, obj):
        sys.stderr.write('get_closure({})\n'.format(obj['address']))
        ref = obj['address']
        if ref not in self._closures:
            refs = self._closures[ref] = set()
            refs.add(ref)
            for child_ref in obj['refs']:
                if child_ref in self:
                    child = self.get_object(child_ref)
                    for child_obj in self.get_closure(child):
                        refs.add(child_obj['address'])
        return [self.get_object(r) for r in self._closures[ref]]

    def get_object(self, ref):
        if ref in self:
            return self._objs[ref]
        raise Exception('No object with address {}'.format(ref))

    def get_closure_of_type(self, typename):
        sys.stderr.write('get_closure_of_type({})\n'.format(typename))
        type_closure = {}
        for obj in self.get_objs_of_type(typename):
            for o in self.get_closure(obj):
                type_closure[o['address']] = o
        return type_closure.values()
