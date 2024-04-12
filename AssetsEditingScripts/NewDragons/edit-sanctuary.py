#!/usr/bin/env python3

"""
    Script for adding new dragons (sanctuary pet type).
    
    Need prepare new_sanctuary_pet.json with single `_PetTypes` array entry (you can use output file sanctuarydata-org.json as example) and update `newPetType` variable bellow.
"""

import UnityPy

import json, os

out_debug = "."

newPetType = ("Tough", "Ice")
newPetData = json.load(open(os.path.dirname(__file__) + "/new_sanctuary_pet.json"))

in_asset = "./pfsanctuarydatado_org"
out_asset = "./pfsanctuarydatado"


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
        if obj.serialized_type.nodes:
            tree = obj.read_typetree()
            if out_debug:
                with open(out_debug + "/SanctuaryData-org.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
            
            tree["_PetTypes"].append(newPetData)
            
            typeId = newPetData["_TypeID"]
            
            for ti in tree["_PrimaryTypeInfo"]:
                if ti["_PrimaryType"] == newPetType[0]:
                    ti["_PetTypeIDs"].append(typeId)
                    break
            
            for ti in tree["_SecondaryTypeInfo"]:
                if ti["_SecondaryType"] == newPetType[1]:
                    ti["_PetTypeIDs"].append(typeId)
                    break
            
            # tree["_DragonCustomizationInfo"] = []
            # for pet in tree["_PetTypes"]:
            #     if pet["_TypeID"] == 104:
            #         scale = 1.2
            #         pet["_AgeData"][3]["_BoneInfo"][0]["_Scale"]["x"] = scale
            #         pet["_AgeData"][3]["_BoneInfo"][0]["_Scale"]["y"] = scale
            #         pet["_AgeData"][3]["_BoneInfo"][0]["_Scale"]["z"] = scale
            
            x = obj.save_typetree(tree)
            
            break

with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))


if out_debug: # check
    env = UnityPy.load(out_asset)
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            if obj.serialized_type.nodes:
                tree = obj.read_typetree()
                with open(out_debug + "/SanctuaryData-new.json", "wt", encoding = "utf8") as f:
                    json.dump(tree, f, ensure_ascii = False, indent = 4)
                break
