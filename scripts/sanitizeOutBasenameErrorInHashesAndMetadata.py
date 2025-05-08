#! /usr/bin/python3


import sys

fileName = sys.stdin.readline().replace("\n","");

fh=open(fileName, "r");
A=fh.read();
fh.close();

import hashlib

import base64

def getSha512HashInBase64(stringToHash):
    return base64.encodebytes(hashlib.sha512(str.encode(stringToHash, "utf-8")).digest()).decode().replace("\n","");

B=[];
for thisLine in A.split("\n"):
    if(len(thisLine) == 0):
        continue;
    if(thisLine=="Try 'basename --help' for more information."):
        continue;
    if("basename" in thisLine):
        assert(thisLine.count(",") >= 12); # the field seperator should be present and correct for the previous correctly formatted content.
        (left, match, right)=thisLine.partition("basename:");
        if("basename" in (left+right)):
            raise Exception("Special case"); # in principle possible, but we'd like to handle it as a special case
        B.append(left+ ",6807e895-9b3d-487b-b037-ea643256712d" + getSha512HashInBase64(right)); # a UUID is used so the lines where this replacedment occurred are easily found and very unlikely to collide with any names preexisting.
    else:
        assert(thisLine.count(",") >= 12 or thisLine.count(",") == 2) ;
        B.append(thisLine +"\n");
print("".join(B),flush=True);
