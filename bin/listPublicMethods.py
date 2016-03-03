#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
# this script is meant to be ran inside of zendmd
# e.g. zendmd --script /path/to/script/listPublicMethods.py

from collections import defaultdict
import cStringIO
import inspect

try:
    import yaml
except ImportError:
    pass


def classes_to_check(dmd_item):
    to_check = set()

    to_check.add(dmd_item.__class__)
    if hasattr(dmd_item, 'getPythonDeviceClass'):
        to_check.add(
            getattr(dmd_item, 'getPythonDeviceClass')()
        )

    nodes_to_check = filter(lambda node: 'getChildNodes' in dir(node), dmd_item.getChildNodes())
    for node in nodes_to_check:
        to_check.update(classes_to_check(node))

    return to_check


def implicitly_public(klass, methods):

    def implicit_filter(method_name):
        valid = True

        # Covers cases from documentation for method not being public
        if any((method_name == 'manage',
                method_name.startswith(('_', 'manage_')),
                hasattr(klass, method_name + '__roles__'),
                not inspect.getdoc(getattr(klass, method_name)),
                )):
            valid = False

        return valid

    return filter(implicit_filter, methods)


def explicitly_public(klass, methods):

    def explicit_filter(method_name):
        valid = False
        roles = getattr(klass, method_name + '__roles__', False)
        if roles is None:
            valid = True
        return valid

    return filter(explicit_filter, methods)


def get_data(dmd=None):
    data = defaultdict(dict)

    for klass in classes_to_check(dmd):
        methods = tuple(
            attr for attr in klass.__dict__ if inspect.ismethod(getattr(klass, attr))
        )
        data[klass] = {
            'public': explicitly_public(klass, methods),
            'unprotected': implicitly_public(klass, methods),
        }

    return data


def print_data(tree, indent_lvl=0):
    if yaml:
        print yaml.safe_dump(tree, default_flow_style=False)
    else:
        INDENT = ' ' * 2
        for key, value in tree.iteritems():
            print INDENT * indent_lvl + key
            if isinstance(value, dict):
                print_data(value, indent_lvl+1)
            else:
                value_indent = INDENT * (indent_lvl+1)
                print value_indent + ('\n' + value_indent).join(value)


def get_report(data):
    INDENT = '  '
    METHOD_PREFIX = '\n{indent}{indent} - '.format(indent=INDENT)
    report = cStringIO.StringIO()

    for klass in sorted(data.iterkeys()):
        fullname = '{}.{}'.format(klass.__module__, klass.__name__)
        try:
            header = '{}\n\t(from file: {})'.format(fullname, inspect.getabsfile(klass))
        except TypeError:
            header = fullname

        footer = '\n'

        unprotected_methods = METHOD_PREFIX.join(sorted(data[klass]['unprotected']))
        if unprotected_methods:
            unprotected = '{indent}Implicitly public methods:{prefix}{unprotected}\n'
        else:
            unprotected = '{indent}No implicitly public methods.'

        public_methods = METHOD_PREFIX.join(sorted(data[klass]['public']))
        if public_methods:
            public = '{indent}Methods declared as public:{prefix}{public}\n'
        else:
            public = '{indent}No methods declared as public.'

        args = {
            'indent': INDENT,
            'unprotected': unprotected_methods,
            'public': public_methods,
            'prefix': METHOD_PREFIX,
        }

        report.write(header)
        report.write('\n')
        report.write(unprotected.format(**args))
        report.write('\n')
        report.write(public.format(**args))
        report.write('\n')
        report.write(footer)
        report.write('\n')

    return report.getvalue()


if __name__ == '__main__':
    data = get_data(dmd)
    print(get_report(data))
