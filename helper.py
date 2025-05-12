#!/usr/bin/env python3
"""
Some useful functions not part of the standard library (mostly cool functional constructs to cope with Python).
"""
from typing import Callable, Any
from functools import reduce

# Inspired by https://www.idris-lang.org/docs/idris2/0.6.0/contrib_docs/docs/Data.SortedMap.html#Data.SortedMap.mergeWith
def merge_with(fn: Callable[[Any, Any], Any], left_dict: dict, right_dict: dict) -> dict:
    """
    Merge two dictionaries. If duplicate keys exist, combine them using `fn`.
    
    Args:
        fn: if a duplicate key exists across both dictionaries, the new value will be fn(left_dict[key], right_dict[key])
        left_dict: the left dictionary to be merged
        right_dict: the right dictionary to be merged
    
    Returns the merged dictionary.
    """
    fn_ = lambda a,b: b if a == None else (a if b == None else fn(a,b))
    if len(right_dict.keys()) == 1:
        # speed optimization if the right dict only has one item
        k = list(right_dict.keys())[0]
        left_dict[k] = fn_(left_dict.get(k), right_dict.get(k))
        return left_dict
    return {k: fn_(left_dict.get(k), right_dict.get(k)) for k in left_dict.keys() | right_dict.keys()}

def merge_left(left_dict: dict, right_dict: dict) -> dict:
    """
    Merge two dictionaries (left-biased). If duplicate keys exist, take the value from the left dictionary.

    Args:
        left_dict: the left dictionary to be merged
        right_dict: the right dictionary to be merged
    
    Returns the merged dictionary.
    """
    return merge_with(lambda l, r: l, left_dict, right_dict)

def flatten(lists: list[list]) -> list:
    """
    Flatten a list of lists to a single list.

    Args:
        lists: the list of lists

    Returns the flattened list.
    """
    return reduce(lambda a, b: a+b, lists, [])