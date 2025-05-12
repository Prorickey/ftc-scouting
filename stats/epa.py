#!/usr/bin/env python3
import database
from database import MatchKey
import numpy as np
from helper import *
import copy
from collections import defaultdict

__epa_dict = {}
__teams = {}
__scores = {}

# https://www.statbotics.io/blog/epa

def init():
    """
    Performs initialization (loads matches from database, initializes all EPAs to default values).

    Must be called before doing any EPA calculations.
    """
    global __teams, __scores, __epa_dict
    database.init()
    __teams = database.get_match_teams() # should be sorted by time, not filtered by event code
    __scores = database.get_match_scores()

    start_of_january = 1735707600
    end_of_january = 1738299600
    
    january_matches = list(filter(lambda key: start_of_january <= key.start_time <= end_of_january, __teams.keys()))

    # FRC: stddev of Week 1, so FTC is maybe stddev of January? idk
    january_scores = [__scores[key]["totalPoints"] for key in january_matches]

    average_january_score = float(np.average(january_scores))

    # Set initial EPA to average "Week 1" score / 3
    __epa_dict = defaultdict(lambda: average_january_score / 3)

__historical_epas = defaultdict(lambda: [])

# This is just point unit Elo for now
def calc_epa(match_key: MatchKey):
    """
    Calculates the EPA updates from a single match.

    Args:
        match_key: the key of the relevant match
    
    Returns nothing.
    """
    global __epa_dict

    red_match_key = copy.deepcopy(match_key)
    red_match_key.alliance = "Red"
    blue_match_key = copy.deepcopy(match_key)
    blue_match_key.alliance = "Blue"

    red_teams = list(filter(lambda t: __teams[red_match_key][t][1], __teams[red_match_key].keys()))
    blue_teams = list(filter(lambda t: __teams[blue_match_key][t][1], __teams[blue_match_key].keys()))

    predicted_score_margin = sum(map(lambda team: __epa_dict[team], red_teams)) - sum(map(lambda team: __epa_dict[team], blue_teams))
    actual_score_margin = __scores[red_match_key]["totalPoints"] - __scores[blue_match_key]["totalPoints"]
    delta_epa = 36/250 * (actual_score_margin - predicted_score_margin) # if red does better, this is positive, so we need to invert for blue

    for team in red_teams:
        __epa_dict[team] += delta_epa
        __historical_epas[team].append((match_key, __epa_dict[team]))

    for team in blue_teams:
        __epa_dict[team] -= delta_epa
        __historical_epas[team].append((match_key, __epa_dict[team]))

def season_epa():
    """
    Calculates the EPA by analyzing every match stored in the database.
    """
    global __teams
    sorted_match_keys = sorted(filter(lambda k: k.alliance == "Red", __teams.keys()), key=lambda k: k.start_time)
    for match_key in sorted_match_keys:
        calc_epa(match_key)

def get_epa(team: int, time: float = None):
    """
    Gets the EPA of a team.

    Args:
        team: the team whose EPA should be retrieved
        time (optional): if set, will retrieve the team's latest EPA as of that time. if unset, will get the team's latest EPA.
    
    Returns a float storing the EPA of the team.
    """
    if time == None:
        return __epa_dict[team]
    else:
        latest_epa = 0
        for (match_key, epa) in __historical_epas[team]:
            if match_key.start_time > time:
                break
            else:
                latest_epa = epa
        return latest_epa

def get_all_epas(team: int):
    """
    Gets all historical EPAs for a team.

    Args:
        team: the team whose EPA should be retrieved
    
    Returns a dict where the key is the time and the value is the EPA at that time.
    """
    return {k.start_time: epa for (k, epa) in __historical_epas[team]}

def get_ranks():
    """
    Returns a dictionary where the key is the team and the value is a tuple of (their EPA rank, their EPA).
    """
    return {team: (idx + 1, __epa_dict[team]) for (idx, team) in enumerate(list(map(lambda t: t[0], sorted(__epa_dict.items(), key=lambda t: t[1], reverse=True))))}