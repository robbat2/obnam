# Makefile for Obnam
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

CC = gcc
CFLAGS = -D_GNU_SOURCE

prefix = /usr/local
bindir = $(prefix)/bin
libdir = $(prefix)/lib
sharedir = $(prefix)/share
mandir = $(sharedir)/man
man1dir = $(mandir)/man1
pydir = $(libdir)/python2.5
sitedir = $(pydir)/site-packages

all: obnam.1 obnamfs.1 fadvise.so

version:
	./obnam --version

obnam.1: obnam.docbook
	docbook2x-man --encoding utf8 obnam.docbook

obnamfs.1: obnamfs.docbook
	docbook2x-man --encoding utf8 obnamfs.docbook

fadvise.so: fadvisemodule.c
	python setup.py build
	cp build/lib*/fadvise.so .
	rm -rf build

check: all
	python -m CoverageTestRunner
	rm -f .coverage
	sh blackboxtests tests/*
	./xxx-restore-etc-old-style
	./check-options
	bzr ls --versioned --kind=file | \
	    grep -Fxv -f check-license-exceptions | \
	    xargs ./check-license

clean:
	rm -rf *~ */*~ *.pyc *.pyo */*.pyc */*.pyo tmp.* *,cover */*,cover build
	rm -f obnam.1 obnamfs.1 .coverage fadvise.so


install: all
	install -d $(bindir)
	install obnam $(bindir)/obnam
	install obnamfs.py $(bindir)/obnamfs
	install -d $(man1dir)
	install -m 0644 *.1 $(man1dir)
	install -d $(sitedir)/obnam
	install -m 0644 obnam/*.py $(sitedir)/obnam
	python2.5 fixup-defaults.py \
	    --gpg-encrypt-to= \
	    --gpg-home= \
	    --gpg-sign-with= \
	    --ssh-key= \
	    --store= \
	    --host-id= \
	    --cache= \
	    > $(sitedir)/obnam/defaultconfig.py
