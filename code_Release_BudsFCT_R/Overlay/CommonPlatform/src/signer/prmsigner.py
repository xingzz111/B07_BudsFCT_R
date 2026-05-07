#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/4/16 09:33
=====================
"""
import os
import sys
import pickle
import argparse
from hashlib import sha1


def signer(sigPath):
    sigPath = os.path.abspath(sigPath)
    if not os.path.exists(sigPath):
        print("Please check signer project is exists!", file=sys.stdout)
        sys.stdout.flush()
        sys.exit(1)
    if not os.path.isdir(sigPath):
        print("Please check signer project is folder!", file=sys.stdout)
        sys.stdout.flush()
        sys.exit(1)

    sigFileTab = {}
    for root, dirs, files in os.walk(sigPath):
        for file in files:
            fileType = os.path.splitext(file)[-1]
            if fileType.lower() in (".py", ".json", ".csv", ".lua", ".sh", ".png", ".jpg"):
                absPathFile = os.path.join(root, file)
                with open(absPathFile, "rb") as f:
                    data = f.read()
                    code = sha1(data).hexdigest()
                    relativePath = absPathFile.replace(sigPath, "<<root>>")
                    sigFileTab[relativePath] = code
                    print(f"{relativePath} = {code}", file=sys.stdout)

    packData = pickle.dumps(sigFileTab)
    sigFile = os.path.join(sigPath, "encrypted.sig")
    with open(sigFile, "wb") as f:
        f.write(packData)
    print("Signature Finish", file=sys.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--signerDir', help='Signer project', type=str, required=True)
    args = parser.parse_args()

    signer(args.signerDir)