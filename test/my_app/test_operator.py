from unittest import TestCase

from my_app.operator import BackgroundOperation


class TestOperator(TestCase):

    def test_run(self):
        b = BackgroundOperation()
        self.assertFalse(b.cancel_me)
        b.run(1)
