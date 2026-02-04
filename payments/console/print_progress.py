"""
    Functions for printing a provider operation progress
"""
import os
from functools import partial

print_progress = partial(print, end='\n...' if "GITHUB_ACTIONS" in os.environ else '', flush=True)

print_done = partial(print, flush=True)


def print_stage(msg: str, stage_id: int, number_of_stages: int) -> None:
    """
    Prints a stage progress
    :param msg: stage name
    :param stage_id: stage id
    :param number_of_stages: total number of stages
    """
    # Or, if GHA starts to have problems with live output:
    # message = f'...{msg} {stage_id + 1} of {number_of_stages}...'
    # ...
    # print_done("")
    # print_progress(message)
    message = f'\n...{msg} {stage_id + 1} of {number_of_stages}...'
    if stage_id + 1 == number_of_stages:
        message = f'{message}\n...'
    print_progress(message)
