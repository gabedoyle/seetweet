#Function to generate a map based on mixture of Gaussians centered at each hit
#Much slower than the KD estimator; use genmapkd() instead
#Note: the Gaussians are unnormalized & sd is not actually the variance.
genmap <- function(df,lats,longs,size,sd) {
	#Defining bin boundaries for map
	rows <- seq(lats[1],lats[2],size)
	cols <- seq(longs[1],longs[2],size)
	
	#Creating a map-like matrix of all zeros
	map <- matrix(0,nrow=length(rows),ncol=length(cols))
	
	#For each bin individually
	for (r in seq(1,length(rows))) {
		print(paste("beginning lat",rows[r]))
		for (c in seq(1,length(cols))) {
			temp <- 0
			#For each hit in the dataframe
			for (dr in seq(1,nrow(df))) {
				#Determine distance from SW bin corner to hit LL
				dist <- sqrt((rows[r]-df$lat[dr])^2+(cols[c]-df$long[dr])^2)
				#Add Gaussian contribution from this hit to the bin
				temp <- temp + exp(-dist/sd)
			}
			#Set map value to the calculated bin score
			map[r,c] <- temp
		}
	}
	return(map)	
}

#Function to generate a map based on 2D Kernel Density Estimation
# uses Venables & Ripley's MASS library & method
# returns a map-like matrix
genmapkd <- function(df,lats,longs,boxsize,band=0) {
	require(MASS)
	#If bandwidth is unspecified, it is estimated from data according to MASS's method
	if(band==0) {
		band <- c(width.SJ(df$long),width.SJ(df$lat))
	}
	bnds <- c(longs[1],longs[2],lats[1],lats[2])	#map boundaries
	xbins <- round((longs[2]-longs[1])/boxsize)	#number of longitude bins
	ybins <- round((lats[2]-lats[1])/boxsize)		#number of latitude bins
	numbins <- c(xbins,ybins)
	kdf <- kde2d(df$long,df$lat,n=numbins,h=band,lims=bnds)	#KDE estimation
	#kdf <- con2tr(kdf)
	return(kdf)
}

#Code to restrict a dataframe to datapoints within a rectangle around the contiguous 48 states
#Should be improved; currently includes some of Northern MX, Southern Canada, Bahamas
#restrictUS now covers this more accurately, but also much more slowly
restrictll <- function(df) {
	return(with(df,subset(df,lat<49.5 & lat>24.5 & long < -66.5 & long > -125)))
}

#
loadusmap <- function(folder='c:/stuff/ucsd/seetweet21/maps',mapname='statesp020') {
	require(rgdal)		#required for readOGR()
	require(ggplot2)		#required for fortify()
	require(plyr)		#required for join()
	usmapfull <- readOGR(dsn=folder,layer=mapname)
	usmap <- usmapfull[usmapfull$ORDER_ADM < 49,]
	usmap <- usmap[usmap$ORDER_ADM > 0,]
	usmap <- usmap[usmap$AREA > 0.2,]
	usmap@data$id <- rownames(usmap@data)
	usmap.points <- fortify(usmap, region="id")
	usmap.df <- join(usmap.points, usmap@data, by="id")
	
	return(usmap.df)
}

loadusmapfull <- function(folder='c:/stuff/ucsd/seetweet21/maps',mapname='statesp020') {
	require(rgdal)		#required for readOGR()
	require(ggplot2)		#required for fortify()
	require(plyr)		#required for join()
	usmapfull <- readOGR(dsn=folder,layer=mapname)
	usmap <- usmapfull[usmapfull$ORDER_ADM < 49,]
	usmap <- usmap[usmap$ORDER_ADM > 0,]
	#usmap <- usmap[usmap$AREA > 0.2,]
	usmap@data$id <- rownames(usmap@data)
	usmap.points <- fortify(usmap, region="id")
	usmap.df <- join(usmap.points, usmap@data, by="id")
	
	return(usmap.df)
}


#Function to load a dataframe from SeeTweet output
loaddf <- function(filename,folder='c:/stuff/ucsd/seetweet21/') {
	datafile <- paste(folder,filename,sep='')
	df <- read.table(datafile, header=T, quote="", sep=",")
	return(df)
}	

