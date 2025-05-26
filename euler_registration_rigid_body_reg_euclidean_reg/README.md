# Briefly, On the Name of the Problem

Within the Flavell Lab, Euler registration came to be the term used to refer to attempting
to align two volumes using only rotation and translation, and often also used to refer to 
similar alignment process for simple 2D images. This may be borrowed from other phrasing in
related work, and likely is meant to be a reference to Euler angles, a decomposition of 
movement in three dimensions as a sequence of certain rotations about select axes.

<details>
<summary>A Word on Related Terms and Concepts</summary>
Closely related concepts, at least to solve the component problems as devised
within the lab, are Euclidean registration and more broadly rigid body registration.
For the latter, flips are allowed for consideration when disecting the problem into
2D planes, a transformation we typically explicitly or implicitly; the existing "Euler
registration" process adopted by the lab aligns projections in the XY-plane first, then 
in the XZ-plane, which removes the possibility of a flip in the XY-plane (but allows it,
effectively, in the XZ by a rotation in XY first) perhaps by design since that 
corresponds to a a rotation about the length of the worm which we typically try to control
for through other means.
</details>

# Place to Find Material Related to Euler Registration

## Material Already Provided and Integrated into ANTSUN Notebook

See the branch `dbayani/workingInFasterEulerRegistration/_r` or the repo `git@github.com:flavell-lab/private_ANTSUN`
which  - as of at least May 8th, 2025 - contained material that should prove immediately 
useful in deploying the updated Euler registration into ANTSUN. Note that - as of
at least May 8th, 2025 - the git-hash of the head of the branch mentioned in the preceeding
sentence is `9b9fe55f928c3920fff6b96ffff4bf4ca63db638`. 

