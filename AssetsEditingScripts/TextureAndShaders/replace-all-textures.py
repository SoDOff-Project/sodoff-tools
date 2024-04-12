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

    In some special cases (e.g. missed alpha channel) it may also be necessary to change the texture format - by default script set RGBA32 for RGBA input file.
"""

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
    print(f"Usage {sys.argv[0]} input_asset_file_path output_asset_file_path directory_eith_textures_to_replace")
    exit()

in_asset = sys.argv[1]
out_asset = sys.argv[2]
textures_dir = sys.argv[3]

if not os.path.isfile(in_asset):
    print(f"Input asset file {in_asset} do not exist")
    exit()

env = UnityPy.load(in_asset)

for obj in env.objects:
    if obj.type.name == "Texture2D":
    # replace textures
        data = obj.read()
        new_file = textures_dir + "/" + data.name + ".png"
        if os.path.isfile(new_file):
            try:
                pil_img = Image.open(new_file)
                if data.m_Width <= pil_img.size[0] or data.m_Height <= pil_img.size[1]:
                    data.image = pil_img
                    if pil_img.mode == 'RGBA':
                        data.m_TextureFormat = UnityPy.enums.TextureFormat.RGBA32
                    data.m_Width = pil_img.size[0]
                    data.m_Height = pil_img.size[1]
                    data.save()
                else:
                    print("skip (quality)", data.name)
            except Exception as err:
                print(f"skip (error={err})", data.name)
        else:
            print("skip (not found)", data.name)

with open(out_asset, "wb") as f:
    f.write(env.file.save(packer=asset_flags))
