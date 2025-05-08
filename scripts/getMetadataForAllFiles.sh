#!/bin/bash

# below suggested by: https://stackoverflow.com/questions/54467389/how-to-have-bash-scripts-reference-local-files
SCRIPTPATH=$(dirname "$0")

# TODO: consider listing the directories, or, depeding on the value of $2, just the
# number of the create time... or something...

find -L "$1"  -exec $SCRIPTPATH"/.helper_getFileMetadata.sh" "{}" "$2" \;

