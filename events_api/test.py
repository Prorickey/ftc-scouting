#!/usr/bin/env python3
#%%
import requests
import pickle
from requests.auth import HTTPBasicAuth

# USERNAME = "get your own username"
# TOKEN = "get your own token"

# basic = HTTPBasicAuth(username=USERNAME, password=TOKEN)

# test_score_data = requests.get("https://ftc-api.firstinspires.org/v2.0/2024/scores/FTCCMP1OCHO/qual", auth=basic)
# test_match_data = requests.get("https://ftc-api.firstinspires.org/v2.0/2024/matches/FTCCMP1OCHO", auth=basic)

# with open("test_match_data.pkl", "wb") as f:
#     pickle.dump(test_match_data, f)

# don't spam their API for testing stuff
#%%

with open("test_match_data.pkl", "rb") as f:
    test_match_data: requests.Response = pickle.load(f)

with open("test_score_data.pkl", "rb") as f:
    test_score_data: requests.Response = pickle.load(f)

test_match_data = test_match_data.json()
test_score_data = test_score_data.json()

# %%
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

stat = lambda allianceScore: allianceScore['teleopSampleNet'] + allianceScore['teleopSampleLow'] + allianceScore['teleopSampleHigh'] + allianceScore['teleopSpecimenLow'] + allianceScore['teleopSpecimenHigh']

import numpy as np
from functools import reduce

match_teams = {}
match_scores = {}

# want to write this functionally but want to get working first
for match in test_match_data['matches']:
    # data that links these together (oops should probably use SQL eventually haha):
    # tournamentLevel in matches = matchLevel in scores
    # series in matches = matchSeries in scores
    # matchNumber in matches = matchNumber in scores
    teams = match['teams']
    active_teams = list(filter(lambda team: team['onField'], teams))
    # teams = reduce(dict.__or__, map(lambda team: {team['station']: team['teamNumber']}, active_teams), {})
    red_teams = list(map(lambda team: team['teamNumber'], filter(lambda team: "Red" in team['station'], active_teams)))
    blue_teams = list(map(lambda team: team['teamNumber'], filter(lambda team: "Blue" in team['station'], active_teams)))
    match_teams[(match['tournamentLevel'], match['series'], match['matchNumber'])] = [red_teams, blue_teams]

match = None # no footguns here!

for score in test_score_data['matchScores']:
    allianceScores = score['alliances']
    blue_stat = stat(next(filter(lambda allianceScore: allianceScore['alliance'] == 'Blue', allianceScores)))
    red_stat = stat(next(filter(lambda allianceScore: allianceScore['alliance'] == 'Red', allianceScores)))

    match_scores[(score['matchLevel'], score['matchSeries'], score['matchNumber'])] = [red_stat, blue_stat]

# We only care about the matches we have scores for
match_teams = {k: v for k, v in match_teams.items() if k in match_scores.keys()}

teams_at_event = list(set(team for d in match_teams.values() for q in d for team in q))

match_keys = list(match_scores.keys()) # set an order now

# matches*2 because 2 alliances per match, i am arbitrarily deciding to do first red then blue
alliance_matrix = np.zeros((len(match_scores) * 2, len(teams_at_event)), dtype=np.uint64)
score_matrix = np.zeros((len(match_scores) * 2, 1), dtype=np.float64)

# alliance_matrix is the design matrix X
# we'll have a score_matrix Y of relevant stats for every alliance
# X*beta = Y
# X_pinv * Y = beta

for idx, key in enumerate(match_keys):
    red_teams = list(map(lambda team: 1 if team in match_teams[key][0] else 0, teams_at_event))
    blue_teams = list(map(lambda team: 1 if team in match_teams[key][1] else 0, teams_at_event))
    alliance_matrix[idx*2] = red_teams
    alliance_matrix[idx*2+1] = blue_teams
    # Is it an interesting stat at all if we swap these?
    # (i.e. how many points did the other alliance score, then link that to your team?)
    # I wonder if it correlates to strength of schedule or defensive ability or something
    score_matrix[idx*2] = match_scores[key][0]
    score_matrix[idx*2+1] = match_scores[key][1]

# %%
opr = np.linalg.pinv(alliance_matrix)@score_matrix

opr_associated_with_team = sorted(map(lambda t: (t[1][0], teams_at_event[t[0]]), enumerate(opr)), reverse=True)
# %%
# plot it for fun!
import matplotlib.pyplot as plt

plt.figure(figsize=(12,8), dpi=300)
plt.bar(list(map(lambda t: str(t[1]), opr_associated_with_team)), list(map(lambda t: float(t[0]), opr_associated_with_team)))
plt.xlabel("team")
plt.ylabel("totalGamePieces")
plt.xticks(rotation=45, fontsize=4)
plt.savefig("totalGamePieces.png")
plt.show()
# %%