#Function to 'clean' the data, removing examples we don't want -- specifically:
#	tweets outside the US lat/long rectangle [restrictll()]
#	tweets excluded by multi-search balancing
#	multiple tweets from same user
cleandf <- function(df,badtweets=NULL) {
	df <- restrictll(df)						#removing non-US tweets
	if(is.null(badtweets)) {
		df <- subset(df,df$incl==1)				#removing tweets excluded by balancing criteria
		badtweets <- df$tid[duplicated(df$uid)]		#listing tweets whose baseline forms should be removed
	} else {
		df <- subset(df,df$incl==1 & df$origincl==1)	#removing tweets that are excluded by balancing criteria
		df <- df[!(df$origtid %in% badtweets),]		#removing tweets whose original tweets is a duplicate
	}		
	df <- df[!duplicated(df$uid),]			#removing multiple tweets from same user
	return(list(df=df,badtweets=badtweets))
}

#Function to join a list of dataframes
joindf <- function(dfl) {
	return(cbind(dfl))
}

#Function to convert KD-estimated test & baseline maps 
# to (unnormalized) conditional probability & confidence maps
# Returns a sparse-structured dataframe
createprobmap <- function(map1,map2,df2,smoothing=.0001) {
	#takes in test & baseline kernel density maps
	require(reshape2)
	require(MASS)
	
	smoothmap <- (map1$z+smoothing)/(map2$z+smoothing)
	rownames(smoothmap) <- map1$x
	colnames(smoothmap) <- map1$y
	smdf <- melt(smoothmap)
	colnames(smdf) <- c("long","lat","cond")
	
	#"Confidence" is the log of the expected number of baseline tweets in a box
	#  given the KDE & total number of found tweets in df2.
	smdf$conf <- sqrt(dim(df2)[1]*con2tr(map2)$z)
	smdf$conf[smdf$conf<0] <- 0 
	#test,base are the kernel density estimates for the test form & baseline
	smdf$test <- con2tr(map1)$z
	smdf$base <- con2tr(map2)$z
	
	smdf$lcond <- log(smdf$cond)

	return(smdf)
}
	
#Function to load CSVs from SeeTweet and perform all necessary calculations to yield maps
loadandmapwithbaseline <- function(testfilename,
						basefilename,
						usmap,
						graphtitle,
						folder='c:/stuff/ucsd/seetweet21/',
						lats=c(23,50),
						longs=c(-125,-66),
						boxsize=.5,
						smoothing=.0001,
						bandwidth=5,
						logplot=F,
						balancedlogplot=F) {
	#NOte: setting bandwidth to 0 causes the KDE to use the mean integrated square error to determine bandwidth
	#		(see p. 182-183 of Venables & Ripley 2002)
	
	#require(ggplot2)
	#require(reshape2)
	#require(MASS)
	
	df1 <- loaddf(testfilename,folder)
	df2 <- loaddf(basefilename,folder)
	
	return(mapwithbaseline(df1,df2,usmap,graphtitle,lats,longs,boxsize,smoothing,bandwidth,logplot,balancedlogplot))
}

