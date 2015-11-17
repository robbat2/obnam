# Copyright 2015  Lars Wirzenius
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


import hashlib
import os

import obnamlib


class GAChunkIndexes(object):

    def __init__(self):
        self._fs = None
        self.set_dirname('chunk-indexes')
        self.clear()

    def set_fs(self, fs):
        self._fs = fs

    def set_dirname(self, dirname):
        self._dirname = dirname

    def get_dirname(self):
        return self._dirname

    def clear(self):
        self._data = {}
        self._data_is_loaded = False

    def commit(self):
        self._load_data()
        self._save_data()

    def _save_data(self):
        blob = obnamlib.serialise_object(self._data)
        filename = self._get_filename()
        self._fs.overwrite_file(filename, blob)

    def _get_filename(self):
        return os.path.join(self.get_dirname(), 'data.dat')

    def prepare_chunk_for_indexes(self, chunk_content):
        return hashlib.sha512(chunk_content).hexdigest()

    def put_chunk_into_indexes(self, chunk_id, token, client_id):
        self._load_data()

        by_chunk_id = self._data['by_chunk_id']
        by_chunk_id[chunk_id] = token

        by_checksum = self._data['by_checksum']['sha512']
        chunk_ids = by_checksum.get(token, [])
        if chunk_id not in chunk_ids:
            chunk_ids.append(chunk_id)
            by_checksum[token] = chunk_ids

        used_by = self._data['used_by']
        client_ids = used_by.get(chunk_id, [])
        if client_id not in client_ids:
            client_ids.append(client_id)
            used_by[chunk_id] = client_ids

    def _load_data(self):
        if not self._data_is_loaded:
            filename = self._get_filename()
            if self._fs.exists(filename):
                blob = self._fs.cat(filename)
                self._data = obnamlib.deserialise_object(blob)
                assert self._data is not None
            else:
                self._data = {
                    'by_chunk_id': {
                    },
                    'by_checksum': {
                        'sha512': {},
                    },
                    'used_by': {
                    },
                }
            self._data_is_loaded = True

    def find_chunk_ids_by_content(self, chunk_content):
        self._load_data()

        token = self.prepare_chunk_for_indexes(chunk_content)
        by_checksum = self._data['by_checksum']['sha512']
        result = by_checksum.get(token, [])

        if not result:
            raise obnamlib.RepositoryChunkContentNotInIndexes()
        return result

    def remove_chunk_from_indexes(self, chunk_id, client_id):
        self._load_data()

        used_by = self._data['used_by']
        client_ids = used_by.get(chunk_id, [])
        if client_id in client_ids:
            client_ids.remove(client_id)
            if client_ids:
                used_by[chunk_id] = client_ids
                still_used = True
            else:
                del used_by[chunk_id]
                still_used = False

        if not still_used:
            by_chunk_id = self._data['by_chunk_id']
            token = by_chunk_id.get(chunk_id, None)
            if token is not None:
                del by_chunk_id[chunk_id]

            by_checksum = self._data['by_checksum']['sha512']
            chunk_ids = by_checksum.get(token, [])
            if chunk_id in chunk_ids:
                chunk_ids.remove(chunk_id)
                if chunk_ids:
                    by_checksum[token] = chunk_ids
                else:
                    del by_checksum[token]

    def remove_chunk_from_indexes_for_all_clients(self, chunk_id):
        self._load_data()

        by_chunk_id = self._data['by_chunk_id']
        token = by_chunk_id.get(chunk_id, None)
        if token is not None:
            del by_chunk_id[chunk_id]

        by_checksum = self._data['by_checksum']['sha512']
        chunk_ids = by_checksum.get(token, [])
        if chunk_id in chunk_ids:
            chunk_ids.remove(chunk_id)
            if chunk_ids:
                by_checksum[token] = chunk_ids
            else:
                del by_checksum[token]

        used_by = self._data['used_by']
        if chunk_id in used_by:
            del used_by[chunk_id]

    def validate_chunk_content(self, chunk_id):
        return None
