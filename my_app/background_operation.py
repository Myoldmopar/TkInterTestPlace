from time import sleep
from typing import Callable, Dict, List, Union


class BackgroundOperation:

    def __init__(self, idfs_to_run: List[str]):
        self._cancel_me = True  # need to make sure to call 'get_ready_to_go' prior to running
        self.callback_iteration_complete: Union[None, Callable[[str, str, float], None]] = None
        self.callback_finished: Union[None, Callable[[Dict], None]] = None
        self.callback_cancelled: Union[None, Callable[[], None]] = None
        self.idfs_to_run = idfs_to_run

    def please_stop(self):
        self._cancel_me = True

    def get_ready_to_go(self, f_iteration_complete=None, f_finished=None, f_cancelled=None):
        self._cancel_me = False
        self.callback_iteration_complete = f_iteration_complete
        self.callback_finished = f_finished
        self.callback_cancelled = f_cancelled

    def run(self):
        i = 0
        n = len(self.idfs_to_run)
        for idf in self.idfs_to_run:
            i += 1

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
                    f"{i}/{n} of the way there",
                    f"Run {idf} Completed Successfully",
                    100.0 * float(i) / float(n)
                )
            else:
                print(f"Iteration ({i}/{n}) completed")

        # once totally complete just broadcast the completion
        if self.callback_finished:
            self.callback_finished({'result_string': 'PRETEND I AM RESULTS'})
        else:
            print("Finished!")
