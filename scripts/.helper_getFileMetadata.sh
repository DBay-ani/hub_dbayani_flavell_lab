#!/bin/bash

# NOTE: this file has some issue properly handle some strange names, for example, the file created with the 
# following:
#     touch "example\" ther - *\'"

# Syntax on the below suggested by https://stackoverflow.com/questions/9332802/how-to-write-a-bash-script-that-takes-optional-input-arguments
addNames=${2:-"addName"};


if [[ $addNames != "addName" && $addNames != "--no-name" ]];
then
    echo "Unrecognized second argument."; exit 1 ;  
fi;

# If processing a directory, the area that would print the sha512sum hash instead prints "Not_Applicable"
( echo -n $( ( timeout --signal=9 600 sha512sum  "$1" 2> /dev/null || echo "Not_Applicable_Or_Timeout") | awk -F" " '{print $1}')","$( TZ=utc timeout --signal=9 600 stat --format="%F,%b,%B,%s,%w,%W,%x,%X,%y,%Y,%z,%Z" "$1" ); ) || echo "Time_Out_Error"

# By putting the file name at the end, we know where the file starts and end, even if the name contains
# commas, since the material before it had a fix number of fields.
if [ $addNames = "--no-name" ]; 
then
    echo "";
    # echo $( TZ=utc stat --format="%b,%B,%s,%w,%W,%x,%X,%y,%Y,%z,%Z" "$1" )","$(sha512sum "$1" | awk -F" " '{print $1}');
elif [ $addNames = "addName" ]; 
then
    # echo $( TZ=utc stat --format="%b,%B,%s,%w,%W,%x,%X,%y,%Y,%z,%Z" "$1" )","$(sha512sum "$1" | awk -F" " '{print $1}');
    echo ,$(echo $1 | sha512sum  | awk -F" " '{print $1}'),$( basename "$1" | sha512sum | awk -F" " '{print $1}' );
else 
    echo "Unrecognized second argument."; exit 1 ;  
fi;
#echo "hi_"$1
#ls -l "$1"

