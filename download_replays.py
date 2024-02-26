import requests
import json
import time

def list_replays(token, group_id):
    r = requests.get("https://ballchasing.com/api/replays/", headers={
                      'Authorization': token, "Content-Type": "application/json"}, params={"group": group_id})

    time.sleep(3)

    return r.json()

def list_subgroups(token, group_id):
    r = requests.get("https://ballchasing.com/api/groups/", headers={
                      'Authorization': token, "Content-Type": "application/json"}, params={"group": group_id})

    time.sleep(3)

    return r.json()

def save_replay(token, replay_id, folder_path):
    r = requests.get("https://ballchasing.com/api/replays/" + replay_id + "/file", headers={
                      'Authorization': token, "Content-Type": "application/octet-stream", 
                      'Content-Disposition': 'filename="original-filename.replay"'})
    time.sleep(3)

    with open(folder_path + replay_id + ".replay", "wb") as fd:
      fd.write(r.content)


def loop_through_groups(token, group_id, folder_path):
   '''Recursively loop through folders looking for replays to save'''
   # If there are replays in group, save them to folder_path
   replays = list_replays(token, group_id)
   for replay in replays["list"]:
      save_replay(token, replay["id"], folder_path)

   # Go through subgroups
   subgroups = list_subgroups(token, group_id)
   for subgroup in subgroups["list"]:
      loop_through_groups(token, subgroup["id"], folder_path)

def main():
   # url="https://ballchasing.com/api/replays/c91e5259-0af1-4b30-9b40-4f77effec7c3?g=dig-vs-omlt-wlqdvb6oq1/file"
   replay_group_id = "open-qualifiers-2-aj3y5fbed2"
   token = "F7dFZe55u57HxPlPsVk9AN2WBhrd5PsMvY24E2Yq"

   folder_path = r"C:/Users/User/Documents/carball-master/analysis_replays/"

   loop_through_groups(token, replay_group_id, folder_path)

if __name__ == '__main__':
   main()
