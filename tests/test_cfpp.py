# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import json
import subprocess
import unittest
from glob import glob

import os


def json_normalize(s):
    return json.dumps(json.loads(s), indent=2)


class TestCfpp(unittest.TestCase):
    def test_files(self):
        self.maxDiff = None
        test_inputs = glob("tests/0*.template")
        for one_input in test_inputs:
            output = subprocess.check_output(
                ["cfpp", "-s", "tests", one_input])
            with open(one_input.replace(".template", ".output.json"), "r") as fp:
                expected = fp.read()
            self.assertMultiLineEqual(json_normalize(expected), json_normalize(output))
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
        from cfpp.extrinsics import camel_to_snake
        self.assertEquals("kms::encrypt_file",
                          camel_to_snake("KMS::EncryptFile"))
        self.assertEquals("mime_multipart", camel_to_snake("MimeMultipart"))
        self.assertEquals("trim", camel_to_snake("Trim"))

    def test_is_ref(self):
        from cfpp.extrinsics import is_ref
        self.assertTrue(is_ref({"Ref": "R"}))
        self.assertTrue(is_ref({"ref": "R"}))
        self.assertTrue(is_ref({"REF": "R"}))
        self.assertFalse(is_ref(None))
        self.assertFalse(is_ref([]))
        self.assertFalse(is_ref({}))
        self.assertFalse(is_ref({"X": "Y"}))
        self.assertFalse(is_ref({"X": "Y", "Z": "0"}))

    def test_walk_var_substitution(self):
        from cfpp.extrinsics import walk
        self.assertEqual("ex", walk({"Ref": "X"}, {}, "root", {"X": "ex"}))
        self.assertEqual({"O": "ex"}, walk({"O": {"Ref": "X"}}, {}, ["root"], {"X": "ex"}))


if __name__ == '__main__':
    unittest.main()
