#!/usr/bin/env python3

"""
    Script for edit Dragon Racing track list
    
    Need to prepare new list (`_TrackData` array) in racing_tracks.json
"""

import UnityPy

import json, os, sys

out_debug =  "./" # + (sys.argv[1] if len(sys.argv) > 1 else "")

if len(sys.argv) > 2:
    in_asset = sys.argv[1]
    out_asset = sys.argv[2]
else:
    in_asset = "./dragonracingdo_org"
    out_asset = "./dragonracingdo"
newTracksData = json.load(open(os.path.dirname(__file__) + "/racing_tracks.json"))

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
        if "_GameModeData" in tree and '_TrackData' in tree:
            if out_debug:
                with open(out_debug + "TrackData-org.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
            tree['_TrackData'] = newTracksData
            obj.save_typetree(tree)
            break
 
with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))

if out_debug: # check 
    env = UnityPy.load(out_asset)
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if "_TrackData" in tree:
                tree = obj.read_typetree()
                with open(out_debug + "TrackData-new.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
                break