#Function creating conditional probability maps from existing dataframes
#	Use this if, for instance, you're combining dataframes
mapwithbaseline <- function(df1,
					df2,
					usmap.df,
					graphtitle,
					#folder='c:/stuff/ucsd/seetweet21/',
					lats=c(23,50),
					longs=c(-125,-66),
					boxsize=.5,
					smoothing=.0001,
					bandwidth=5,
					logplot=F,
					balancedlogplot=F,
					restrictUS=F,
					polymap=NULL,
					dontmap=F) {
	#NOte: setting bandwidth to 0 causes the KDE to use the mean integrated square error to determine bandwidth
	#		(see p. 182-183 of Venables & Ripley 2002)
	
	require(ggplot2)
	require(reshape2)
	require(MASS)
	
	#file1 <- paste(folder,testfilename,sep='')
	#file2 <- paste(folder,basefilename,sep='')
	
	if (restrictUS) {
		print("Restricting to US tweets...")
		df1 <- restrictUS(df1,polymap,FALSE)
		df2 <- restrictUS(df2,polymap,FALSE)
	}
	
	print("Removing excess tweets...")
	cdf1 <- cleandf(df1)
	cdf2 <- cleandf(df2,cdf1$badtweets)
	
	print("Building smoothed test distribution...")
	map1 <- genmapkd(cdf1$df,lats,longs,boxsize,bandwidth)
	print("Building smoothed baseline distribution...")
	map2 <- genmapkd(cdf2$df,lats,longs,boxsize,bandwidth)	

	#Don't have to downweight because the kernel estimates are already pdfs
	print("Creating map...")
	smdf <- createprobmap(map1,map2,cdf2$df,smoothing=smoothing)
	
	if (restrictUS) {
		smdf <- restrictUS(smdf,polymap)
	}
	
	if (dontmap) {
		return(smdf)
	}
	
	if(logplot) {
		q <- ggplot(smdf, aes(long,lat)) + geom_tile(aes(fill=lcond,alpha=conf)) + coord_equal() + scale_fill_gradient(low="#0080FF",high="#FF8000",name="LogProb\nRatio") + scale_alpha(name="Confidence\n(sqrt\ntweets)") + theme(panel.background=element_blank(),axis.ticks=element_blank()) + geom_path(data=usmap.df,aes(long,lat,group=group)) + labs(title=graphtitle,x="Longitude",y="Latitude")
	} else if (balancedlogplot) {
		maxrange <- max(abs(smdf$lcond))
		q <- ggplot(smdf, aes(long,lat)) + geom_tile(aes(fill=lcond,alpha=conf)) + coord_equal() + scale_fill_gradient(low="#0080FF",high="#FF8000",name="LogProb\nRatio",limits=c(-maxrange,maxrange)) + scale_alpha(name="Confidence\n(sqrt\ntweets)") + theme(panel.background=element_blank(),axis.ticks=element_blank()) + geom_path(data=usmap.df,aes(long,lat,group=group)) + labs(title=graphtitle,x="Longitude",y="Latitude") + theme(text=element_text(size=20))	
	} else {
		q <- ggplot(smdf, aes(long,lat)) + geom_tile(aes(fill=cond,alpha=conf)) + coord_equal() + scale_fill_gradient(low="#0080FF",high="#FF8000",name="Prob.\nRatio") + scale_alpha(name="Confidence\n(sqrt\ntweets)") + theme(panel.background=element_blank(),axis.ticks=element_blank()) + geom_path(data=usmap.df,aes(long,lat,group=group)) + labs(title=graphtitle,x="Longitude",y="Latitude")
	}

	return(list(map=q,df=smdf))	
}


#Loading a US map and simplifying it (smooth borders & remove all but the core state polygons)
#No longer seems necessary
loadandsimplifyusmap <- function(folder='c:/stuff/ucsd/seetweet21/maps',mapname='statesp020') {
	require(rgdal)		#required for readOGR()
	require(ggplot2)		#required for fortify()
	require(plyr)		#required for join()
	require(shapefiles)	#required for dp()
	usmapfull <- readOGR(dsn=folder,layer=mapname)
	usmap <- usmapfull[usmapfull$ORDER_ADM < 49,]
	usmap <- usmap[usmap$ORDER_ADM > 0,]
	usmap <- usmap[usmap$AREA > 0.2,]
	
	pp <- slot(usmap, "polygons") # take the polygons
	for (i in seq(1,length(pp))) {
		print(paste("Simplifying polygon",i,"of",length(pp))) 
		cf <- coordinates(slot(pp[[i]], "Polygons")[[1]])
		#print(length(pp[[i]]@Polygons))
		pf <- list(x=cf[,1], y=cf[,2]) # list of coordinates, as dp() needs a list and not a matrix or dataframe...
		cf1 <- dp(pf, 0.05) # simplification, with a bandwith of 0.1 decimal degree
		pp[[i]]@Polygons[[1]]@coords <- cbind(cf1$x,cf1$y)
		pp[[i]]@Polygons <- list(pp[[i]]@Polygons[[1]])
		pp[[i]]@plotOrder <- as.integer(1)
	}
	usmap@polygons <- pp
	
	usmap@data$id <- rownames(usmap@data)
	usmap.points <- fortify(usmap, region="id")
	usmap.df <- join(usmap.points, usmap@data, by="id")
	
	return(usmap.df)
}

#Hosmer-Lemeshow test (binned predictor proportions)
regbin <- function(pred,outs,bins=10) {
	inds <- order(pred)
	perbin <- ceiling(length(pred)/bins)
	pres <- 0
	ores <- 0
	counts <- 0 
	for (bin in seq(1,bins)) {
		pres[bin] <- 0
		ores[bin] <- 0
		counts[bin] <- 0
		count <- 0
		for (p in seq(1,perbin)) {
			curr <- p+(bin-1)*perbin
			if (curr <= length(outs)) {
				pres[bin] <- pres[bin] + pred[inds[curr]]
				ores[bin] <- ores[bin] + outs[inds[curr]]
				count <- count + 1
			}
		}
		pres[bin] <- pres[bin] / count
		ores[bin] <- ores[bin] / count
		counts[bin] <- count
	}
	return(data.frame(pbin=pres,obin=ores,count=counts))
}

