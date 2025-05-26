Following a request in email, I'm providing some more material I have on hand, some in relation to evaluation.
I have to dig through more for anything more recent, so some caveats that there might be more that better reflects
improvements; you should take the performance measures here as lower-bounds _on their respective components_; more about that
"component" (versus whole-pipeline) aspect in a moment. The names of the files in this directory, with the exception of this
README, come straight from what I had; I have not renamed anything.

In regard to what is included here: looking through, most performance measures included here seem to be spit-out from running 
ANTSUNCompatible_eulerRegByFeaturePyramid.py, which is an older script and was used in getting together 
../euler_reg_d22M2y2025tzET/rigidTransformationByScalespacePyramid.py
That noted, we suggest running `grep -ir "Done computing Euclidean registration"` to see some of the output.
Also, while it might be a bit deprecated (no updated as much with the code surrounding it in the file), the function
"run_test" in "../euler_reg_d22M2y2025tzET/rigidTransformationByScalespacePyramid.py" might be nice to know about.
It is possible that "old.txt" is from running the Euler registration currently is use in the `main` branch: "old" in the 
file name indicating it is not the "new" stuff provided in this branch, while "current" within the  file referring to
it being the "currently used [in the mainline code]" approach; it may be the case, but I'm not attesting to that
or its preciseness.

Worth noting, while it's a bit older, the code in "compareResults.py" included in this folder may be good to keep in mind; at 
one point while comparing methods, I had some concerns that scores being reported in different places might not be comparable
(e.g., some reporting the square-root of a score, others not), so for a layer of assurance, "compareResults.py" was written to 
load-in the transformed results --- which are the things we care about at the end of the day --- and compute alignment
measures on those directly. By the way, be careful interpreting GNCC scores directly, among other things it is not
necessarily linearly calibrated with intuitions about how-far-different certain alignments are (this ties in to some
points made down below in (1) as well). Randomized spot-checks and visualizations are smart to do.

Bear in mind that the new code uses multiple processes to run; the results shared in this
directory  seem to report per-process and even per-problem outcomes --- part of the idea being to not just look at
cumulative scores like a mean or median, but also look at performance point-wise versus the current 
main-line methods, similar to other collections of reports I've provided in the past (sharing the PDFs 
of those past showing forthcoming). That is, one can imagine a scatter plot of method-A versus method-B and
see where points lay on either side of the x=y line.

*The following is important and should be taken to heart as an aspect of consideration:* 
The main thing we care about is _not_ how well "Euler registration" does on its own, but how good the final alignment
does, not just post-DeepReg registration, but also post-graph-base-clustering. 
To give some examples of why this is an important point to consider:
(1) It may well be that method A versus method B achieves marginally better GNCC on the Euler registration based on
some cumulative score... while also providing *no* robust change in the final DeepReg performance. And bear in mind that, given the 
graph-informed alignment, it could well be that, for aligning a frame F_1, method B produces one high-quality
alignment for F_1 to other frames that is far better than any that method A does, while method A might, for the rest 
of the F_1-related alignments, might do marginally better - with an end result being that method B's high-quality
match overall achieves better performance than method A's slightly-better-most-of-the-time gains.
    (1.1) further, just because method A and method B have different profiles of GNCC performance, it does not
    necessarily entail substantial changes downstream. This is the case even if, technically speaking, one
    strictly dominates another (more probable is that reasonable approaches have a mix of successes and
    losses compared to alternatives, not strict dominance). Is a lack of change likely? Perhaps not, but 
    definitely worth checking especially in cases of non-strict-dominance and if we care about additional 
    factors (e.g., runtime).
(2) Since "Euler registration" is only part of the pipeline, even if we strictly improve its performance, it could
introduce systematic changes that cause downstream components  --- like the DNN-base DeepReg --- to behave 
in undesired ways. That is, while we'd hope it is not the case, producing off-manifold behavior is possible, and
should be checked for. For instance, one could imagine that BrainAlignNet (DeepReg) was trained on data from an 
Euler-alignment method that 80% of the time positioned the moving-frame X units too far right compared
to a globally optimal location- it's conceivable that DeepReg could learn, as part of its training, a transform that
skews toward moving content left in order to compensate. You might imagine the outcome if we provide a "perfect"
Euler-registration method that always gives the truly optimal rigid transform without then changing how 
DeepReg handles it.

To be clear, I am not preaching against analysis of component behavior --- if nothing else, it helps narrow our candidates
for further consideration. It is not, however, where analysis and checks should end.


Regarding my evaluation: like I said, I need to look to see where more of the evaluating-Euler-registration-on-its-own
results got placed. That all aside, I was trying to do the important step of seeing downstream behavior last I was
running this stuff. Unfortunately, that moments when I had time for it, the GPUs were filled to the brim on the machines
I had set things up on. When the clogging subsided a bit, I had some big fires I needed to address that drew efforts away.



