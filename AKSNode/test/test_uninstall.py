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

class TestUninstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_uninstall(self):
        hutil = MockUtil(self)
        waagent.LoggerInit('/var/log/waagent.log','/dev/stdout')
        waagent.Log("{0} started to handle.".format("TestExtension"))
        ep.RunGetOutput = waagent.RunGetOutput
        ep.uninstall(hutil)

if __name__ == '__main__':
    unittest.main()
