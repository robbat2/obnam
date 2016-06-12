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


class MeliaeReader(object):

    def __init__(self):
        self._objs = []

    def __iter__(self):
        return iter(self._objs)

    def __contains__(self, ref):
        return any(o['address'] == ref for o in self)

    def __len__(self):
        return len(self._objs)

    def read(self, filename):
        with open(filename) as f:
            self._objs.extend(json.loads(line) for line in f)

    def get_total_size(self):
        return self.get_size(self._objs)

    def get_size(self, objs):
        return sum(o['size'] for o in objs)

    def get_types(self):
        return set(o['type'] for o in self)

    def get_objs_of_type(self, typename):
        return [o for o in self if o['type'] == typename]

    def get_closure(self, obj):
        closure = []
        todo = [obj]
        done = set()
        while todo:
            o = todo.pop(0)
            done.add(o['address'])
            closure.append(o)
            for ref in o['refs']:
                if ref not in done and ref in self:
                    todo.append(self.get_object(ref))
        return closure

    def get_object(self, ref):
        for obj in self:
            if obj['address'] == ref:
                return obj
        raise Exception('No object with address {}'.format(ref))

    def get_closure_of_type(self, typename):
        type_closure = {}
        for obj in self.get_objs_of_type(typename):
            for o in self.get_closure(obj):
                type_closure[o['address']] = o
        return type_closure.values()
