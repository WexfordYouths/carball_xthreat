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
import subprocess

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

def find_goals_for(team_colour, d):
   if team_colour == "Orange":
      for team in d["teams"]:
         if team["isOrange"]:
            return team["score"]
   else:
      for team in d["teams"]:
         if not team["isOrange"]:
            return team["score"]

def find_goals_against(team_colour, d):
   if team_colour == "Orange":
      for team in d["teams"]:
         if not team["isOrange"]:
            return team["score"]
   else:
      for team in d["teams"]:
         if team["isOrange"]:
            return team["score"]

overall_df = pd.DataFrame()

l = 1
for filename in os.listdir("analysis_replays"):

   try:

      ps_command = "rrrocket.exe -n " + os.path.join("C:/Users/User/Documents/carball-master/analysis_replays", filename)
      command = ["powershell", "-Command", ps_command]

      # Run the command and capture the output
      result = subprocess.run(command, capture_output=True, text=True)

      # Convert the output from string to JSON
      _json = json.loads(result.stdout)
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

   teams = {}
   for team in d["teams"]:
       teams[team["name"]] = {}
       for player_id in team["playerIds"]:
           player_id_str = player_id["id"]
           for player_d in d["players"]:
               if player_d["id"]["id"] == player_id_str:
                   player_name = player_d["name"]
           teams[team["name"]][player_id_str] = player_name

   i = 0
   total_passes = 0
   while i < len(d["gameStats"]["hits"]):
       hit = d["gameStats"]["hits"][i]

       # Ignore kickoffs
       if not hit["isKickoff"]:
           
           # Check who hit previous frame
           curr_player_hit = hit["playerId"]["id"]
           prev_player_hit = d["gameStats"]["hits"][i - 1]["playerId"]["id"]
       
           # If two players are a) different players b) on the same team,
           # then it's a pass
           if curr_player_hit != prev_player_hit and on_same_team(curr_player_hit, prev_player_hit, teams):
               
               # Find if it's an assist
               
               # Find closest goal
               for goal in d["gameMetadata"]["goals"]:
                   if goal["frameNumber"] > hit["frameNumber"]:
                       next_goal = goal
                       break
               
               # Find if between the hit and the goal, does a teammate touch the ball
               diff_teammate_hit = False
               j = 0
               new_hit = d["gameStats"]["hits"][i + j]
               while new_hit["frameNumber"] < next_goal["frameNumber"]:
                   
                  # Is this touch by a different teammate
                  if new_hit["playerId"]["id"] != curr_player_hit and on_same_team(new_hit["playerId"]["id"], curr_player_hit, teams):
                     diff_teammate_hit = True
                     break
                   
                  j += 1
                  if (i + j) < len(d["gameStats"]["hits"]):
                     new_hit = d["gameStats"]["hits"][i + j]
                  else:
                     break
               
               is_assist = (not diff_teammate_hit) and (goal["playerId"]["id"] == curr_player_hit)    
               
               
               # Find the line for plotting
               frame_start_pass = d["gameStats"]["hits"][i - 1]["frameNumber"]
               frame_end_pass = hit["frameNumber"]
               
               x = []
               y = []
               j = 0
               while j + frame_start_pass < frame_end_pass:
                   try:
                     x.append(df.ball.loc[j + frame_start_pass, "pos_x"])
                     y.append(df.ball.loc[j + frame_start_pass, "pos_y"])
                   except:
                     print("Skipping frame", j + frame_start_pass)
                   j += 1
               
               new_line = {"Game ID": d["gameMetadata"]["id"], "Team": find_team(curr_player_hit, teams), "Passer": find_player_name(prev_player_hit, teams),
                           "Reciever": find_player_name(curr_player_hit, teams), "Team Colour": find_team_colour(find_team(curr_player_hit, teams), d),
                           "Is Assist": is_assist, "Pass path x": x, "Pass path y": y, "Goals For": find_goals_for(find_team_colour(find_team(curr_player_hit, teams), d), d),
                           "Goals against": find_goals_against(find_team_colour(find_team(curr_player_hit, teams), d), d)}
               overall_df = overall_df.append(new_line, ignore_index=True)
               total_passes += 1

       i += 1
   l += 1
   print(str((l/len(os.listdir("analysis_replays"))) * 100) + "%", "remaining")
   if l % 10 == 0:
      overall_df.to_csv("passing_data" + str(l) + ".csv")

overall_df.to_csv("passes.csv")