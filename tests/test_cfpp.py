# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import json
import os
import subprocess
import unittest
from glob import glob

from cfpp.__main__ import camel_to_snake


class TestCfpp(unittest.TestCase):

    def test_files(self):
        self.maxDiff = None
        test_inputs = glob("tests/0*.template")
        for one_input in test_inputs:
            output = subprocess.check_output(
                ["cfpp", "-s", "tests", one_input])
            with open(one_input.replace(".template", ".output.json"), "r") as fp:
                expected = fp.read()
            self.assertMultiLineEqual(expected, output)
            print("%s passed." % one_input)

    def test_kms(self):
        if "CFPP_RUN_KMS_TESTS" not in os.environ:
            return

        import boto3
        import botocore

        output = subprocess.check_output(["cfpp", "-s", "tests",
                                          "tests/kms_test.template"])
        parsed = json.loads(output)["Parameters"]
        without_context = parsed["EncryptedValue"]["Default"]
        with_context = parsed["EncryptedValueWithContext"]["Default"]

        kms = boto3.client('kms')
        kms.decrypt(CiphertextBlob=base64.b64decode(without_context))
        try:
            kms.decrypt(CiphertextBlob=with_context)
            self.fail("expected KMS to fail due to lack of context")
        except botocore.exceptions.ClientError:
            pass

        kms.decrypt(CiphertextBlob=base64.b64decode(with_context),
                    EncryptionContext={"ContextKey": "ContextValue"})

    def test_camel_to_snake(self):
        self.assertEquals("kms::encrypt_file",
                          camel_to_snake("KMS::EncryptFile"))
        self.assertEquals("mime_multipart", camel_to_snake("MimeMultipart"))
        self.assertEquals("trim", camel_to_snake("Trim"))


if __name__ == '__main__':
    unittest.main()
