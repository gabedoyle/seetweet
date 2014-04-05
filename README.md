seetweet
========

This is the initial version of SeeTweet, a suite of Python and R scripts for mapping the geographic distribution of tweets within the U.S. for a given search term.

The present version is likely user-unfriendly, as it has so far only been used by me. The release version will be posted ahead of the EACL 2014 conference, at which the SeeTweet paper will be presented.  Versions prior to mid-April 2014 are essentially beta tests while I work on creating a version that works for people who aren't me.

Components
==========

SeeTweet has a Python side and an R side; tweets are obtained by the Python code seetweetVVV.py (VVV being the current version number) and mapped by the R code seetweetfnsVVV.R.  Samples of R code for various projects is included.

Getting Tweets
==============

python seetweet219.py QUERY    -f=QUERY.DATE.csv    >QUERY.DATE.out

This call searches for QUERY through Twitter's API (using Mike Verdone's Python Twitter Tools), and saves details of the tweets to the CSV given by the -f tag. SeeTweet also displays the tweets as they are produced, so I recommend piping the output into a file.  Note that QUERY must not contain spaces (use '+' instead) and that quotation marks must be escaped (use '\"' instead).

**Warning: the output file is UTF-8 encoded. If you encounter a UnicodeEncodeError, run " export PYTHONIOENCODING=utf-8 " before calling seetweet

python seetweet219.py BASE -t=100 -o -c=QUERY.DATE.csv     >QUERY.DATE.base.out

This call generates a baseline distribution for the Tweets found by the previous search (recorded in the filename specified by the -c tag). BASE should be a geographically-constant baseline search term (e.g., "I", "the"), as discussed in the EACL paper.

Mapping Tweets
==============

Mapping is performed by the R portion of the code. Description of this code to come.
