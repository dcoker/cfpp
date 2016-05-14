# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import hashlib
import json
import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
import os


def get_func_or_raise(context, func_name):
    """get_func_or_raise returns the unbound function, or raises an exception
    if the method does not exist or is not allowed to be called."""
    func_name_mangled = func_name.replace("::", "__")
    func = globals().get(func_name_mangled, None)
    if func is None or not getattr(func, '_extrinsic', False):
        raise NoSuchMethodException(context, func_name)
    return func


def extrinsic(func):
    """@extrinsic marks methods as invokable from templates."""
    func._extrinsic = True
    return func


def openfile(config, context, filename):
    paths = config.search_path[:]
    while len(paths):
        full_path = os.path.join(paths.pop(0), filename)
        if os.path.exists(full_path):
            return open(full_path, "r")
    raise FileNotFoundException(context, filename)


@extrinsic
def command(_, context, arg):
    """command executes a command and returns its output (both stdout and
    stderr) as a string."""
    _raise_unless_array_of_strings(context, arg)
    # subprocess returns byte strings, but we want to use uniform string
    # types throughout.
    return unicode(subprocess.check_output(arg))


@extrinsic
def string_split(_, context, arg):
    """string_split returns a list of the words in a string split by a
    separator.

    Example:
        {"CFPP::StringSplit": ["\n", "time\nafter\ntime"]}
    """
    _raise_unless_array_of_strings(context, arg)
    return arg[1].split(arg[0])


@extrinsic
def file_to_string_raw(config, context, arg):
    """file_to_string_raw reads the contents of a file to a string."""
    _raise_unless_filename(context, arg)
    with openfile(config, context, arg) as fp:
        return fp.read()


@extrinsic
def file_to_string(config, context, arg):
    """file_to_string reads the contents of a file to a string, with leading and trailing whitespace removed."""
    return file_to_string_raw(config, context, arg).strip()


@extrinsic
def json_file_to_string(config, context, arg):
    """json_file_to_string parses a JSON file and re-serializes it to a JSON string."""
    _raise_unless_filename(context, arg)
    with openfile(config, context, arg) as fp:
        return json.dumps(json.loads(fp.read()), sort_keys=True)


@extrinsic
def json_file(config, context, arg):
    """json_file reads the contents of a file as JSON.

    Example:
        "WebserverInstanceType": {
            "Type": "String",
            "AllowedValues": {
                "CFPP::JsonFile": "sample_sriov_instance_types.json"
            },
            "Default": "m4.large"
        }
    """
    _raise_unless_filename(context, arg)
    with openfile(config, context, arg) as fp:
        return json.loads(fp.read())


@extrinsic
def trim(_, context, arg):
    """trim strips whitespace from the beginning and end of a string."""
    _raise_unless_string(context, arg)
    return arg.strip()


@extrinsic
def mime_multipart(_, context, arg):
    """mime_multipart composes a MIME multipart string.

    Example:
        "UserData": {
          "Fn::Base64": {
            "CFPP::MimeMultipart": [
              ["text/x-shellscript", {"CFPP::FileToString": "userdata.sh"}],
              ["text/cloud-config", {"CFPP::FileToString": "cloud-init.yaml"}]
            ]
          }
        }
    """
    _raise_unless_mime_params(context, arg)
    mime_doc = MIMEMultipart()
    # set boundary explicitly so that they are stable based on path in the template.
    mime_doc.set_boundary("=" * 10 + hashlib.sha1(".".join(context)).hexdigest() + "=" * 3)
    for mime_type, contents in arg:
        sub_message = MIMEText(contents, contents, sys.getdefaultencoding())
        mime_doc.attach(sub_message)
    return mime_doc.as_string()


@extrinsic
def kms__encrypt_file(config, context, args):
    _raise_unless_kms_encrypt_args(context, args)
    key_id = args[0]
    plaintext_filename = args[1]
    encryption_context = {}
    if len(args) == 3:
        encryption_context = args[2]
    kms = boto3.client('kms')
    with openfile(config, context, plaintext_filename) as fp:
        ciphertext = kms.encrypt(EncryptionContext=encryption_context,
                                 KeyId=key_id,
                                 Plaintext=fp.read())
    return base64.b64encode(ciphertext["CiphertextBlob"])


class ContextException(Exception):
    def __init__(self, context, message):
        message = "%s: %s" % (".".join(context), message)
        super(ContextException, self).__init__(message)


class UnexpectedArgumentTypeException(ContextException):
    def __init__(self, context, expected, actual):
        message = "Expected argument of %s but got %s %s" % (expected, type(actual), actual)
        super(UnexpectedArgumentTypeException, self).__init__(context, message)


class UnexpectedNodeType(ContextException):
    def __init__(self, context, node):
        message = "Encountered an unsupported node: %s %s" % (type(node), node)
        super(UnexpectedNodeType, self).__init__(context, message)


class NoSuchMethodException(ContextException):
    def __init__(self, context, func_name):
        message = "Unrecognized function: %s." % (func_name,)
        super(NoSuchMethodException, self).__init__(context, message)


class InsufficientArgsException(ContextException):
    def __init__(self, context, expected):
        message = "Expected %d arguments but got %d" % expected
        super(InsufficientArgsException, self).__init__(context, message)


class FileNotFoundException(ContextException):
    def __init__(self, context, filename):
        message = "The file '%s' does not exist." % (filename,)
        super(FileNotFoundException, self).__init__(context, message)


def _raise_unless_array_of_strings(context, arg):
    if not isinstance(arg, list):
        raise UnexpectedArgumentTypeException(context, list, arg)
    for element in arg:
        if not isinstance(element, unicode):
            raise UnexpectedArgumentTypeException(context, unicode, element)


def _raise_unless_kms_encrypt_args(context, arg):
    if not isinstance(arg, list):
        raise UnexpectedArgumentTypeException(context, list, arg)
    if len(arg) < 2:
        raise InsufficientArgsException(context, 2)
    if not isinstance(arg[0], unicode):
        raise UnexpectedArgumentTypeException(context, unicode, arg[0])
    if not isinstance(arg[1], unicode):
        raise UnexpectedArgumentTypeException(context, unicode, arg[1])
    if len(arg) == 3 and not isinstance(arg[2], dict):
        raise UnexpectedArgumentTypeException(context, dict, arg[2])


def _raise_unless_string(context, arg):
    if not isinstance(arg, unicode):
        raise UnexpectedArgumentTypeException(context, unicode, arg)


def _raise_unless_filename(context, arg):
    _raise_unless_string(context, arg)


def _raise_unless_mime_params(context, arg):
    if not isinstance(arg, list):
        raise UnexpectedArgumentTypeException(context, list, arg)