#function to match ANAE responses to SeeTweet prediction
compareanae <- function(seetweetres,dfa,boxsize) {
	rdf <- seetweetres$df
	rdf$long <- round(rdf$long/boxsize)*boxsize
	rdf$lat <- round(rdf$lat/boxsize)*boxsize
	
	dfa$blong <- round(dfa$long/boxsize)*boxsize
	dfa$blat <- round(dfa$lat/boxsize)*boxsize
	
	dfa$cond <- 0
	nodata <- 0
	for (r in seq(1,nrow(dfa))) {
		data <- rdf[with(rdf,lat==dfa$blat[r] & long==dfa$blong[r]),]
		if (nrow(data)==0) {
			nodata <- nodata + 1
		} else {
			dfa$lcond[r] <- data$lcond
			dfa$test[r] <- data$test
			dfa$base[r] <- data$base
			dfa$conf[r] <- data$conf
		}
	}
	dfa <- dfa[dfa$response>0,]		#removing respondents with no data
	return(dfa)
}

#running diagnostics for a certain bandwidth
bandtest <- function(bw,dft,dfb,dfanae,usmap.df,boxsize=.2,balancedlogplot=T) {
	lres3 <- mapwithbaseline(dft,dfb,usmap.df,'Needs Done Usage',boxsize=.2,balancedlogplot=T,bandwidth=bw)
	dfa3a <- compareanae(lres3,dfanae,boxsize=.2)
	dfa3a <- dfa3a[dfa3a$response>0,]
	dfa3b <- dfa3a[dfa3a$response!=2,]
	dfa3b$response <- 1-(dfa3b$response-1)/2
	rb3b <- regbin(dfa3b$lcond,dfa3b$response)
	print(paste("Bandwidth",bw))
	print(paste("Corr:",cor(rb3b$pbin,log(rb3b$obin))))			#R2 = .699
	means <- tapply(dfa3a$lcond,dfa3a$response,mean)
	print(tapply(dfa3a$lcond,dfa3a$response,mean))	#-.90,-1.44,-2.14
	print(paste("Diff b/w ANAE levels:",means[1]-means[3]))
}

#hopefully functional try to set the data to zero outside the US
#though need to link it to map making & tweet acceptance.
restrictUS <- function(data,map,remove=T) {
	pts <- SpatialPoints(data[, c('long','lat')], proj4string = map@proj4string)
	pts.over <- over(pts, map)
	rownames(pts.over) <- rownames(data)
	#print(str(pts.over)) # check
	pts.bad <- rownames(pts.over[is.na(pts.over$STATE), ])
	#print(data[pts.bad, ]) # how many do we have
	if (remove) {
		data.good <- data[!(rownames(data) %in% pts.bad), ]
		return(data.good)
	} else {
		data.bad <- (rownames(data) %in% pts.bad)
		data$incl <- ifelse(data$incl==1 & !data.bad,1,0)
		return(data)
	}
}

#removes lake & ocean boundaries from the states in the simplified map usmap.df
removewater <- function(mapdf) {
	return(subset(mapdf,    group!="1293.1" &
				      group!="1321.1" &
					group!="1498.1" &
					group!="1309.1" &
					group!="1716.1" &
					group!="1718.1" &
					group!="1714.1" &
					group!="1522.1" &
					group!="1261.1"))
}
	
#prepare tweets for identification as good tweets
prepincltweets <- function(tweetfile,csvfile,folder) {
	csv <- loaddf(paste(csvfile,".csv",sep=''),folder)
	tweets <- read.csv(paste(tweetfile,".tweets",sep=''),header=T,sep=',',fill=T,quote='')
	incltweets <- csv$tid[csv$incl==1]
	write.csv(tweets[tweets$tid %in% incltweets,],paste(tweetfile,".incltweets",sep=''))
	return
}

#prepare tweets for identification as good tweets
prepincltweetsfromdf <- function(tweetfile,df) {
	#csv <- loaddf(paste(csvfile,".csv",sep=''),folder)
	tweets <- read.csv(paste(tweetfile,".tweets",sep=''),header=T,sep=',',fill=T,quote='')
	incltweets <- df$tid[df$incl==1]
	outtweets <- tweets[tweets$tid %in% incltweets,]
	outtweets <- as.data.frame(lapply(outtweets,factor))
	write.csv(outtweets,paste(tweetfile,".incltweets.csv",sep=''))
	return
}
