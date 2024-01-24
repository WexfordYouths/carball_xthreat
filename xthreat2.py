import json
import copy

with open("event_data.json", "r") as fd:
   d = json.load(fd)

# Firstly, say every other xThreat is 0
for key in d.keys():
   if d[key]["Total events"] == 0:
      d[key]["xThreat"] = 0
   else:
      d[key]["xThreat"] = d[key]["Total goals"] / d[key]["Total events"]

prev = copy.deepcopy(d)

# Now iterate with the xThreat formula
i = 0
while True:
   for key in prev.keys():
      if prev[key]["Total events"] == 0:
         d[key]["xThreat"] = 0
      else:
         goal_prob = prev[key]["Total goals"] / prev[key]["Total events"]
         move_prob = prev[key]["Total moves"] / prev[key]["Total events"]
         total = 0
         for k in prev[key]["Transition dict"].keys():
            transition_prob = prev[key]["Transition dict"][k] / prev[key]["Total moves"]
            total += transition_prob * prev[key]["xThreat"]

         d[key]["xThreat"] = goal_prob + (move_prob * total)

   if prev == d or i > 500:
      break
   else:
      prev = copy.deepcopy(d)
      i += 1
      print(i)

with open("xThreat_data.json", "w") as fd:
   json.dump(d, fd, indent=3)