Content here reflects hashes and metadata for exported copies of various content from Slack using https://github.com/rusq/slackdump on more than one date.

After getting the Slack data, the commands used to form the hash files here were as follows:
sudo [path to script]/getMetadataForAllFiles.sh . > ../stdout_linksFollowed_slack_s03m04htw04d07M05y2025tzEDT.csv 2> ../stderr_linksFollowed_slack_s03m04htw04d07M05y2025tzEDT.txt
sudo [path to script]/noFollowingLinks_getMetadataForAllFiles.sh . > ../stdout_nolinkFollowing_slack_s03m04htw04d07M05y2025tzEDT.csv 2> ../stderr_nolinkFollowing_slack_s03m04htw04d07M05y2025tzEDT.txt

In addition to the hashes and metadata, a list of the files and directories were also gathered, using the following command, which was run in the directory holding the Slack content.
find . > ../stdout_slack_find_noLinkFollowing_$(db_date_format ).txt 2> ../stderr_slack_find_noLinkFollowing_$(db_date_format ).txt 
find -L . > ../stdout_slack_find_linkFollowing_$(db_date_format ).txt 2> ../stderr_slack_find_linkFollowing_$(db_date_format ).txt 
We do not provide those files here, but their sha512 hashes were as follows:
cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e  stderr_slack_find_linkFollowing_s24m29htw14d07M05y2025tzEDT.txt
cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e  stderr_slack_find_noLinkFollowing_s38m26htw14d07M05y2025tzEDT.txt
826a49bdab98ef1c372c3d2ac31aeedca991eef1cf8780937a0bdd14aa31fcae9cc57b760e867cfe2c42b3db8ff00210f172acaded7268ab79af76875970cac7  stdout_slack_find_linkFollowing_s24m29htw14d07M05y2025tzEDT.txt
826a49bdab98ef1c372c3d2ac31aeedca991eef1cf8780937a0bdd14aa31fcae9cc57b760e867cfe2c42b3db8ff00210f172acaded7268ab79af76875970cac7  stdout_slack_find_noLinkFollowing_s38m26htw14d07M05y2025tzEDT.txt