A subset of content from that branch are provided in this present repository at
[`./subsetOfMaterialAddedToRepo-private_ANTSUN-byTimeOfCommit-9b9fe55f928c3920fff6b96ffff4bf4ca63db638`](#subsetOfMaterialAddedToRepo-private_ANTSUN-byTimeOfCommit-9b9fe55f928c3920fff6b96ffff4bf4ca63db638). Excluded from the content provided at otherwise could be found at commit `9b9fe55f928c3920fff6b96ffff4bf4ca63db638` of the `flavell-lab/private_ANTSUN` repo are: 
- `ANTSUN.ipynb` (important, since it was modified to incorporate the newer approach, but is best left
private to the lab for the time being)
- The temporary files accidentally committed at `README.md.bak`, `temp`, `temp2`, `temp.bak`, and `subsetOfMoreMaterial_m39htw17d8M5y2025tzET/README.txt.bak`
- The tope-level `.git` directory for the `flavell-lab/private_ANTSUN` repo

Also be aware that I emailed some members of the lab to communicate this, as seen in:
    -----
===========

## Materials on Dropbox

Additional code and methods explored can be found at https://www.dropbox.com/scl/fo/z2b0qgincsh3tm1dnos6k/AKfxdfY1LfMYNThv9_PwWxo?rlkey=4vpz7ytnqinmq97jwelqrp4ir&st=5pgsggli&dl=0

***We highlight the directory [`2020-Computer-Version/file/BenBen`](https://www.dropbox.com/scl/fo/vtiot16tux2afh1uzitjo/AFB2hlnsUiYImZ5QmEcVSUw?rlkey=ik5x4eoc4g5lsrzrrwbsyuwpq&st=ofwfkrn7&dl=0) which has code and results that might otherwise be easy to miss due to the names of the directories they are placed under.*** We would consider moving or renaming, but for sake of sparing confusion with historical record, we leave the structure as-is and simply make explicit this locale.

Instructions for confirming the hashes are at [`../README.md#hasheschecksums-and-metadata-for-content-gathered`](https://github.com/DBay-ani/hub_dbayani_flavell_lab?tab=readme-ov-file#hasheschecksums-and-metadata-for-content-gathered); as discussed, the hashes and metadata provided benefits including integrity checks and ensuring content has not changed passed the claimed date of last modification. Be aware that of the content provided, I have removed a subdirectory called "settingUpDocker", which pretained to setting up Docker both for ANTSUN in general and specific approach/packages for examining improvements to "Euler registration"; I can provide those notes elsewhere for any interested, and even without me doing that, those interested can download the `.git`  folder located there and see the entire collection (heads up: the git repo is about 1.6GB). For those interested in data related to outcomes and testing, the `.dvc` directory and its cache may be of interest (those the data in directly accessible for is also provided on DropBox - the `.dvc` file is more for those who
want to do thorough, non-trivial work with the content on their local machines.  

A list of names of content found in the Dropbox link is provided in the [`./listOfContentOnDropbox_s28m53htw02d26M05y2025tzEDT.txt`](#listOfContentOnDropbox_s28m53htw02d26M05y2025tzEDT.txt).




# References to Subset of Slides Discussing Some Approaches Shown in Material Provided

- for the approach provided in private_ANTSUN branch mentioned above: [meetingWithDrFlavell_d13M3y2025tzET.pdf](https://www.dropbox.com/scl/fi/m2luljwdd2xub35cujo8w/meetingWithDrFlavell_d13M3y2025tzET.pdf?rlkey=48739jzmgybb94trbhcwvzups&st=l1q6uxbk&dl=0)
- on page 16 of [fridayQuantMeeting_d8M11y2024.pdf](https://www.dropbox.com/scl/fi/8qcqzy8gdckql7ffrnu5n/fridayQuantMeeting_d8M11y2024.pdf?rlkey=6o9qrfnx4yh95773qhqheftwi&st=wuhls27x&dl=0)
- on page 13 of [fridayQuantMeeting_d10M1y2025tzET.pdf](https://www.dropbox.com/scl/fi/i5xfd4xtz57v80f6khe9o/fridayQuantMeeting_d10M1y2025tzET.pdf?rlkey=b1yolc7vbyv71demk5kacwnh4&st=iu3f6z6h&dl=0)
- [fridayQuantMeetingSlides_d1M11y2024.pdf](https://www.dropbox.com/scl/fi/kzyzthdjfps74k8gsyz9p/fridayQuantMeetingSlides_d1M11y2024.pdf?rlkey=mpt9q7b70lekcftva1mjai3nu&st=9jbtfph0&dl=0)
- [labMeeting_d21M1y2025tzET.pdf](https://www.dropbox.com/scl/fi/ot2i51qvmd1pu6nyobz2s/labMeeting_d21M1y2025tzET.pdf?rlkey=lho0553s6wmfc0io6xfuqf5wa&st=axwx6tac&dl=0)
- [lides_dbayani_4Oct2024.pdf](https://www.dropbox.com/scl/fi/594mfhdognbjkgsevhhyv/lides_dbayani_4Oct2024.pdf?rlkey=dq3g49cmuvt1doux3dqj7k3mt&st=wanihuuj&dl=0)
- [quantMeeting_d7M3y2025tzET.pdf](https://www.dropbox.com/scl/fi/yx1v25r2ry15l2v23daua/quantMeeting_d7M3y2025tzET.pdf?rlkey=aw3gtd5y2nq6yo9xulcelul9c&st=lk3qy3i5&dl=0)
-[quantMeeting_d14M3y2025tzET.pdf](https://www.dropbox.com/scl/fi/r1x4ewcq88c7luya78nfk/quantMeeting_d14M3y2025tzET.pdf?rlkey=7omwqnarudfdygxlqms4h6vge&st=cf45nphn&dl=0)
- [quantMeeting_d28M2y2025tzET.pdf](https://www.dropbox.com/scl/fi/0uq8sqeijyljew7bzz3m3/quantMeeting_d28M2y2025tzET.pdf?rlkey=5i7u87m1r7hog3irs67nh987p&st=b4ecrebf&dl=0)
- slide 18 of [roundRobin_d10M1y2025tzET.pdf](https://www.dropbox.com/scl/fi/ab5g7g7h7c02ge19b4rep/roundRobin_d10M1y2025tzET.pdf?rlkey=od3rwiskugwjtd356c88wvkjr&st=cwczcx6t&dl=0)
- [roundRobin_d25M2y2025tzET.pdf](https://www.dropbox.com/scl/fi/lm5nd9boguy5omj35xf7o/roundRobin_d25M2y2025tzET.pdf?rlkey=j6wza1l50vwetrqnn2ft4d54o&st=ryxjt4q8&dl=0)
- [slidesForRoundRobin_d5M11y2024.pdf](https://www.dropbox.com/scl/fi/13vo5hh5ush03c42no1q9/slidesForRoundRobin_d5M11y2024.pdf?rlkey=buabzhbc3u5jzqqo5e3e264ex&st=rgiiya4x&dl=0)

# Misc Example, for Fun and Demonstration, of Eye-Candy Found In Materials Pointed-To Here

For quick visual of various things offered, an example PNG of the process for matching based on SIFT etc:
![Example of Outcomes Trying SIFT-Based Keypoint Alignment for Rigid-body Euclidean Registration](https://www.dropbox.com/scl/fi/3djouct7rit0io2xgd1he/vis.png?rlkey=h9u3t1k7vmkgus576rdymggqj&st=4pqzbjoo&raw=1)
