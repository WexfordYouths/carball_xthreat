'''
Expected threat definition for Zone(x,y)
xThreat(x,y) = G(x,y) + ( M(x,y) * SUM( T(x,y -> w,z) * xThreat(w,z) ) )
, where 
    - G(x,y) = Goal probability directly for Zone(x,y) = Goals from zone / Total Events in zone
    - M(x,y) = Move probability from Zone(x,y) = Total passes + Total dribbles from zone to different zone / Total Events in zone
    - T(x,y -> w,z) = Transition probability from Zone(x,y) to Zone (w,z) = passes + dribbles from Zone(x,y) -> Zone(w,z) / Total passes + Total dribbles

    - An 'Event' is the last hit by a particular player in a zone, that results in 
       a) a goal directly for that player
       b) a Pass/ Dribble into a new zone (a 'Move' in the context of the formula above)
       c) loss of possession

This formula requires you have the xThreat for every other zone, which leads to a cyclic problem of not being able to find any zones xThreat
This can be fixed by setting the xThreat for every other zone to 0 initially, which makes the right hand side of the formula 0,
so the formula is simply the goal probability from that zone.
You then iteritively find the xThreat for every zone again, until the values converge.
'''

import carball
import gzip
from carball.json_parser.game import Game
from carball.analysis.analysis_manager import AnalysisManager
import json
import math
from matplotlib import pyplot as plt
import matplotlib.lines as lines
import pandas as pd
import numpy as np
import os

def find_team_colour(team_name, d):
   for team in d["teams"]:
      if team["name"] == team_name:
         if team["isOrange"]:
            return "Orange"
         else:
            return "Blue"

def find_player_name(player_id, teams):
    for team in teams.keys():
        if player_id in teams[team].keys():
            return teams[team][player_id]

def find_team(player_id, teams):
   for team in teams.keys():
      players = teams[team]
      for playerid in players.keys():
         if playerid == player_id:
            return team

def on_same_team(player_1, player_2, teams):
   for team in teams.keys():
      if player_1 in teams[team].keys() and player_2 in teams[team].keys():
         return True
   return False

def create_teams_dict(d):
   teams = {}
   for team in d["teams"]:
       teams[team["name"]] = {}
       for player_id in team["playerIds"]:
           player_id_str = player_id["id"]
           for player_d in d["players"]:
               if player_d["id"]["id"] == player_id_str:
                   player_name = player_d["name"]
           teams[team["name"]][player_id_str] = player_name
   return teams

def create_transition_dict():
   d = {}
   for i in range(0, 8):
      for j in range(0, 10):
         zone_string = "x" + str(i) + "-y" + str(j)
         d[zone_string] = 0
   return d

def create_event_dict():
   d = {}
   x_diff = (4096 * 2) / 6
   y_diff = (5120 * 2) / 8

   for i in range(0, 6):
      for j in range(0, 8):
         zone_string = "x" + str(i) + "-y" + str(j)
         d[zone_string] = {"X range": (-4096 + (i * x_diff), -4096 + ((i + 1) * x_diff)),
                           "Y range": (-5120 + (j * y_diff), -5120 + ((j + 1) * y_diff)),
                           "Total events": 0,
                           "Total goals": 0,
                           "Total moves": 0,
                           "Transition dict": create_transition_dict()}
   return d

def find_zone_str(event_data, coord):
   for (key, value) in event_data.items():
      if coord[0] >= value["X range"][0] and coord[0] <= value["X range"][1]:
         if coord[1] >= value["Y range"][0] and coord[1] <= value["Y range"][1]:
            return key

def get_ball_position(coord, team_colour):
   pos_x = - coord[0]
   pos_y = coord[1]
   if team_colour == "Orange":
      pos_y = - pos_y

   if pos_x < -5120:
      pos_x = -5120
   if pos_x > 5120:
      pos_x = 5120
   if pos_y < -4096:
      pos_y = -4096
   if pos_y > 4096:
      pos_y = 4096

   return (pos_x, pos_y)

