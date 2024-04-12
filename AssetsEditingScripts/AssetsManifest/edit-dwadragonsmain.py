#!/usr/bin/env python3

"""
    Script for add new entries or/and change hash of existed entries in AssetBundleManifest (dwadragonsmain).
    
    Need edit this script (to set name of entries and hash value) before use.
"""

import UnityPy

import json, os, sys

out_debug = "."

ver1 = 0
ver2 = 0
dev = 13

new_assets = [
    # "shareddata/dwcrimsonhowlerdo",
    # "shareddata/dwcrimsonhowleranimbasic",
    # "shareddata/dwcrimsonhowleranimfull",
    # "shareddata/dwcrimsonhowleranimplayer",
]
new_assets_fileId = 0 # override fileId - no quality version for new_assets

updated_assets = [
    # "data/pfsanctuarydatado",
    # "data/dragonsres"
]

if len(sys.argv) > 3:
    in_asset = sys.argv[2]
    out_asset = sys.argv[3]
else:
    in_asset = "./dwadragonsmain_org"
    out_asset = "./dwadragonsmain"

fileId = 0
if len(sys.argv) > 1:
    if sys.argv[1] == "High":
        fileId = 1
    elif sys.argv[1] == "Mid":
        fileId = 2
    elif sys.argv[1] == "Low":
        fileId = 3
    else:
        fileId = int(sys.argv[1])

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
    if obj.type.name == "AssetBundleManifest":
        if obj.serialized_type.nodes:
            tree = obj.read_typetree()
            if out_debug:
                with open(out_debug + "/manifest-org.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
            
            aid = 0
            aids = {}
            for x in tree["AssetBundleNames"]:
                if x[1] in updated_assets:
                    aids[x[0]] = x[1]
                if aid < x[0]:
                    aid = x[0]

            for x in tree["AssetBundleInfos"]:
                if x[0] in aids:
                    x[1]["AssetBundleHash"]["bytes[0]"] = 83
                    x[1]["AssetBundleHash"]["bytes[1]"] = 111
                    x[1]["AssetBundleHash"]["bytes[2]"] = 68
                    x[1]["AssetBundleHash"]["bytes[3]"] = 79
                    x[1]["AssetBundleHash"]["bytes[4]"] = 102
                    x[1]["AssetBundleHash"]["bytes[5]"] = 102
                    x[1]["AssetBundleHash"]["bytes[6]"] = 0
                    x[1]["AssetBundleHash"]["bytes[7]"] = 0
                    x[1]["AssetBundleHash"]["bytes[8]"] = ver1
                    x[1]["AssetBundleHash"]["bytes[9]"] = ver2
                    x[1]["AssetBundleHash"]["bytes[10]"] = 0
                    x[1]["AssetBundleHash"]["bytes[11]"] = 0
                    x[1]["AssetBundleHash"]["bytes[12]"] = 0
                    x[1]["AssetBundleHash"]["bytes[13]"] = dev
                    x[1]["AssetBundleHash"]["bytes[14]"] = 0
                    x[1]["AssetBundleHash"]["bytes[15]"] = fileId

            if not new_assets_fileId is None:
                fileId = new_assets_fileId

            for new_asset_path in new_assets:
                aid += 1
                tree["AssetBundleNames"].append([aid, new_asset_path]) 
                tree["AssetBundleInfos"].append([aid, json.loads("""{
                    "AssetBundleHash": {
                        "bytes[0]": 83,
                        "bytes[1]": 111,
                        "bytes[2]": 68,
                        "bytes[3]": 79,
                        "bytes[4]": 102,
                        "bytes[5]": 102,
                        "bytes[6]": 0,
                        "bytes[7]": 0,
                        "bytes[8]": 1,
                        "bytes[9]": 0,
                        "bytes[10]": 0,
                        "bytes[11]": 0,
                        "bytes[12]": 0,
                        "bytes[13]": """ + str(dev) + """,
                        "bytes[14]": 0,
                        "bytes[15]": """ + str(fileId) + """
                    },
                    "AssetBundleDependencies": []
                }""")])
                
            x = obj.save_typetree(tree)

 
with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))


if out_debug: # check 
    env = UnityPy.load(out_asset)
    for obj in env.objects:
        if obj.type.name == "AssetBundleManifest":
            if obj.serialized_type.nodes:
                tree = obj.read_typetree()
                with open(out_debug + "/manifest-new.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
                break
