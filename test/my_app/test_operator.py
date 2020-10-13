from unittest import TestCase

from my_app.background_operation import BackgroundOperation


class TestOperator(TestCase):

    def test_run(self):
        b = BackgroundOperation(1, [])
        b.get_ready_to_go()
        self.assertFalse(b._cancel_me)
        b.run()
