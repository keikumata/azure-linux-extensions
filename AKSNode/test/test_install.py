#!/usr/bin/env python
import sys
sys.path.insert(0,'..')

import unittest
import os
import zipfile
import codecs
import shutil

from MockUtil import MockUtil
from Utils.WAAgentUtil import waagent
import entrypoint as ep

class TestInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_install(self):
        hutil = MockUtil(self)
        ep.RunGetOutput = waagent.RunGetOutput
        ep.install(hutil)

if __name__ == '__main__':
    unittest.main()
