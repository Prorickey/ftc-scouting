#!/usr/bin/env python3
import database
import numpy as np
from typing import Callable
from functools import reduce
from helper import *

# Let's try calculating OPR
# Need to set up a system of equations
# q1_red1 + q1_red2 = red_score
# q1_blue1 + q1_blue2 = blue_score
# ....
# Then format it into a matrix
# Probably have each column be a team, then augment it with the output score I think?
# e.g. two matches, team1+team2 score 80 vs team3+team4 score 60 | team2+team3 score 120 vs team1+team4 score 10
# team1 team2 team3 team4 score
# 1     1     0     0     80
# 0     0     1     1     60
# 0     1     1     0     120
# 1     0     0     1     10
# this seems right.
# the matrix of ones and zeroes times the vector [team1 team2 team3 team4] = [team1 + team2 ; team3 + team4 ; team2 + team3 ; team1 + team4];

# "just try stuff," as our keynote speaker eloquently stated today
# premature optimization is the root of all evil

def calc_opr_from_function(event_code: str, fn: Callable[[dict[database.MatchKey, dict[str, Any]]], float], season: int = 2024) -> dict:
    """
    Calculates OPR for every team in an event.

    Args:
        event_code: the event code of the event (used to retrieve data from database)
        fn: the function used to calculate the relevant metric, given a dictionary of score stats from the FTC Event API (e.g. autoSampleNet, teleopPoints, etc)
        season: the season the event happened
    
    Returns a dictionary where key = team number and value = calculated metric.
    """

    match_teams = database.get_match_teams(event_code=event_code, season=season)
    match_scores = database.get_match_scores(event_code=event_code, season=season)

    teams_at_event = list(set(flatten(map(lambda match_team: list(match_team.keys()), match_teams.values()))))

    alliance_matrix = np.zeros((len(match_scores), len(teams_at_event)), dtype=np.uint64)
    score_matrix = np.zeros((len(match_scores), 1), dtype=np.float64)

    # alliance_matrix is the design matrix X
    # we'll have a score_matrix Y of relevant stats for every alliance
    # X*beta = Y
    # X_pinv * Y = beta

    for idx, key in enumerate(match_teams.keys()):
        if key not in match_scores:
            # probably didn't pull qual and playoff data from both
            return {}
        # ` and match_teams[key][team][1]` is important, ensures a team actually played in that match
        # Orange Alliance does not have this check and only looks at qual matches (i.e. to have our OPR match theirs, remove the check and continue if key.match_level != "QUALIFICATION")
        # This is better though IMO
        alliance_matrix[idx] = list(map(lambda team: 1 if team in match_teams[key].keys() and match_teams[key][team][1] else 0, teams_at_event))
        score_matrix[idx] = fn(match_scores[key])

    opr = np.linalg.pinv(alliance_matrix)@score_matrix

    return {teams_at_event[t[0]]: float(t[1][0]) for t in enumerate(opr)}

def calc_single_stat_opr(event_code: str, statistic: str, season: int = 2024) -> dict:
    """
    Calculates OPR for every team in an event.

    Args:
        event_code: the event code of the event (used to retrieve data from database)
        statistic: the specific score statistic to use from the FTC Event API (e.g. autoSampleNet, teleopPoints, etc)
        season: the season the event happened
    
    Returns a dictionary where key = team number and value = calculated metric.
    """
    return calc_opr_from_function(event_code, lambda d: d[statistic], season)