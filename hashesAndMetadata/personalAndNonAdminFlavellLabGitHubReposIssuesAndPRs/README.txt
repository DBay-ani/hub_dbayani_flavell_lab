The metadata reported here include content available to standard members of the Flavell Lab on GitHub,
as well as from several repositories on my personal account containing material I personally developed
during my time at the Flavell lab. The content that was solely in my hands (e.g., on my account) was
easily git-cloned manually for the hash-and-metadata computation process, and additionally is was confirmed
manually that they did not have GitHub issues or GitHub PRs to report here (I was the only one involved on them,
so that is as expected). For reflecting the Flavell-Lab repositories that I contributed to - and in many cases, 
actually started - the process was more involved and is shown below. *Note that not all Git repositories I
contributed to during my time with the Flavell Lab are reflected here*; certain repositories that were considered
sensitive (i.e., for administration) I separated from at a point prior to the gathering-process shown in the
rest of this file.


How content for the flavell-lab GitHub was gathered, using the GitHub CLI interface (https://cli.github.com/):


# grabbing the flavell lab repos accessible to me (not admin ones at this point):
for thisRepo in $(gh repo list flavell-lab -L 200  --json "name" | json_pp | grep ":" | awk -F"(name\" *: * \")|(\"$)" '{print $2}' ); do gh repo clone "flavell-lab/"$thisRepo ; done

# getting list of URLs for issues and PRs; note that we can manually confirm that the set of pertinent values per repo is no greater than 1000:
for thisRepo in $(ls -1 ); do gh search issues -R "flavell-lab/"$thisRepo -L 1000 --json "url"; sleep 2; gh search prs -R "flavell-lab/"$thisRepo -L 1000 --json "url"; sleep 2; done 1> ../flavellLab_stdout_urls 2> ../flavellLab_stderr_urls

# gathering the PRs and issues:

cp ../flavellLab_stdout_urls temp_urlsFound ; 
vi  temp_urlsFound  -c '0 | s/{"url":"\([^"]*\)"/\r\1\r/g1000000 | wq' ; 
for thisURL in $(cat temp_urlsFound | grep -i http ); 
do 
basenameForFiles=$( echo $thisURL | awk -F"/" '{for(x=4;x<=NF; x++){printf $x"_" ;} print ""; }');
gh pr view  $thisURL >  "1_"$basenameForFiles".md5"; 
sleep 0.5;  
gh pr view --comments  $thisURL >  "2_"$basenameForFiles".md5"; 
sleep 0.5; 
gh pr view --comments  $thisURL  --json "additions,assignees,author,autoMergeRequest,baseRefName,baseRefOid,body,changedFiles,closed,closedAt,closingIssuesReferences,comments,commits,createdAt,deletions,files,fullDatabaseId,headRefName,headRefOid,headRepository,headRepositoryOwner,id,isCrossRepository,isDraft,labels,latestReviews,maintainerCanModify,mergeCommit,mergeStateStatus,mergeable,mergedAt,mergedBy,milestone,number,potentialMergeCommit,projectCards,projectItems,reactionGroups,reviewDecision,reviewRequests,reviews,state,statusCheckRollup,title,updatedAt,url" >  "3_"$basenameForFiles".json";
sleep 0.5;  
gh pr view $thisURL  --json "additions,assignees,author,autoMergeRequest,baseRefName,baseRefOid,body,changedFiles,closed,closedAt,closingIssuesReferences,comments,commits,createdAt,deletions,files,fullDatabaseId,headRefName,headRefOid,headRepository,headRepositoryOwner,id,isCrossRepository,isDraft,labels,latestReviews,maintainerCanModify,mergeCommit,mergeStateStatus,mergeable,mergedAt,mergedBy,milestone,number,potentialMergeCommit,projectCards,projectItems,reactionGroups,reviewDecision,reviewRequests,reviews,state,statusCheckRollup,title,updatedAt,url" >  "4_"$basenameForFiles".json";
sleep 0.5;  
gh issue view  $thisURL >  "1_"$basenameForFiles".md5"; 
sleep 0.5;  
gh issue view --comments  $thisURL >  "2_"$basenameForFiles".md5"; 
sleep 0.5; 
gh issue view --comments  $thisURL  --json "assignees,author,body,closed,closedAt,comments,createdAt,id,isPinned,labels,milestone,number,projectCards,projectItems,reactionGroups,state,stateReason,title,updatedAt,url" >  "3_"$basenameForFiles".json";
sleep 0.5;  
gh issue view $thisURL  --json "assignees,author,body,closed,closedAt,comments,createdAt,id,isPinned,labels,milestone,number,projectCards,projectItems,reactionGroups,state,stateReason,title,updatedAt,url"  >  "4_"$basenameForFiles".json";
sleep 0.5;  
done 2> stderrWhileCollectingIssuesAndPRs_m52htw14d5M5y2025tzET.txt


# collecting the hashes and metadata
[absolute path to file]/noFollowingLinks_getMetadataForAllFiles.sh . 1> ../gitHubHashes_linksNotFollowed_$(db_date_format).csv 2> ../stderr_gitHubHashes_linksNotFollowed_$(db_date_format).csv
[absolute path to file]/getMetadataForAllFiles.sh . 1> ../gitHubHashes_linksFollowed_$(db_date_format).csv 2> ../stderr_gitHubHashes_linksFollowed_$(db_date_format).csv