def is_goal(d, i, teams):
   '''i = index of hit'''
   hit = d["gameStats"]["hits"][i]
   curr_player = find_player_name(hit["playerId"]["id"], teams)

   # Find next closest goal
   for goal in d["gameMetadata"]["goals"]:
      if goal["frameNumber"] > hit["frameNumber"]:
         next_goal = goal
         break

   if "next_goal" not in locals():
      return False

   

   # Did this player or teammate hit the ball between the initial hit and the goal
   j = 1
   if (i + j) < len(d["gameStats"]["hits"]):
     next_hit = d["gameStats"]["hits"][i + j]
     while next_hit["frameNumber"] < next_goal["frameNumber"]:
        next_player = find_player_name(next_hit["playerId"]["id"], teams)
        if next_player == curr_player or on_same_team(curr_player, next_player, teams):
           return False

        j += 1
        if (i + j) < len(d["gameStats"]["hits"]):
           next_hit = d["gameStats"]["hits"][i + j]
        else:
           break
   return curr_player == find_player_name(next_goal["playerId"]["id"], teams)

event_data = create_event_dict()


k = 0
for filename in os.listdir("all_rlcs_replays"):
  try:

    _json = carball.decompile_replay(os.path.join("C:/Users/User/Documents/carball-master/all_rlcs_replays", filename))

    # _json is a JSON game object (from decompile_replay)
    game = Game()
    game.initialize(loaded_json=_json)

    analysis_manager = AnalysisManager(game)
    analysis_manager.create_analysis()
              
    # return the proto object in python
    proto_object = analysis_manager.get_protobuf_data()
    #print(type(proto_object))

    # return the proto object as a json object
    d = analysis_manager.get_json_data()

    # # return the pandas data frame in python
    df = analysis_manager.get_data_frame()
  except:
    print("Skiping replay", filename)
    continue

  # Create team dictionary
  teams = create_teams_dict(d)

  # Create dict for event data

  # Events are the END of dribbles, a pass or shot resulting in a goals
  total_goals = 0
  i = 0
  while i < len(d["gameStats"]["hits"]):
     hit = d["gameStats"]["hits"][i]

     # Ignore kickoffs
     if not hit["isKickoff"]:

        pos_x, pos_y = get_ball_position((hit["ballData"]["posX"], hit["ballData"]["posY"]), find_team_colour(find_team(hit["playerId"]["id"], teams), d))

        zone_hit = find_zone_str(event_data, (pos_x, pos_y))

        player_hit = find_player_name(hit["playerId"]["id"], teams)

        # Is it the last hit by this player in this zone?
        
        # Last hit of game, has to be last hit in zone
        last_hit = False
        if i + 1 == len(d["gameStats"]["hits"]):
           last_hit = True

        else:
           next_hit = d["gameStats"]["hits"][i + 1]
           next_player_hit = find_player_name(next_hit["playerId"]["id"], teams)
           next_zone_hit = find_zone_str(event_data, get_ball_position((next_hit["ballData"]["posX"], next_hit["ballData"]["posY"]), find_team_colour(find_team(hit["playerId"]["id"], teams), d)))


           # If the next hit was by a different player, then it is the last hit
           if player_hit != next_player_hit:
              last_hit = True

           # If the next hit was by the same player but in a DIFFERENT ZONE
           if player_hit == next_player_hit and zone_hit != next_zone_hit:
              last_hit = True

        # Was it the last hit?
        if last_hit:

           # Increment event counter
           event_data[zone_hit]["Total events"] += 1

           # Find if goal was scored directly
           if is_goal(d, i, teams):
              event_data[zone_hit]["Total goals"] += 1
              total_goals += 1
              i += 1
              continue

           # If there was no other hit after this hit and it was not a goal, then stop
           if i + 1 == len(d["gameStats"]["hits"]):
              break

           # Find if next hit was made by player or teammate
           if next_player_hit == player_hit or on_same_team(next_player_hit, player_hit, teams):
              event_data[zone_hit]["Total moves"] += 1
              event_data[zone_hit]["Transition dict"][next_zone_hit] += 1
       
     i += 1
  k += 1
  print(str((k / len(os.listdir("all_rlcs_replays"))) * 100) + "%",  "of replays completed")

with open("event_data.json", "w") as fd:
   json.dump(event_data, fd, indent=3)

