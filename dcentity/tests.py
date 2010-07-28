import doctest
import unittest

from tools import utils, wpapi

# Old stale tests that used to be here were moved to `oldtests.py`.


# NOTE:  Because the default test suite is overridden here, additional tests
# added to this file need to be explicitly referenced with a "suite.addTest"
# call.  e.g., for this test:
#
#  class FooTestCase(unittest.TestCase):
#      def testFoo(self):
#          self.assertEquals('foo', 'bar')
#
# add this to the suite definition:
#
#      suite.addTest(unittest.TestLoader().loadTestsFromTestCase(FooTestCase))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(utils))
    suite.addTest(doctest.DocTestSuite(wpapi))
    #suite.addTest(doctest.DocTestSuite(models))
    return suite
