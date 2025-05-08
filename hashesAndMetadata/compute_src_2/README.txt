
The initial scripts collected were generated with code matching (when run in the proper directory):
sudo [path to script]/getMetadataForAllFiles.sh . &> linksFollowed_m45htw3d22M4y2025tzET.csv
sudo [path to script]/noFollowingLinks_getMetadataForAllFiles.sh .  &> noLinkFollowing_m14htw18d22M4y2025tzET.csv
Notice these commands placed stdout and stderr into the same files, which went on to be a point requiring clean-up.
The files had to sanitized post-collection due to issue with certain names not being sanitized before being passed 
to the `basename` utility.
See `sanitizeOutBasenameErrorInHashesAndMetadata.py` . Prior to sanitization, the hashes for the two files were as follows:
b0d1ffe11f7f87d270097de60cbc7c5eb64cbdd3e850fa72443114c6cfdadb84e929b8875cabdf6f036bdbaee861702363dce201c460390b61fd21f5f3846cde  linksFollowed_m45htw3d22M4y2025tzET.csv
feb720a48aca5def04168b92a4368c32b57bd7eac1889062a98cdb59a6a7acb5397f5dccbabb18fca6f49d95e7eef7451deb8db3f10041cf61eca615a23ff821  noLinkFollowing_m14htw18d22M4y2025tzET.csv

Commands used to do the sanitization:
echo $(pwd)"/noLinkFollowing_m14htw18d22M4y2025tzET.csv" |  [path to script]/sanitizeOutBasenameErrorInHashesAndMetadata.py  > postSanitization_noLinkFollowing_m14htw18d22M4y2025tzET.csv
echo $(pwd)"/linksFollowed_m45htw3d22M4y2025tzET.csv" |  [path to script]/sanitizeOutBasenameErrorInHashesAndMetadata.py  > postSanitization_linksFollowed_m45htw3d22M4y2025tzET.csv

Post sanitization hashes of files (sha512sum postSanitization_*):
01b58e8c6203016507bf6d54530e37f8c70c6e267dc8236f5f7e8a463fdc5f7e6622de2691a97c9187e7c76e47e55794099fc86215196c4df89a001685618d77  postSanitization_linksFollowed_m45htw3d22M4y2025tzET.csv
539002e17a3893d3c8fc292619ae3c8e89c23580c7ff3d34202e7d2bbc61c22f2fe620dc1e3f330e348d2d6b02ce0bbc84c0b594a0f5fed924e0c42bb41e61a7  postSanitization_noLinkFollowing_m14htw18d22M4y2025tzET.csv 

The results of running the `find` command - both with and without link following - were also collected at m16htw18d22M4y2025tzET and saved in files. The sha512 hashes of the files
703558b5c8f3cd7e7e6516e86622a2976b95c6a96e89a8473eaeb09f19027a13757d3931317b744a06c74d4ce0c60b5890d7aa0ed241585ba63f1313dc295bb3  the file following links
4f9356c5dad5ec22c27f7e0391d86582f113196719342307559c8f233a3a4350367aa98d3cf295d6e19eb928aa0fd0e3048a903a73c33d0c7880a6ef58934158  the file not following links

