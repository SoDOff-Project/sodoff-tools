#!/usr/bin/env python3

"""
    Script for change type of battle ships - fixed ship version
    
    Need edit this script before use - set ship type - ship_* variables (see examples bellow).
"""

import UnityPy

import json, os, sys

out_debug =  "."

# 3.28
ship_bundle = "RS_DATA/BattleShipsSnoggletogDO"
ship_object1 = "PfBattleBoatWorldEventSnoggletog1"
ship_object2 = "PfBattleBoatWorldEventSnoggletog2"
ship_name1 = "Icy Schooner"
ship_name2 = "Glacial Longboat"

# 3.26
ship_bundle = "RS_DATA/BattleShipsSummerDO"
ship_object1 = "PfBattleBoatWorldEventSummer"
ship_object2 = "PfBattleBoatWorldEventSummer2"
ship_name1 = "Warlord Light Scout"
ship_name2 = "Warlord Heavy Attacker"

# 3.19
ship_bundle = "RS_DATA/BattleShipsDreadfallDO.unity3d"
ship_object1 = "PfBattleBoatWorldEventDreadfall1"
ship_object2 = "PfBattleBoatWorldEventDreadfall2"
ship_name1 = "Dreadfall Scout"
ship_name2 = "Dreadfall Scout"

if len(sys.argv) > 2:
    in_asset = sys.argv[1]
    out_asset = sys.argv[2]
else:
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
            if "_EventObjectResourceURL" in tree:
                tree["_EventObjectResourceURL"] = ship_bundle
            if "_EventObjectResourceURL" in tree["_WorldEvent"][0]:
                tree["_WorldEvent"][0]["_EventObjectResourceURL"] = ship_bundle
            tree["_WorldEvent"][0]["_Objects"][0]["_ObjectName"] = ship_object1
            tree["_WorldEvent"][0]["_Objects"][1]["_ObjectName"] = ship_object2
            tree["_WorldEvent"][0]["_Objects"][0]["_NameText"]["_Text"] = ship_name1
            tree["_WorldEvent"][0]["_Objects"][1]["_NameText"]["_Text"] = ship_name2
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
