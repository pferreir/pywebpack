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

"""Webpack manifests API."""

from __future__ import absolute_import, print_function

import json
import sys
from os.path import splitext

_string_types = (str, ) if sys.version_info[0] == 3 else (basestring, )


#
# Errors
#
class ManifestError(Exception):
    pass


class InvalidManifestError(ManifestError):
    pass


class UnfinishedManifestError(ManifestError):
    pass


class UnsupportedManifestError(ManifestError):
    pass


class UnsupportedExtensionError(ManifestError):
    pass


#
# Manifest
#
class Manifest(object):
    """Assets manifest."""

    def __init__(self):
        self._entries = {}

    def add(self, entry):
        """Add an entry to the manifest."""
        if entry.name in self._entries:
            raise KeyError('Entry {} already present'.format(entry.name))
        self._entries[entry.name] = entry

    def __getitem__(self, key):
        """Get a manifest entry."""
        return self._entries[key]

    def __getattr__(self, name):
        """Get a manifest entry."""
        try:
            return self._entries[name]
        except KeyError:
            raise AttributeError('Attribute {} does not exists.'.format(name))


class ManifestEntry(object):
    """Represents a manifest entry."""
    templates = {
        '.js': '<script src="{}"></script>',
        '.css': '<link rel="stylesheet" href="{}"></link>',
    }

    def __init__(self, name, paths):
        self.name = name
        self._paths = paths

    def render(self):
        """Render entry."""
        out = []
        for p in self._paths:
            _dummy_name, ext = splitext(p)
            tpl = self.templates.get(ext.lower())
            if tpl is None:
                raise UnsupportedExtensionError(p)
            out.append(tpl.format(p))
        return ''.join(out)

    def __str__(self):
        return self.render()


#
# Factories
#
class ManifestFactory(object):
    """Manifest factory base class."""
    @classmethod
    def load(cls, filepath):
        with open(filepath) as fp:
            return cls.create(json.load(fp))

    @classmethod
    def create_entry(cls, entry, paths):
        """Create a manifest entry instance."""
        return ManifestEntry(entry, paths)

    @classmethod
    def create_manifest(cls):
        """Create a manifest instance."""
        return Manifest()


class WebpackManifestFactory(ManifestFactory):
    """Manifest factory for webpack-manifest-plugin."""

    @classmethod
    def create(cls, data):
        manifest = cls.create_manifest()
        for entry_name, path in data.items():
            if not isinstance(path, _string_types):
                raise InvalidManifestError('webpack-manifest-plugin')
            manifest.add(cls.create_entry(entry_name, [path]))
        return manifest


class WebpackYamFactory(ManifestFactory):
    """Manifest factory for webpack-yam-plugin."""

    @classmethod
    def create(cls, data):
        # Is manifest of correct type?
        try:
            status = data['status']
            files = data['files']
        except KeyError:
            raise InvalidManifestError('webpack-yam-plugin')

        # Is manifest finished?
        if files is None or status != 'built':
            raise UnfinishedManifestError(data)

        manifest = cls.create_manifest()
        for entry_name, paths in files.items():
            manifest.add(cls.create_entry(entry_name, paths))
        return manifest


class WebpackBundleTrackerFactory(ManifestFactory):
    """Manifest factory for webpack-bundle-tracker."""

    @classmethod
    def create(cls, data):
        # Is manifest of correct type?
        try:
            status = data['status']
        except KeyError:
            raise InvalidManifestError('webpack-bundle-tracker')

        if 'chunks' not in data:
            raise InvalidManifestError('webpack-bundle-tracker')

        # Is manifest finished?
        if status != 'done':
            raise UnfinishedManifestError(data)

        manifest = cls.create_manifest()
        for entry_name, paths in data['chunks'].items():
            manifest.add(
                cls.create_entry(entry_name, [x['publicPath'] for x in paths]))
        return manifest


class ManifestLoader(object):
    """Loads a Webpack manifest (multiple types supported)."""
    types = [
        WebpackBundleTrackerFactory,
        WebpackYamFactory,
        WebpackManifestFactory,
    ]

    @classmethod
    def load(cls, filepath):
        """Load a manifest from a file."""
        with open(filepath) as fp:
            data = json.load(fp)

        for t in cls.types:
            try:
                return t.create(data)
            except InvalidManifestError:
                pass

        raise UnsupportedManifestError(filepath)
