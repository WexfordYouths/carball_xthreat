import carball
import gzip
from carball.json_parser.game import Game
from carball.analysis.analysis_manager import AnalysisManager
import json

_json = carball.decompile_replay('C:/Users/User/Downloads/game_2.replay')

# _json is a JSON game object (from decompile_replay)
game = Game()
game.initialize(loaded_json=_json)

analysis_manager = AnalysisManager(game)
analysis_manager.create_analysis()
    
# return the proto object in python
proto_object = analysis_manager.get_protobuf_data()
#print(type(proto_object))

# return the proto object as a json object
json_oject = analysis_manager.get_json_data()

# # return the pandas data frame in python
dataframe = analysis_manager.get_data_frame()

with open("game_2_proto_game.json", "w") as fd:
   json.dump(json_oject, fd, indent=3)

with open("game_2_all_data.json", "w") as f:
   json.dump(_json, f, indent=3)
