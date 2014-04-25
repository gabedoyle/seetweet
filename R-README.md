This file discusses the major R functions in seetweetfnsVVV.R used in analyzing the data from the Python scripts.

mapwithbaseline
===============
The main function, takes in two dataframes of tweets: the query tweets and the baseline tweets.
* restricts to US-based tweets
* builds kernel density estimates of tweet likelihood
* divides query map by baseline map to generate unnormalized ratio map
* returns ggplot of the map

loadandmapwithbaseline
===============
Performs mapwithbaseline() but loads tweet dataframes directly from CSV files

loaddf
===============
loads a csv of tweets into a dataframe

cleandf
===============
removes:
* duplicate tweets
* multiple tweets from same user
* tweets excluded by multi-search balancing

joindf
===============
Wrapper for cbind([df,df,df,...]) because I couldn't remember wheter to do rbind() or cbind() the first couple times.

createprobmap
===============
Code to divide query by baseline to generate unnromalized ratio map of usage

restrictUS
===============
Code to remove or mark as not included (df$incl=0) all datapoints outside contiguous US

prepincltweets
===============
Code to print out a csv of tweets with the text of each tweet included
This is used for manually checking tweets and removing those that do not fit the search criteria
