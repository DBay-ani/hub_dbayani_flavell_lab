
# Comments Related to the Faster Euler:

At a high-level, the method provided here for faster Euler registration uses a feature pyramid approach:
essentially, it starts by aligning highly downsampled versions of the images then uses the match found to 
initialize a search over a a less-down-sampled version of the images that sweeps over a smaller region, repeating this
process until reaching a stopping resolution. Notice the interplay of image resolution and search area: 
the higher the resolution, the smaller the x-y offsets considered are, for instance (smaller with respect 
to the image size, not necessarily smaller with respect to the number of options tried).

Alternative methods examined included, for instance, keypoint-matching (e.g., think of how image stitching
works) and fast-Fourier transform methods (note that ANTSUN already uses some of those - a fact I only came
upon after finding and running related methods separately - but the ones presently adopted in mainline ANTSUN
don't do the full rigid transforms, only a restricted subspace of it). Also, "smart" ways to initialize alignment,
such as with PCA based on high-intensity points (e.g. image-> {(x,y) | intensity(x,y)> threshold} -> PCA)
were also explored. There are techniques inbetween these layers to be aware of as well, like ICP (iterative closest point) and
Procrustes analysis tools, etc., but those are not what we focus on here. For record, no claim is made here 
that more than one of these things can't be used together :) . That all said, we mostly focus on the Pyramid approach here.
More details on some of that other stuff are to come in slides in coming days etc. 
Added m2htw21d98M5y2025tzET: taking a glance at "../subsetOfMoreMaterial_m39htw17d8M5y2025tzET/.gitmodules" can
give you an idea of a subset of what was explored in the meantime.

## Notes on Seeing the Changes So They Can Be Worked Into Other Code Branches

Suppose you're working with the most recent version of the `dev` branch and want to see what the
changes in this branch's notebook are in respect to `dev`. One approach is to do:
```bash
git checkout dev ;
git checkout <name of this branch> ANTSUN.ipynb ;
<invoke nbdiffweb, either directly or via Jupyter-lab extension, and see the diff>
```
The approach in the above code snippet could result in a lot of changes being reported that are
not key to understanding what this current branch provides. In particular, if `dev` and this current
branch have a common ancestor commit, say commit C, the snippet above will not just show what
this branch added to `C`, it will show what `dev` added as well. It may be easier to see one at a time.

To do that, the `merge-base` subcommand of `git` can be handy; often, it gives that common ancestor, C,
that provides a good foundation for comparison. An example use:
```bash
hashOfCurrentHeadCommit=$(git log HEAD -n1 --format=format:%H) &&
baseCommit=$(git merge-base HEAD origin/dev) && echo $baseCommit &&
# output when run at time of writing this: 513b4848ce83a745e9b75086dc4812f4221fff5b
git checkout $baseCommit &&
git checkout $hashOfCurrentHeadCommit ANTSUN.ipynb;
<invoke nbdiffweb, either directly or via Jupyter-lab extension, and see the diff>
```
Taking the approach of the snippet immediately above should show what this branch added, 
compared to the state of the `dev` branch at the time this work separated.   


## Notes on Running the Code Fast

The Euler-registration provided here runs on CPU and is parallelized by multiprocessing
( one could consider multithreading, but (1) the may be some more consideration to pay then
about  Python's global interpreter lock, and (2) of the sources of slowdown or excess consumption
we have to treat, those related to using processes instead of lightweight threads are probably
near the bottom of concern). Using the CPU cores we often have available, could run in a few minutes
and achieve reasonable performance in certain tests I ran.

But --- and this is a point to keep in mind --- since this code now runs on CPU, we have the 
GPU free --- which means we can run DeepReg at the same time as this! In other words, we can have
producer-consumer parallelism between this Euler registration and BrainAlignNet, since at present
most of the relevant alignment jobs can be treated independently (i.e., I can align X_1 and Y_1 by
passing them through Euler registration and BrainAlignNet without having to worry about whether 
X_2 and Y_2 have been registered yet (x_2!=X_1 or Y_2 != Y_1) ). Now why might this be useful
if we already have code that runs in minutes for Euler registration? Suppose one wanted to 
try and improve Euler registration correlation performance (not speed, but alignment quality)
by more rigorously sampling the space; note we might even be able to achieve higher GNCC than
Euler GPU since we can sample at finer-grained values. Searching more options, of course, takes
more time ---- *BUT* if the total time to get all the alignment problems through Euler registration
is no slower than how long BrainAlignNet takes, we can essentially make the runtime of Euler
registration disappear. In particular, in BrainAlignNet runs in its own thread and consumes 
results from EulerRegistration as soon as _any_ are available, then Euler registration just needs
to provide values no slower than BrainAlignNet can eat them. So one can explore more than 
the current parameters of Euler registration implemented here entail and yet not feel much pain.

(Note, m5htw20d8M5y2025: to be blatant in case its lost in technical details, I'm saying that
using CPU for Euler registration is possibly a _good thing_ in this case.)

*We do suggest you also see and implement suggestions at https://github.com/flavell-lab/private_ANTSUN/issues/7 
since those should be easy to do and do have noticeable impact. Really.* It relates to the topic
of image registration because we save out a lot of data --- data that we then go on to reprocess
soon after (e.g., Euler registration feeding into DeepReg) and paying the network IO price
to transfer that content while being sensitive to time-until-result is not sensible. 

In some of the code in ["euler_reg_d22M2y2025tzET/rigidTransformationByScalespacePyramid.py"](#euler_reg_d22M2y2025tzET/rigidTransformationByScalespacePyramid.py), you'll see parts fixing the CPUs used and maximum number of threads, etc (ex: lines 16 to 21, and
370 to 388). That relates to wanting to avoid things moving around unnecessarily and using full resources
on a core but not more than that, where excess has negative effects (note that this relates to how many
things _a single process_ spins up, not the overall amount of resource use); I'm sparing most details on that for now, but 
wanted to acknowledge that as I look over it now and express that I recall it being there by design. The values
that show up in the environment variables being set, like those in likes 16 to 21, have to do with the specific hardware
we have on the servers from my recollection of how I set them. Its been a few weeks since I touched this last.    


### Note at m23htw20d8M5y2025tzET: a Brief Digression on Thread-Based Data-Retrieval Latency Hiding

General comment for broader audience: multithreading also helps with the (disk) IO performance --- 
which can be a major bottleneck. Basically, in typical synchronous and/or single-threaded code, 
a single logical control path issues a read command and waits until the 
content is read from disk (which can be really, really slow, relatively speaking --- and only
worse if over a network, ex, `store1`, `data1`, etc). An alternative using multi-threading is to have
one thread sleep until the result is fetched, but allow others to continue and/or wake up as
content from previous read-requests arrive. This ensures something is always processing, 
instead of having one thread that does work, issues a read request, then
sits around doing nothing until the read returns. 

Technically speaking, be aware there are circumstances where more threads hurt performance ---
thrashing the cache, having more active work than processing power, etc. Those circumstances are beside the
point being gotten-at here. The intention of this sub-sub section is not to say "method X should always be done",
but to let the reader know that, for the problem profile being considered and types of issues that are 
causing us slowdown, one of the benefits of this approach comes from better handling of IO latency, though really
as just a cherry-on-top of the substantial benefits of having multiple CPUs solve problem-instances in parallel, 
and consumer-producer parallelism with DeepReg.



# ANTSUN

Implements the Automatic Neuron Tracking System for Unconstrained Nematodes. This notebook takes as input raw video data from NIR and confocal microscopes and outputs neural traces and behavioral parameters for that worm.

Version 1.3.5 is the version from [this article](https://github.com/flavell-lab/AtanasKim-Cell2023/tree/main#citation).

Version 2.1.0 is the version from [this article](https://doi.org/10.1101/2024.07.18.601886).

## Neural network weights

Most neural network weights should be available in [our Zenodo repository](https://zenodo.org/records/8185377). We've since updated the 3D U-Net segmentation network to include NeuroPAL training data; the updated weights are available [here](https://www.dropbox.com/scl/fo/zn530f0lnw9p8wqssqfwq/h?rlkey=01izs13oa9ef4hdw9ielhaqcx&dl=0).

## `elastix` parameters

Our `elastix` parameters are available in [our registration package](https://github.com/flavell-lab/RegistrationGraph.jl/tree/master/params).


## Citation

To cite this work, please refer to the following papers:

#### Brain-wide representations of behavior spanning multiple timescales and states in C. elegans
**Adam A. Atanas\***, **Jungsoo Kim\***, Ziyu Wang, Eric Bueno, McCoy Becker, Di Kang, 
Jungyeon Park, Talya S. Kramer, Flossie K. Wan, Saba Baskoylu, Ugur Dag,  Elpiniki Kalogeropoulou,
Matthew A. Gomes, Cassi Estrem, Netta Cohen, Vikash K. Mansinghka, Steven W. Flavell

Cell 2023; doi: https://doi.org/10.1016/j.cell.2023.07.035

**\* Equal Contribution**

#### Deep Neural Networks to Register and Annotate the Cells of the *C. elegans* Nervous System
Adam A. Atanas, Alicia Kun-Yang Lu, Jungsoo Kim, Saba Baskoylu, Di Kang, Talya S. Kramer, Eric Bueno, Flossie K. Wan, Steven W. Flavell

bioRxiv 2024; doi: https://doi.org/10.1101/2024.07.18.601886
