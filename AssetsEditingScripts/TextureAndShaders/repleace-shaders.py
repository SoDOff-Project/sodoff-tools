#!/usr/bin/env python3

"""
    Script for replacing shaders in asset bundle.
    Allow use og shaders in custom build asset bundles.
    
    Need configure list of replaced shaders in repleace-shaders.json
"""

import UnityPy
import json, os, pprint, sys

if len(sys.argv) < 3:
    print(f"USAGE: {sys.argv[0]} input_asset_file output_asset_file")
    exit()

in_asset = sys.argv[1]
out_asset = sys.argv[2]

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
shaders = json.load(open(os.path.dirname(__file__) + "/repleace-shaders.json"))

for obj in env.objects:
    if obj.type.name == "Shader":
        data = obj.read_typetree()
        name = data["m_ParsedForm"]["m_Name"]
        if name in shaders:
            shaders[name]["path_id"] = obj.path_id
            with open(shaders[name]["file"], "rb") as f:
                obj.set_raw_data(f.read())

fileData = env.file.save()
env = UnityPy.load(fileData)

# for obj in env.objects:
#     if obj.type.name == "Shader":
#         data = obj.read_typetree()
#         name = data["m_ParsedForm"]["m_Name"]
#         if name in shaders:
#             shaders[name]["object"] = obj

for obj in env.objects:
    if obj.type.name == "Shader":
        data = obj.read_typetree()
        name = data["m_ParsedForm"]["m_Name"]
        if name in shaders and "map" in shaders[name]:
            for d in range(len(data["m_Dependencies"])):
                oldId = str(data["m_Dependencies"][d]["m_PathID"])
                dName = shaders[name]["map"].get(oldId, None)
                if not "path_id" in shaders[dName]:
                    raise BaseException(f"sharer {dName} (dependency of {name}) is missing in asset")
                if dName:
                    data["m_Dependencies"][d]["m_PathID"] = shaders[dName]["path_id"]
            obj.save_typetree(data)
        
with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))
