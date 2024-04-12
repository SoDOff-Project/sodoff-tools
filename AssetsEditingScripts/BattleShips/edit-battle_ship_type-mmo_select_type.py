#!/usr/bin/env python3

"""
    Script for change type of battle ships - allow mmo server to decide about ship type.
    (by set `EventName` in mmo `appsettings.json` to one of following values: ScoutAttack ScoutAttack_Thawfest ScoutAttack_Summer ScoutAttack_Dreadfall ScoutAttack_Snoggletog)
"""

import UnityPy

import json, os, sys

out_debug =  "."

in_asset = "./hubtrainingdo_org"
out_asset = "./hubtrainingdo"

asset_flags = (
    # data_flag
    #   0x02 -> lz4 compression of `block_data`
    #   0x40 -> contain DirectoryInfo (must be set for UnityPy)
    #   not 0x80 -> `block_data` before `file_data` (require for `UnityWebRequest.downloadProgress` return non zero progress while downloading asset)
    0x42,
    # block_info_flag
    #   0x02 -> lz4 compression of `file_data`
    0x02
)

if not os.path.isfile(in_asset):
    print(f"Input asset file {in_asset} do not exist")
    exit()

env = UnityPy.load(in_asset)
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if "_WorldEvent" in tree:
            if out_debug:
                with open(out_debug + "/WorldEventScoutAttack-org.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
            tree["_WorldEvent"][0]["_Name"] = "ScoutAttack";
            tree["_WorldEvent"][1]["_Name"] = "ScoutAttack_Thawfest";
            tree["_WorldEvent"][2]["_Name"] = "ScoutAttack_Summer";
            tree["_WorldEvent"][3]["_Name"] = "ScoutAttack_Dreadfall";
            tree["_WorldEvent"][4]["_Name"] = "ScoutAttack_Snoggletog";
            
            tree["_WorldEvent"][0]["_SeasonalEventName"] = "";
            tree["_WorldEvent"][1]["_SeasonalEventName"] = "";
            tree["_WorldEvent"][2]["_SeasonalEventName"] = "";
            tree["_WorldEvent"][3]["_SeasonalEventName"] = "";
            tree["_WorldEvent"][4]["_SeasonalEventName"] = "";
            
            x = obj.save_typetree(tree)

 
with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))


if out_debug: # check 
    env = UnityPy.load(out_asset)
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if "_WorldEvent" in tree:
                tree = obj.read_typetree()
                with open(out_debug + "/WorldEventScoutAttack-new.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
                break
