from platform import system
from subprocess import check_call

from pubsub import pub

from my_app.structs import PubSubMessageTypes


class BackgroundOperation:

    def __init__(self):
        self.cancel_me = False

    def run(self, number_iterations: int):
        for i in range(1, number_iterations + 1):
            if self.cancel_me:
                pub.sendMessage(PubSubMessageTypes.CANCELLED)
                return
            if system() == 'Windows':
                a_sum = 0
                for k in range(10000):
                    for j in range(2000):
                        a_sum += 1
            else:
                check_call(['sleep', '1'])
            pub.sendMessage(PubSubMessageTypes.STATUS, status=f"{i}/{number_iterations} of the way there")
        pub.sendMessage(PubSubMessageTypes.FINISHED, results='PRETEND I AM RESULTS')
