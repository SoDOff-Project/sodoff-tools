#!/usr/bin/env python3

"""
    Script for replacing all textures in asset bundle.
    Allow convert "Low" version into "High" to fix broken UV (in "Mid" and "High" versions) on some objects.

    Usage example:

    X.bad - Hight version with broken UV
    X.ok - Low version with correct UV

    1. extract textures from `X.bad` using asset ripper (or other tool)
    2. run:
        name="X"; python3 replace-all-textures.py $name.ok $name extracted/$name.bad/ExportedProject/Assets/Texture2D/

    In some special cases (e.g. missed alpha channel) it may also be necessary to change the texture format.
    By default script do not change format, if needed set `change_format` to `True` (then will be set RGBA32 for RGBA input file).
    Caution: in some cases changing texture format may results in game crash.
    
    In case of duplicated textures names rename all duplicated images file to {name}___path_id___{pathid}.png
    (for example for file xxx.png with path id 123 name should be xxx___path_id___123.png).
"""

change_format = False
allow_lower_quality = False

def NoLog(*x): pass
LogSuccess = NoLog
LogError = print

import UnityPy
from PIL import Image
import os, sys

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

if len(sys.argv) < 4:
    print(f"USAGE: {sys.argv[0]} input_asset_file_path output_asset_file_path directory_with_textures_to_replace")
    exit()

in_asset = sys.argv[1]
out_asset = sys.argv[2]
textures_dir = sys.argv[3]

if not os.path.isfile(in_asset):
    print(f"Input asset file {in_asset} do not exist")
    exit()

env = UnityPy.load(in_asset)

used = []
for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        new_file = textures_dir + "/" + data.name + "___path_id___" + str(data.path_id) + ".png"
        if not os.path.isfile(new_file):
            new_file = textures_dir + "/" + data.name + ".png"
            if data.name in used:
                print("Warning duplicated use of " + data.name + ".png file")
            else:
                used.append(data.name)
        if not os.path.isfile(new_file):
            LogError("skip (not found)", data.name, data.path_id)
            continue
        try:
            pil_img = Image.open(new_file)
            if allow_lower_quality or data.m_Width <= pil_img.size[0] or data.m_Height <= pil_img.size[1]:
                data.image = pil_img
                if change_format and pil_img.mode == 'RGBA':
                    data.m_TextureFormat = UnityPy.enums.TextureFormat.RGBA32
                data.m_Width = pil_img.size[0]
                data.m_Height = pil_img.size[1]
                data.save()
                LogSuccess("done", data.name, data.path_id)
            else:
                LogError("skip (quality)", data.name, data.path_id)
        except Exception as err:
            LogError(f"skip (error={err})", data.name, data.path_id)

with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))
