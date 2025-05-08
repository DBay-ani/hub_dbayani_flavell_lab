
When running the metadata collection code, stdout and stderr  were separated into different files via piping (i.e. 1> and 2> during runtime).

We only report results here for the hash and metadata collection process that does not follow links (i.e., running [root of code repo]scripts/getMetadataForAllFiles.sh ). 
The result of following links is not reflected here due to extensive runtime, technical issues due to depth of dereferencing,  and likely lack
of utility; the links, if followed anywhere external to what is already reflected in the files already here, would almost certainly just point 
to standard Ubuntu 24.04 LTS features and installed applications with by and large standard configurations. The stderr file here was modified
post-collection only to exclude the absolute path leading to the collection script, which was reported in part of the two timeout-error 
messages shown.
