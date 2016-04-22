# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import subprocess
import unittest
from glob import glob


class TestCfpp(unittest.TestCase):
    def test_files(self):
        self.maxDiff = None
        test_inputs = glob("tests/*.template")
        for one_input in test_inputs:
            output = subprocess.check_output(["cfpp", "-s", "tests", one_input])
            with open(one_input.replace(".template", ".output.json"), "r") as fp:
                expected = fp.read()
            self.assertMultiLineEqual(expected, output)
            print("%s passed." % one_input)
