#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python client for Hiera hierachical database."""

from __future__ import print_function, unicode_literals

import logging
import os.path
import subprocess

import hiera.exc

__all__ = ('HieraClient',)


class HieraClient(object):
    __doc__ = __doc__

    def __init__(self, config_filename, hiera_binary='hiera', hiera_vars = {}):
        """Create a new instance with the given settings.

        hiera_vars is passed in as a dict.  This dict will translate key=value and be appended
        onto the class definition would be:
          obj = hiera.HieraClient(config_filename='hiera.yaml', hiera_binary='hiera',
                hiera_vars={'environment': 'developer', 'osfamily': 'Debian', '::facter_key': 'helloworld'}
          obj.get('some_key')

        and the hiera command line would result ini:
          [hiera_binary] --config [config_filename] [key] [hiera_vars.key]=[hiera_vars.value]
          hiera --config hiera.yaml some_key environment='developer' osfamily='Debian' ::facter_key='helloworld'

        :param config_filename: Path to the hiera configuration file.
        :param hiera_binary: Path to the hiera binary. Defaults to 'hiera'.
        :param hiera_vars: Custom Key Values to pass to the hiera command.  This is to get around python not accepting colons in the keys. Format: hiera_vars = {'::custom_fact': 'value'}
        """
        self.config_filename = config_filename
        self.hiera_binary = hiera_binary
        self.hiera_vars = hiera_vars

        self._validate()
        logging.debug('New Hiera instance: {0}'.format(self))

    def __repr__(self):
        """String representations of Hiera instance."""
        def kv_str(key):
            """Takes an instance attribute and returns a string like:
            'key=value'
            """
            return '='.join((key, repr(getattr(self, key, None))))

        params_list = map(kv_str,
                          ['config_filename', 'hiera_binary', 'hiera_vars'])
        params_string = ', '.join(params_list)
        return '{0}({1})'.format(self.__class__.__name__, params_string)

    def get(self, key_name):
        """Request the given key from hiera.

        Returns the string version of the key when successful.

        Raises :class:`hiera.exc.HieraError` if the key does not exist or there
        was an error invoking hiera. Raises
        :class:`hiera.exc.HieraNotFoundError` if the hiera CLI binary could not
        be found.

        :param key_name: string key
        :rtype: str value for key or None
        """
        return self._hiera(key_name)

    def _command(self, key_name):
        """Returns a hiera command list that is suitable for passing to
        subprocess calls.

        :param key_name:
        :rtype: list that is hiera command
        """
        cmd = [self.hiera_binary,
               '--config', self.config_filename,
               key_name]

        if self.hiera_vars:
            for key, value in self.hiera_vars.iteritems():
                cmd.append("%s=%s" % (key, value))

        return cmd

    def _hiera(self, key_name):
        """Invokes hiera in a subprocess with the instance environment to query
        for the given key.

        Returns the string version of the key when successful.

        Raises HieraError if the key does not exist or there was an error
        invoking hiera. Raises HieraNotFoundError if the hiera CLI binary could
        not be found.

        :param key_name: string key
        :rtype: str value for key or None
        """
        hiera_command = self._command(key_name)
        output = None
        try:
            output = subprocess.check_output(
                hiera_command, stderr=subprocess.STDOUT)
        except OSError as ex:
            raise hiera.exc.HieraNotFoundError(
                'Could not find hiera binary at: {0}'.format(
                    self.hiera_binary))
        except subprocess.CalledProcessError as ex:
            raise hiera.exc.HieraError(
                'Failed to retrieve key {0}. exit code: {1} '
                'message: {2} console output: {3}'.format(
                    key_name, ex.returncode, ex.message, ex.output))
        else:
            value = output.strip()
            if not value:
                return None
            else:
                return value

    def _validate(self):
        """Validate the instance attributes. Raises HieraError if issues are
        found.
        """
        if not os.path.isfile(self.config_filename):
            raise hiera.exc.HieraError(
                'Hiera configuration file does not exist '
                'at: {0}'.format(self.config_filename))
