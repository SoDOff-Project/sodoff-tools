#!/usr/bin/env python3

"""
    Tool for encrypt / decrypt DWADragonsMain.xml
    
    Usage:
      python3 FileEncryption.py input_file [decrypt]
"""

from Cryptodome.Cipher import DES3
from Cryptodome.Util.Padding import pad, unpad
from hashlib import md5
from base64 import b64decode, b64encode

# based on https://github.com/hictooth/sodoff/blob/master/sodoff/api/common/des.py by hictooth, AGPL-3.0 license

ENCODING_WRAPPING_NONE = '{encrypted}'
ENCODING_WRAPPING_XML_STRING = '<?xml version="1.0" encoding="utf-8"?>\n<string>{encrypted}</string>'

BLOCK_SIZE = 8

# the key initially used by the game for the DWADragonsMain.xml file
ASCII_KEY = 'C92EC1AA-54CD-4D0C-A8D5-403FCCF1C0BD'
ASCII_CODING = 'utf-8'

# the key used for api requests
KEY = '56BB211B-CF06-48E1-9C1D-E40B5173D759'
CODING = 'utf-16-le'

# the key used for signing
SIGN_KEY = '11A0CC5A-C4DF-4A0E-931C-09A44C9966AE'

# converts the string keys as used by SoD to DES keys
def get_key(key_string, coding):
  key_bytes = key_string.encode(encoding=coding)
  key_hash = md5(key_bytes).digest()
  # repeat first 8 bytes at the end to get full 24 byte key array
  return key_hash + key_hash[:8]


def decrypt(input, key, coding):
  key = get_key(key, coding)
  cipher = DES3.new(key, DES3.MODE_ECB)
  base64_decoded = b64decode(input)
  decrypted = cipher.decrypt(base64_decoded)
  decrypted_unpadded = unpad(decrypted, BLOCK_SIZE)
  decrypted_string = decrypted_unpadded.decode(coding)
  return decrypted_string


def encrypt(input, key, coding, wrapping = None):
  key = get_key(key, coding)
  cipher = DES3.new(key, DES3.MODE_ECB)
  input_bytes = input.encode(encoding=coding)
  input_bytes_padded = pad(input_bytes, BLOCK_SIZE)
  encrypted = cipher.encrypt(input_bytes_padded)
  encrypted_string = b64encode(encrypted)
  if wrapping:
    return wrapping.format(encrypted=encrypted_string.decode('utf-8')).encode('utf-8')
  else:
    return encrypted_string


def generate_signature(key, text):
  totaltext = key + text
  totaltext_bytes = totaltext.encode('utf-8')
  hashed = md5(totaltext_bytes)
  return hashed.hexdigest()

if __name__ == "__main__":
  import sys
  if len (sys.argv) == 1:
    print (f"USAGE {sys.argv[0]} input_file [decrypt]")
  elif len (sys.argv) > 2 and sys.argv[2] == "decrypt":
    print(decrypt(open(sys.argv[1]).read(), ASCII_KEY, ASCII_CODING), end='')
  else:
    print(encrypt(open(sys.argv[1]).read(), ASCII_KEY, ASCII_CODING).decode(), end='')

