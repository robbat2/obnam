# Makefile for Obnam
# Copyright (C) 2006-2008  Lars Wirzenius <liw@liw.fi>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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

CC = gcc
CFLAGS = -D_GNU_SOURCE

all:

fadvise.so: fadvisemodule.c
	python setup.py build
	cp build/lib*/fadvise.so .
	rm -rf build

.PHONY: check
check: check-test-modules check-unittests check-licenses

.PHONY: check-test-modules
check-test-modules:
	bzr ls --versioned --kind=file | grep '\.py$$' | \
		xargs ./check-has-test-module

.PHONY: check-unittests
check-unittests:
	python -m CoverageTestRunner
	rm -f .coverage

.PHONY: check-licenses
check-licenses:
	bzr ls --versioned --kind=file | \
	    grep -Fxv -f check-license-exceptions | \
	    xargs ./check-license

.PHONY: clean
clean:
	rm -rf *~ */*~ *.pyc *.pyo */*.pyc */*.pyo tmp.* *,cover */*,cover build
	rm -f obnam.1 obnamfs.1 .coverage fadvise.so

