# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Storage class test."""

from __future__ import absolute_import, print_function

import time
from os import utime
from os.path import exists, getmtime, join

from pywebpack.storage import FileStorage, iter_files


def test_iterfiles(sourcedir):
    """Test file iteration."""
    assert [x[1] for x in iter_files(sourcedir)] == [
        'buildtpl/package.json',
        'buildtpl/webpack.config.js',
        'bundle/index.js',
        'simple/index.js',
        'simple/package.json',
        'simple/webpack.config.js',
    ]


def test_filestorage(sourcedir, tmpdir):
    """Test file storage copy."""
    fsrc = join(sourcedir, 'simple/package.json')
    fdst = join(tmpdir, 'simple/package.json')

    fs = FileStorage(sourcedir, tmpdir)

    # File is copied
    assert not exists(fdst)
    fs.run()
    assert exists(fdst)

    # File is *not* copied (not modified)
    mtime = getmtime(fdst)
    assert mtime > getmtime(fsrc)
    fs.run()
    assert getmtime(fdst) == mtime

    # File is copied (source was modified)
    time.sleep(1)
    utime(fsrc)
    assert mtime < getmtime(fsrc)
    fs.run()
    assert getmtime(fdst) >= getmtime(fsrc)
