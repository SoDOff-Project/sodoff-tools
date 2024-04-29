#!/usr/bin/env python3

"""
    Tool for create password hash for reset password directly in SoDOff database
    
    Usage:
      python3 MakePassword.py password
"""

import secrets, hashlib, base64

def makePassword(password):
	# setting: V3, 128-bit salt, 10000 iterations
	prefix = b"\x01\x00\x00\x00\x01\x00\x00'\x10\x00\x00\x00\x10"
	salt = secrets.token_bytes(16)
	subkey = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000, 32)
	return base64.b64encode(prefix + salt + subkey).decode()

if __name__ == "__main__":
	import sys
	if len (sys.argv) == 1:
		print (f"USAGE {sys.argv[0]} input_file [decrypt]")
	else:
		print (makePassword(sys.argv[1]))
