# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import collections
import json
import sys

import re
from . import extrinsics
from ._version import VERSION

FUNC_PREFIX = "CFPP::"

RC_OK = 0
RC_NOPE = 1


def main(args=None):
    args = parse_args(args)

    try:
        with open(args.filename, "r") as fp:
            parsed = json.loads(fp.read())
            parsed = walk(parsed, args, ['$'])
            print(json.dumps(parsed, indent=2, sort_keys=True))
    except extrinsics.ContextException as e:
        print(e.message, file=sys.stderr)
        return RC_NOPE


def parse_args(args):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog='cfpp',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filename', metavar='filename')
    parser.add_argument('-s', '--search-path',
                        action='append',
                        default=['.'],
                        help='List of paths to search when reading files '
                             'referenced from the CloudFormation template. '
                             'The current working directory is always '
                             'searched first, regardless of this '
                             'setting. Specify this option once for each '
                             'directory to add to the search path.')
    parser.add_argument('--version',
                        action='version',
                        version=VERSION,
                        help='Display version number and exit.')
    args = parser.parse_args(args)
    return args


def walk(node, config, path):
    if isinstance(node, list):
        return [apply_extrinsics(walk(value, config, path + [i]), config, path + [i])
                for i, value in enumerate(node)]

    if isinstance(node, collections.Mapping):
        return {key: apply_extrinsics(walk(value, config, path + [key]), config, path + [key])
                for key, value in node.iteritems()}

    if isinstance(node, int):
        return node

    if isinstance(node, unicode):
        return node

    raise extrinsics.UnexpectedNodeType(path, node)


def is_extrinsic_dict(value):
    return isinstance(value, collections.Mapping) \
           and len(value) == 1 \
           and value.keys()[0].startswith(FUNC_PREFIX)


def apply_extrinsics(value, config, context):
    if not is_extrinsic_dict(value):
        return value
    func_name = camel_to_snake(value.keys()[0][len(FUNC_PREFIX):])
    method = extrinsics.get_func_or_raise(context, func_name)
    result = method(config, context, value.values()[0])
    return result


def camel_to_snake(name):
    # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    underscores = re.sub('([^:])([A-Z][a-z]+)', r'\1_\2', name)
    first_word = re.sub('([a-z0-9])([A-Z])', r'\1_\2', underscores)
    lower_case = first_word.lower()
    return lower_case


if __name__ == '__main__':
    status = main()
    sys.exit(status)
