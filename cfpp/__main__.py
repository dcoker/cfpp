# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import json
import sys

from . import extrinsics
from ._version import VERSION

RC_OK = 0
RC_NOPE = 1


def main(args=None):
    args = parse_args(args)

    try:
        with open(args.filename, "r") as fp:
            parsed = json.loads(fp.read())
            parsed = extrinsics.walk(parsed, search_path=args.search_path)
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


if __name__ == '__main__':
    status = main()
    sys.exit(status)
