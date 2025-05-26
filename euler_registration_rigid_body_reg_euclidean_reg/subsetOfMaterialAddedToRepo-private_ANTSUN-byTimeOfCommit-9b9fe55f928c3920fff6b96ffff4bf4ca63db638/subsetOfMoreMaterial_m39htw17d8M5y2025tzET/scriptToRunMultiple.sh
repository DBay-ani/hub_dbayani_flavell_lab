#!/bin/bash

date;

placeToWrite="out_exploringFeaturePyramid_"$(date +s%Sm%Mhtw%Hd%dM%my%Ytz%Z)".txt";
k=128;
for((x=0;x<$k;x++)); 
do
export MKL_NUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
export OMP_NUM_THREADS=2
	( 	echo $k,$x | time python3  exploringFeaturePyramid.py  >> $placeToWrite )& 
done
date;
