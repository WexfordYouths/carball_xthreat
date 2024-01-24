import os

delete_replays = os.listdir("delete_replays")

for replay in delete_replays:
   filepath = os.path.join("C:/Users/User/Documents/carball-master/all_rlcs_replays", replay)
   if os.path.isfile(filepath):
      print("Removing", filepath)
      os.remove(filepath)