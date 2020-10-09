from time import sleep

from pubsub import pub

from my_app.structs import PubSubMessageTypes


class BackgroundOperation:

    def __init__(self):
        self._cancel_me = True  # need to make sure to call 'get_ready_to_go' prior to running

    def get_ready_to_go(self):
        self._cancel_me = False

    def please_stop(self):
        self._cancel_me = True

    def run(self, number_iterations: int):
        for i in range(1, number_iterations + 1):

            # background thread code should check for cancellation as often as possible
            if self._cancel_me:
                pub.sendMessage(PubSubMessageTypes.CANCELLED)
                return

            # run one single iteration
            # check_call([command, '1'])
            sleep(1)

            # then broadcast the message to any listeners
            pub.sendMessage(
                PubSubMessageTypes.STATUS,
                object_completed=f"Iteration {i} Completed Successfully",
                percent_complete=100.0 * float(i) / float(number_iterations),
                status=f"{i}/{number_iterations} of the way there")

        # once totally complete just broadcast the completion
        pub.sendMessage(PubSubMessageTypes.FINISHED, results={'result_string': 'PRETEND I AM RESULTS'})
