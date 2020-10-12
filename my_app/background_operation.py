from time import sleep
from typing import Callable, Dict, Union


class BackgroundOperation:

    def __init__(self):
        self._cancel_me = True  # need to make sure to call 'get_ready_to_go' prior to running
        self.callback_iteration_complete: Union[None, Callable[[str, str, float], None]] = None
        self.callback_finished: Union[None, Callable[[Dict], None]] = None
        self.callback_cancelled: Union[None, Callable[[], None]] = None

    def please_stop(self):
        self._cancel_me = True

    def get_ready_to_go(self, f_iteration_complete = None, f_finished = None, f_cancelled = None):
        self._cancel_me = False
        self.callback_iteration_complete = f_iteration_complete
        self.callback_finished = f_finished
        self.callback_cancelled = f_cancelled

    def run(self, number_iterations: int):
        for i in range(1, number_iterations + 1):

            # background thread code should check for cancellation as often as possible
            if self._cancel_me:
                if self.callback_cancelled:
                    self.callback_cancelled()
                else:
                    print("Background thread cancelled")
                return

            # run one single iteration
            sleep(1)

            # then broadcast the message to any listeners
            if self.callback_iteration_complete:
                self.callback_iteration_complete(
                    f"{i}/{number_iterations} of the way there",
                    f"Iteration {i} Completed Successfully",
                    100.0 * float(i) / float(number_iterations)
                )
            else:
                print(f"Iteration ({i}/{number_iterations}) completed")

        # once totally complete just broadcast the completion
        if self.callback_finished:
            self.callback_finished({'result_string': 'PRETEND I AM RESULTS'})
        else:
            print("Finished!")
