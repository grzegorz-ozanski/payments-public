"""
    Functions for printing a provider operation progress
"""
from functools import partial

print_progress = partial(print, end='', flush=True)

print_done = partial(print, flush=True)


def print_stage(msg: str, stage_id: int, number_of_stages: int) -> None:
    """
    Prints a stage progress
    :param msg: stage name
    :param stage_id: stage id
    :param number_of_stages: total number of stages
    """
    message = f'\n...{msg} {stage_id + 1} of {number_of_stages}...'
    if stage_id + 1 == number_of_stages:
        message = f'{message}\n...'
    print_progress(message)
