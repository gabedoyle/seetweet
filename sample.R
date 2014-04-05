###################################################
# call this part at the beginning of each session #
###################################################

library(rgdal)
library(plyr)
library(ggplot2)
library(reshape2)
library(MASS)
library(grid)

#Customize the folder that your .csv file from the Python scripts live in
#NOTE: make sure folders end with slash
folder <- 'c:/whatever/address/'                                         #base folder (if not R's current working directory)
resfolder <- paste(folder,'subfolder/subsubfolder/',sep='')              #folder you want results to go into
source(paste(folder,'seetweetfns220.R',sep=''))                          #update with the current version of seetweetfns
load(paste(folder,'usmap.RData',sep=''))                                 #load a map of the US

#Removing small islands
usmap.df <- subset(usmap.df, group!="1293.1" & group!="1321.1" & group!="1498.1" & group!="1309.1" & group!="1716.1" & group!="1718.1" & group!="1714.1" & group!="1522.1" & group!="1261.1")
usmap <- usmap[setdiff(1:59,c(2,7,8,10,16,18,25,27,28)),]

#########################################
# sample: mapping "y'all"
#########################################

#Optional subfolder that the CSV files live in
projfolder1 <- 'sample/'
projfolder2 <- 'sample/'

filename1 <- "yall.ml131013"
filename2 <- "yall.ml131014"

#Loading the test (y'all-containing) and baseline tweets
testfilename1 <- paste(filename1,".csv",sep='')
basefilename1 <- paste("base.i.",filename1,".csv",sep='')
dft1 <- loaddf(testfilename1,paste(folder,projfolder1,sep=''))
dfb1 <- loaddf(basefilename1,paste(folder,projfolder1,sep=''))

testfilename2 <- paste(filename2,".csv",sep='')
basefilename2 <- paste("base.i.",filename2,".csv",sep='')
dft2 <- loaddf(testfilename2,paste(folder,projfolder2,sep=''))
dfb2 <- loaddf(basefilename2,paste(folder,projfolder2,sep=''))

dft <- rbind(dft1,dft2)
dfb <- rbind(dfb1,dfb2)

#Setting box size and bandwidth (in degrees lat/long) for the map
bs <- .2
bw <- 3
lres <- mapwithbaseline(dft,dfb,usmap.df,'Y\'all',boxsize=bs,balancedlogplot=T,bandwidth=bw,restrictUS=T,polymap=usmap)	#plotting the map in ggplot

#Saving the map as a PDF
pdf(file=paste(resfolder,'yall-131113.pdf',sep=''),width=14.22,height=6.88)
lres$map + scale_alpha(name="Confidence\n(sqrt tweets)",limits=c(0,5),labels=c('0','1','2','3','4','5+'))
dev.off()

#Plotting positive/baseline hits without converting to a density estimate
dfti <- subset(dft,dft$incl==1)
ggplot(dfti, aes(long,lat)) + geom_jitter(color="orange") + coord_equal() + theme(panel.background=element_blank(),axis.ticks=element_blank()) + geom_path(data=usmap.df,aes(long,lat,group=group)) + labs(title="Hits for y'all",x="Longitude",y="Latitude") + theme(text=element_text(size=20)) + ylim(c(25,49.2))

dfbi <- subset(dfb,dfb$incl==1 & dfb$origincl==1)
ggplot(dfbi, aes(long,lat)) + geom_jitter(color="blue") + coord_equal() + theme(panel.background=element_blank(),axis.ticks=element_blank()) + geom_path(data=usmap.df,aes(long,lat,group=group)) + labs(title="Pseudo-absences",x="Longitude",y="Latitude") + theme(text=element_text(size=20)) + ylim(c(25,49.2))   + xlim(c(-125,-64))
