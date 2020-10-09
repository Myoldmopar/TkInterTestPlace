from unittest import TestCase

from my_app.operator import BackgroundOperation


class TestOperator(TestCase):

    def test_run(self):
        b = BackgroundOperation()
        b.get_ready_to_go()
        self.assertFalse(b._cancel_me)
        b.run(1)
