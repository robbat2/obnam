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


import unittest

import obnamlib


class WholeFileCheckSummerTests(unittest.TestCase):

    def test_computes_nothing_if_repo_wants_no_checksum(self):
        repo = FakeRepository(None)
        summer = obnamlib.WholeFileCheckSummer(repo)
        chunk = 'hello'
        token = repo.prepare_chunk_for_indexes(chunk)
        summer.append_chunk(chunk, token)
        self.assertEqual(summer.get_checksum(), None)

    def test_computes_checksum_for_md5(self):
        repo = FakeRepository(obnamlib.REPO_FILE_MD5)
        summer = obnamlib.WholeFileCheckSummer(repo)
        chunk = 'hello'
        token = repo.prepare_chunk_for_indexes(chunk)
        summer.append_chunk(chunk, token)
        self.assertEqual(
            summer.get_checksum(),
            '5d41402abc4b2a76b9719d911017c592')

    def test_computes_checksum_for_sha512(self):
        repo = FakeRepository(obnamlib.REPO_FILE_SHA512)
        summer = obnamlib.WholeFileCheckSummer(repo)
        chunk = 'hello'
        token = repo.prepare_chunk_for_indexes(chunk)
        summer.append_chunk(chunk, token)
        self.assertEqual(
            summer.get_checksum(),
            '9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca7'
            '2323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043')


class FakeRepository(object):

    def __init__(self, file_key):
        self._file_key = file_key

    def get_file_checksum_key(self):
        return self._file_key

    def prepare_chunk_for_indexes(self, data):
        if self._file_key is None:
            return None
        return 'fake checksum'
