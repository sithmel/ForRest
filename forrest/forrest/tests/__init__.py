from tests import *
import unittest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWsgiApp))
    suite.addTest(unittest.makeSuite(TestRamDict))
    suite.addTest(unittest.makeSuite(TestFileDict))
    suite.addTest(unittest.makeSuite(TestFs))
    suite.addTest(unittest.makeSuite(TestAuth))
    suite.addTest(unittest.makeSuite(TestAuth2))

    return suite
