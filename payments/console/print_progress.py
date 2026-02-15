"""
    Functions for printing a provider operation progress
"""
import os

_IS_CI = 'GITHUB_ACTIONS' in os.environ
PREFIX = ''


def print_done(*values: object) -> None:
    """
    Prints message indicating that provider processing has completed
    :param values: objects to print
    """
    global PREFIX
    if PREFIX:
        try:
            first_string = next(item for item in values if isinstance(item, str))
            values_list = list(values)
            values_list[values_list.index(first_string)] = PREFIX + first_string
            PREFIX = ''
            print(*values_list, flush=True)
            return
        except StopIteration:
            pass
    print(*values, flush=True)


def print_progress(*values: object) -> None:
    """
    Prints progress message
    :param values: objects to print
    """
    try:
        last_string = next(item for item in reversed(values) if isinstance(item, str))
    except StopIteration:
        last_string = None
    end = ''
    if _IS_CI:
        end = '\n'
        if last_string and not last_string.endswith('...'):
            end = '\n...'
    print(*values, end=end, flush=True)


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
    global PREFIX
    if not _IS_CI:
        message = '\n'
    else:
        message = ''
    message += f'...{msg} {stage_id + 1} of {number_of_stages}...'
    if stage_id + 1 == number_of_stages:
        if not _IS_CI:
            message += '\n...'
        else:
            PREFIX = '...'
    print_progress(message)
