# download Stackoverflow PostHistory
wget https://archive.org/download/stackexchange/stackoverflow.com-PostHistory.7z
7z e stackoverflow.com-PostHistory.7z
bzip2 PostHistory.xml

# download Stackoverflow Posts
wget https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z
7z e stackoverflow.com-Posts.7z
bzip2 Posts.xml

# NOTE: you must have already downloaded full_technote_collection.txt.bz2 from https://leaderboard.techqa.us-east.containers.appdomain.cloud/

# generate dataset
python stackexchange_posthistory.py \
--posts Posts.xml.bz2 --posthistory PostHistory.xml.bz2 \
--corpus full_technote_collection.txt.bz2 \
--link_regex "ibm.com/support/[^\\s]*uid=((?:swg|nas|ssg|isg|ibm)[a-zA-Z0-9]+)" \
--outdir stackoverflow-technotes
