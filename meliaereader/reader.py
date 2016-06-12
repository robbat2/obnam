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
        self._objs = {}  # ref to object
        self._closures = {}  # ref to list of refs

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
        self.compute_closures()

    def get_total_size(self):
        return self.get_size(self._objs.values())

    def get_size(self, objs):
        return sum(o['size'] for o in objs)

    def get_types(self):
        return set(o['type'] for o in self)

    def get_obnam_types(self):  # pragma: no cover
        return set(
            o['type']
            for o in self
            if hasattr(obnamlib, o['type'])
        )

    def get_objs_of_type(self, typename):
        return [o for o in self if o['type'] == typename]

    def compute_closures(self):
        sys.stderr.write('computing closures for {} objects'.format(len(self)))

        all_refs = self._objs.keys()

        # Set all closures to be just the object itself.
        for ref in all_refs:
            self._closures[ref] = set([ref])

        # Find new objects that can be reached from current closures.
        # Repeat until no more.
        added = True
        while added:
            added = False
            for ref in all_refs:
                added = self.add_to_closure(ref) or added

        assert set(self._objs.keys()) == set(self._closures.keys())

    def add_to_closure(self, ref):
        added = False
        closure = self._closures[ref]
        children = [self.get_object(r) for r in closure]
        for child in children:
            delta = set(child['refs']).difference(closure)
            if delta:
                for r in delta:
                    if r in self:
                        closure.add(r)
                added = True
        return added

    def _simple_get_closure(self, ref):  # pragma: no cover
        closure = set()
        todo = set([ref])
        done = set()
        while todo:
            ref = todo.pop()
            done.add(ref)
            if ref in self._closures:
                closure = closure.union(self._closures[ref])
            else:
                closure.add(ref)
                obj = self.get_object(ref)
                for child_ref in obj['refs']:
                    if child_ref not in done and child_ref in self:
                        todo.add(child_ref)

        return closure

    def get_closure(self, obj, indent=0):
        ref = obj['address']
        assert ref in self._closures, 'ref {} not in _closures'.format(ref)
        return [self.get_object(r) for r in self._closures[ref]]

    def get_object(self, ref):
        if ref in self:
            return self._objs[ref]
        raise Exception('No object with address {}'.format(ref))

    def get_closure_of_type(self, typename):
        sys.stderr.write('get_closure_of_type({})\n'.format(typename))
        type_closure = {}
        for obj in self.get_objs_of_type(typename):
            for o in self.get_closure(obj, indent=1):
                type_closure[o['address']] = o
        return type_closure.values()
