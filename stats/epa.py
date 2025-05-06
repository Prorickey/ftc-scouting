#!/usr/bin/env python3
import database
from database import MatchKey
import numpy as np
from helper import *
import copy
# https://www.statbotics.io/blog/epa

__epa_dict = {}
__teams = {}
__scores = {}

__stddev = 0

# https://www.statbotics.io/blog/epa

def init():
    global __teams, __scores, __epa_dict
    database.init()
    __teams = database.get_match_teams() # should be sorted by time, not filtered by event code
    __scores = database.get_match_scores()

    start_of_january = 1735707600
    end_of_january = 1738299600
    
    january_matches = list(filter(lambda key: start_of_january <= key.start_time <= end_of_january, __teams.keys()))

    # FRC: stddev of Week 1, so FTC is maybe stddev of January? idk
    january_scores = [__scores[key]["totalPoints"] for key in january_matches]

    average_january_score = np.average(january_scores)

    # Set initial EPA to average "Week 1" score / 3
    print("hi")
    __epa_dict = {team: average_january_score / 3 for team in flatten(map(lambda d: list(d.keys()), __teams.values()))}
    print("bye")

    __stddev = np.std(january_scores)

# This is just point unit Elo for now
def calc_epa(match_key: MatchKey):
    global __epa_dict

    red_match_key = copy.deepcopy(match_key)
    red_match_key.alliance = "Red"
    blue_match_key = copy.deepcopy(match_key)
    blue_match_key.alliance = "Blue"

    red_teams = list(filter(lambda t: __teams[red_match_key][t][1], __teams[red_match_key].keys()))
    blue_teams = list(filter(lambda t: __teams[blue_match_key][t][1], __teams[blue_match_key].keys()))

    print(red_teams, blue_teams)

    predicted_score_margin = sum(map(lambda team: __epa_dict[team], red_teams)) - sum(map(lambda team: __epa_dict[team], blue_teams))
    actual_score_margin = __scores[red_match_key]["totalPoints"] - __scores[blue_match_key]["totalPoints"]
    delta_epa = 72/250 * (actual_score_margin - predicted_score_margin) # if red does better, this is positive, so we need to invert for blue?

    print(f"delta: {delta_epa}")

    for team in red_teams:
        __epa_dict[team] += delta_epa

    for team in blue_teams:
        __epa_dict[team] -= delta_epa

def season_epa():
    global __teams
    sorted_match_keys = sorted(filter(lambda k: k.alliance == "Red", __teams.keys()), key=lambda k: k.start_time)
    # print(sorted_match_keys[:5])
    for match_key in sorted_match_keys:
        print(match_key)
        calc_epa(match_key)
        print(__epa_dict[11260])
