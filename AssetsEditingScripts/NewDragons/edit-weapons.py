#!/usr/bin/env python3

"""
    Sample script for creating new dragon fire type.
    
    Need edit this script before use.
"""

import UnityPy

import json, os

out_debug = "."

in_asset = "./dragonsres_org"
out_asset = "./dragonsres"

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

root = env.container['assets/dragonsres/pfweapontunedata.prefab']
for obj in root.read().m_Components:
    if obj.type.name == "MonoBehaviour":
        if obj.serialized_type.nodes:
            tree = obj.read_typetree()
            if out_debug:
                with open(out_debug + "/WeaponTuneData-org.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
            
            a, b = None, None
            for w in tree["_Weapons"]:
                if w["_Name"] == "CrimsonGoregutter":
                    a = w
                if w["_Name"] == "WoolyHowl":
                    b = w

            newTune = a.copy()
            newTune["_Name"] = "CrimsonHowler"
            newTune["_AdditionalProjectile"] = [
                {
                    "_ProjectilePrefab": b["_ProjectilePrefab"],
                    "_HitPrefab": b["_HitPrefab"]
                }
            ]
            tree["_Weapons"].append(newTune)
            x = obj.save_typetree(tree)

with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))


if out_debug: # check
    env = UnityPy.load(out_asset)
    root = env.container['assets/dragonsres/pfweapontunedata.prefab']
    for obj in root.read().m_Components:
        if obj.type.name == "MonoBehaviour":
            if obj.serialized_type.nodes:
                tree = obj.read_typetree()
                with open(out_debug + "/WeaponTuneData-new.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
                break
