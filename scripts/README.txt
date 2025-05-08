This directory contains scripts used to produce the cryptographic hashes and metadata present in this repository. These pieces of code are largely base
on content at https://github.com/DBay-ani/information_preservation_and_backup_notes_and_info/tree/master/scriptsForCollectingFileMetadata ,
and one is encouraged to visit this URL to get the main gist of what is computed. That said, there are several modifications and additions
present here as compared to the other repository that are worth underscoring:
(1) there is an additional script called "noFollowingLinks_getMetadataForAllFiles.sh" that differs from "getMetadataForAllFiles.sh"  
in that links (e.g., softlinks, hardlinks) are presented as-is in the hashes collected instead of being dereferenced and having content
reachable from that dereferencing be reported.
(2) while file names, in what has been collected using these scripts so far, have not been reported, code to gathered a cryptographic 
hash of the file name and file path have been included. Since file names and paths are often indicative of what the content pertains
to, adding this information could potentially provide information about what content was used for / as part of (to a degree - reuse of code via program-internal linking would not be reflected, but the point is that further confirmation could be available).
(3) while the implementation of the name hashing in (2) worked as hoped for the most part, there were times that content with certain
pathological names caused issues with the `basename` utility used in the implementation. To address this - in particular to reduce the
chances of unintentionally leaking parts of names raw - a sanitization script was written to clean out error messages that revealed parts
of names, record that such a thing occurred during the generation of a particular record, and to ensure the content continues to be formatted
more-or-less as envisioned (ex, one record per line, with relative ease of machine-parsing, etc.). An examples of where this comes up can 
be see in `../hashesAndMetadata/compute_src_2/README.txt` 

