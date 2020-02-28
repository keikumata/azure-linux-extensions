#!/usr/bin/env python
import unittest
import os
import zipfile
import codecs
import shutil

from MockUtil import MockUtil
import entrypoint as ep

class TestInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_install(self):
        hutil = MockUtil(self)
        ep.install(hutil)

if __name__ == '__main__':
    unittest.main()
