seetweet
========

This is the initial version of SeeTweet, a suite of Python and R scripts for mapping the geographic distribution of tweets within the U.S. for a given search term.

The present version is likely user-unfriendly, as it has so far only been used by me. The release version will be posted ahead of the EACL 2014 conference, at which the SeeTweet paper will be presented.  Versions prior to mid-April 2014 are essentially beta tests while I work on creating a version that works for people who aren't me.

Components
==========

SeeTweet has a Python side and an R side; tweets are obtained by the Python code seetweetVVV.py (VVV being the current version number) and mapped by the R code seetweetfnsVVV.R.  Samples of R code for various projects is included.

This also requires the "twitter" modeule by Mike Verdone, available at https://pypi.python.org/pypi/twitter (tested using v.1.14.2)

Getting Tweets
==============

python -u seetweet220.py QUERY    -f=QUERY.DATE.csv    >QUERY.DATE.out

This call searches for QUERY through Twitter's API (using Mike Verdone's Python Twitter Tools), and saves details of the tweets to the CSV given by the -f tag. SeeTweet also displays the tweets as they are produced, so I recommend piping the output into a file.  Note that QUERY must not contain spaces (use '+' instead) and that quotation marks must be escaped (use '\"' instead).

**Warning:** the output file is UTF-8 encoded. If you encounter a UnicodeEncodeError, run " export PYTHONIOENCODING=utf-8 " before calling seetweet

python -u seetweet220.py BASE -t=100 -c=QUERY.DATE.csv     >QUERY.DATE.base.out

This call generates a baseline distribution for the Tweets found by the previous search (recorded in the filename specified by the -c tag). BASE should be a geographically-constant baseline search term (e.g., "I", "the"), as discussed in the EACL paper.

**Important question you might ask:** "The code started hanging after like 5 minutes, what the hell?"  Yeah, sorry about that.  Twitter has strict rate limits on the number of searches you can do per time period. Most SeeTweet searches are going to run afoul of that.  SeeTweet automatically monitors the rate limit and pauses searching when it's about to hit it.  At present, this means it pauses approximately every 150 searches until the limit window resets.  However, it automatically restarts searching, so you can go do something else and let it do its thing.

Note this also means that you should *not* run multiple copies of SeeTweet simultaneously.  Please wait for one to finish before starting the next.

Mapping Tweets
==============

Mapping is performed by the R portion of the code. Description of this code to come.
