#!/usr/bin/python
# -*- encoding: utf-8 -*-

#SeeTweet 2.1.9 adds tweet date/time to the output, with individual columns for day,date,month,year,hour (24),min,sec
#   times are based on UTC unless Twitter changes this at some point
#	2.1.9b: corrected location of Grand Rapids, MI & set up to correct other mislocations
#NOTE THOUGH: I have not had time to properly debug these debuggings. They appear to work but must be checked before v. 2.2

versionnum = '2.1.9b'

import sys
import re
import os
from time import localtime,strftime,sleep,time

#Add the Python twitter module
#Twitter package from http://pypi.python.org/pypi/twitter, under MIT License
#by Mike Verdone, http://mike.verdone.ca/twitter
sys.path.append('./twitter-1.10.0/build/lib.linux-x86_64-2.7')
from twitter import *

re.I	#ignore case in all regexp searches
re.U	#perform regexp searches in UTF-8

#Function to manually replace lat/long for city,state combos that the USGS National File gets "wrong"
#i.e., ones where the last entry with that city,state combo is clearly not the intended one
def replacecitystate(d):
	d['mi']['grand rapids'] = [42.9633599,-85.6680863]
	return d


#Function replaces full versions of states with their postal codes for USGS locator matching
#Note: may want to extend this with other abbreviations for the states
def replacestates(text):
	text = re.sub('ala(bama)?\Z','al',text)
	text = re.sub('alaska\Z','ak',text)
	text = re.sub('ariz(ona)?\Z','az',text)
	text = re.sub('ark(ansas)?\Z','ar',text)
	text = re.sub('cal(i(f(ornia)?)?)?\Z','ca',text)
	text = re.sub('colorado\Z','co',text)
	text = re.sub('conn(ecticut)?\Z','ct',text)
	text = re.sub('del(aware)?\Z','de',text)
	text = re.sub('district of columbia\Z','dc',text)	
	text = re.sub('florida\Z','fl',text)
	text = re.sub('georgia\Z','ga',text)
	text = re.sub('hawaii\Z','hi',text)
	text = re.sub('idaho\Z','id',text)
	text = re.sub('ill(inois)?\Z','il',text)
	text = re.sub('ind(iana)?\Z','in',text)
	text = re.sub('iowa\Z','ia',text)
	text = re.sub('kan(s(as)?)?\Z','ks',text)
	text = re.sub('ken(tucky)?\Z','ky',text)
	text = re.sub('louisiana\Z','la',text)
	text = re.sub('maine\Z','me',text)
	text = re.sub('maryland\Z','md',text)
	text = re.sub('mass(achusetts)?\Z','ma',text)
	text = re.sub('mich(igan)?\Z','mi',text)
	text = re.sub('minn(esota)?\Z','mn',text)
	text = re.sub('miss(issippi)?\Z','ms',text)
	text = re.sub('missouri\Z','mo',text)
	text = re.sub('mont(ana)?\Z','mt',text)
	text = re.sub('neb(raska)?\Z','ne',text)
	text = re.sub('nev(ada)?\Z','nv',text)
	text = re.sub('new hampshire\Z','nh',text)
	text = re.sub('new jersey\Z','nj',text)
	text = re.sub('new mexico\Z','nm',text)
	text = re.sub('new york\Z','ny',text)
	text = re.sub('n(orth)? car(olina)?\Z','nc',text)
	text = re.sub('n(orth)? dak(ota)?\Z','nd',text)
	text = re.sub('ohio\Z','oh',text)
	text = re.sub('okla(homa)?\Z','ok',text)
	text = re.sub('oregon\Z','or',text)
	text = re.sub('penn(sylvania)?\Z','pa',text)
	text = re.sub('rhode island\Z','ri',text)
	text = re.sub('s(outh)? car(olina)?\Z','sc',text)
	text = re.sub('s(outh)? dak(ota)?\Z','sd',text)
	text = re.sub('tenn(essee)?\Z','tn',text)
	text = re.sub('tex(as)?\Z','tx',text)
	text = re.sub('utah\Z','ut',text)
	text = re.sub('vermont\Z','vt',text)
	text = re.sub('wash(ington)?\Z','wa',text)
	text = re.sub('west virginia\Z','wv',text)
	text = re.sub('virginia\Z','va',text)
	text = re.sub('wisc(onsin)?\Z','wi',text)
	text = re.sub('wyo(ming)?\Z','wy',text)
	return text

knowncities = [['(cincinnati|cincy)\\b',39.13,-84.5],
	['(fort|ft) wayne\\b',41.08,-85.14],
	['(fort|ft) worth\\b',32.76,-97.33],
	['(long beach|lbc)\\b',33.8,-118.16],
	['(los angeles|lax|la\Z|l a\Z)\\b',34.05,-118.25],
	['(minneapolis|st paul|twin cities)\\b',44.95,-93.2],
	['(new orleans|nawlins)\\b',29.97,-90.05],
	['(nyc|new york city)\\b',40.72,-74],
	['(oklahoma city|okc)\\b',35.48,-97.54],
	['(philly|philadelphia)\\b',39.95,-75.17],
	['(salt lake city|slc)\\b',40.75,-111.88],
	['(st|saint) louis\\b',38.63,-90.2],
	['(st|saint) pete(rsburg)?\\b',27.78,-82.67],
	['akron\\b',41.07,-81.52],
	['albuquerque\\b',35.11,-106.61],
	['anaheim\\b',33.84,-117.89],
	['atl(anta)?\\b',33.75,-84.39],
	['austin\\b',30.25,-97.75],
	['bakersfield\\b',35.37,-119.02],
	['baltimore\\b',39.28,-76.62],
	['baton rouge\\b',30.45,-91.14],
	['boise\\b',43.61,-116.24],
	['boston\\b',42.35,-71.06],
	['bridgeport\\b',41.19,-73.2],
	['brooklyn\\b',40.69,-73.99],
	['buffalo\\b',42.9,-78.85],
	['chandler\\b',33.3,-111.84],
	['(charlotte|clt)\\b',35.23,-80.84],
	['chicago\\b',41.88,-87.62],
	['cleveland\\b',41.48,-81.67],
	['colorado springs\\b',38.86,-104.79],
	['corpus christi\\b',27.74,-97.4],
	['dallas\\b',32.78,-96.8],
	['dfw\\b',32.77,-97.07],		#midpoint between Dallas & Ft Worth
	['dayton\\b',39.76,-84.19],
	['denver\\b',39.74,-104.98],
	['detroit\\b',42.33,-83.05],
	['durham\\b',35.99,-78.91],
	['el paso\\b',31.79,-106.42],
	['fremont\\b',37.55,-121.99],
	['fresno\\b',36.74,-119.77],
	['garland\\b',32.9,-96.64],
	['grand rapids\\b',42.96,-85.66],
	['greensboro\\b',36.08,-79.82],
	['harrisburg\\b',40.27,-76.88],
	['hartford\\b',41.76,-72.67],
	['henderson\\b',36.03,-115.03],
	['hialeah\\b',25.86,-80.29],
	['honolulu\\b',21.31,-157.83],
	['houston\\b',29.76,-95.38],
	['indianapolis\\b',39.79,-86.14],
	['iowa city\\b',41.65,-91.53],
	['irvine\\b',33.68,-117.79],
	['irving\\b',32.81,-96.95],
	['jacksonville\\b',30.32,-81.66],
	['kansas city\\b',39.1,-94.58],
	['lansing\\b',42.73,-84.55],
	['laredo\\b',27.52,-99.49],
	['lincoln\\b',40.81,-96.68],
	['louisville\\b',38.25,-85.76],
	['lubbock\\b',33.57,-101.89],
	['madison\\b',43.07,-89.4],
	['memphis\\b',35.11,-89.97],
	['mesa\\b',33.42,-111.83],
	['miami\\b',25.78,-80.22],
	['milwaukee\\b',43.05,-87.95],
	#['montreal\\b',45.51,-73.55],
	['nashville\\b',36.17,-86.78],
	['new haven\\b',41.31,-72.92],
	['norfolk\\b',36.91,-76.2],
	['oakland\\b',37.8,-122.27],
	['omaha\\b',41.25,-96],
	['orlando\\b',28.53,-81.38],
	#['ottawa\\b',45.42,-75.7],
	['phoenix\\b',33.43,-112.07],
	['pittsburgh\\b',40.44,-80],
	['plano\\b',33.05,-96.75],
	['providence\\b',41.82,-71.42],
	['raleigh\\b',35.82,-78.64],
	['reno\\b',39.53,-119.82],
	['riverside\\b',33.95,-117.4],
	['rochester\\b',43.17,-77.61],
	['sacramento\\b',38.56,-121.47],
	['san antonio\\b',29.42,-98.5],
	['san bernardino\\b',34.13,-117.29],
	['san diego\\b',32.72,-117.17],
	['san fran(cisco)?\\b',37.77,-122.42],
	['san jose\\b',37.33,-121.89],
	['santa ana\\b',33.74,-117.88],
	['sarasota\\b',27.34,-82.54],
	['seattle\\b',47.61,-122.33],
	['spokane\\b',47.66,-117.43],
	['stockton\\b',37.98,-121.3],
	['tallahassee\\b',30.45,-84.27],
	['tampa\\b',27.97,-82.46],
	['toledo\\b',41.67,-83.58],
	['tucson\\b',32.22,-110.93],
	['tulsa\\b',36.13,-95.94],
	['(las )?vegas\\b',36.18,-115.14],
	['virginia beach\\b',36.85,-75.98],
	['wichita(?! falls)\\b',37.69,-97.34],
	['winston ?salem\\b',36.1,-80.26]]
	
cities = {}
cityre = re.compile(u'([a-z ]+)[, ]+([a-z]{2})\Z')
utre = re.compile(u'(üt|iphone): ([0-9\.]+[0-9]),(-[0-9\.]+[0-9])')
llre = re.compile(u'([0-9\.]+[0-9]),(-[0-9\.]+[0-9])')
depunctre = re.compile(u'[^a-z ]')
cleantweetre = re.compile(u'[\n,]')

def findcities(text):
	#print text
	text = depunctre.sub('',text)
	#print text
	for city in knowncities:
		r = re.match(city[0],text)
		if r:
			return [text,'unk',str(city[1]),str(city[2])]
	return None

def getlimits():
	errors = 0
	maxerrors = 3
	while (errors < maxerrors):
		try:
			r = tsearch.application.rate_limit_status(resources='search')
			break
		except TwitterHTTPError as e:
			errors = errors + 1
			print "Twitter Error encountered. Retrying",MAXERRORS-errors,"more times."                                                       
			print "\n"+e.response_data
			sleep(5)
	if (errors==MAXERRORS):
		print "Repeated errors encountered, possibly due to rate limit."
		print "Will wait 15 minutes and try once more before quitting."
		sleep(900)
		try:
			r = tsearch.application.rate_limit_status(resources='search')
		except:			
			raise Exception("Gave up because of repeated errors, sorry.")
	return r['resources']['search']['/search/tweets']

def parsetime(timestr):
	#Assumes Twitter is still reporting a tweet's time as, e.g.,:
	# "Wed Aug 27 13:08:45 +0000 2008"
	#Returns list of: day,year,month,date,hour,minute,second
	monthdict = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6','Jul':'7','Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}
	timesplit = re.split('[: ]',timestr)
	timelist = [timesplit[0],timesplit[7],monthdict[timesplit[1]]]
	timelist.extend(timesplit[2:6])
	return ','.join(timelist)

def extractinfo(res,wff=False):
	outputline = ''
	outcome = ''
	tid = res['id_str']
	tweettime = parsetime(res['created_at'])
	tweet = cleantweetre.sub(' ',res['text'])+'\n'
	try:
		uid = res['user']['id_str']
	except:
		tweetline = 'unk,unk,'+tid+','+tweet
		return ['','nouserinfo',tid,tweetline]
			
	if res['geo']:
		print 'GEO: '+str(res['geo']['coordinates'])+' '+tweet.strip()
		outcome = 'geo'
		origloc = str(res['geo']['coordinates'][0])+','+str(res['geo']['coordinates'][1])
		outputline = outcome+','+'unk,unk,'+origloc+','+uid+','+tid+'\n'
	elif res['coordinates']:
		print 'COORD: '+str(res['coordinates']['coordinates'])+' '+tweet.strip()
		outcome = 'coordinates'
		origloc = str(res['coordinates']['coordinates'][0])+','+str(res['coordinates']['coordinates'][1])
		outputline = outcome+','+'unk,unk,'+origloc+','+uid+','+tid+'\n'
	else:
		loc = res['user']['location'].lower().strip()
		origloc = loc.replace(',',' ')
		lr = utre.match(loc)
		if lr:
			print 'UT: ['+lr.group(2)+','+lr.group(3)+'] '+tweet.strip()
			outcome = 'ut'
			outputline = outcome+','+'unk,unk,'+lr.group(2)+','+lr.group(3)+','+uid+','+tid+'\n'
			#return [outputline,outcome,tid]
		else:
			#print 'L: '+loc+' '+res['text']
			ll = llre.search(loc)
			if ll:
				print 'LL: '+loc+' '+tweet.strip()
				outcome = 'llprofile'
				outputline = outcome+','+'unk,unk,'+ll.group(1)+','+ll.group(2)+','+uid+','+tid+'\n'
				#return [outputline,outcome,tid]
			else:
				loc = loc.replace('.','')
				loc = replacestates(loc)
				r = cityre.search(loc)
				if r:
					city = r.group(1).strip()
					state = r.group(2).replace('.','')
					if state in cities:
						if city in cities[state]:
							print 'CS: '+city+','+state+' '+tweet.strip()
							outcome = 'citystate'
							outputline = outcome+','+city+','+state+','+str(cities[state][city][0])+','+str(cities[state][city][1])+','+uid+','+tid+'\n'
							tweetline = ','.join([origloc,uid,tid,tweet])
							return [','.join([tweettime,outputline]),outcome,tid,tweetline]	#skip the rest of the manual city list
				cityres = findcities(loc)
				if cityres:
					#print cityres
					print 'KC: '+cityres[0]+' '+tweet.strip()
					outcome = 'knowncity'
					outputline = outcome+','+cityres[0]+','+cityres[1]+','+cityres[2]+','+cityres[3]+','+uid+','+tid+'\n'
				else:
					#print 'Unsuccessful loc: ',loc,' (from user ',uid,')\n'
					print 'F: '+origloc+' '+uid
					outcome = 'failure'
					if wff:
						failline = origloc+'\n'
						wff.write(failline.encode('ascii','ignore'))
	csvloc = origloc.replace(',',';')						#Removing excess commas for storing tweet in a CSV
	tweetline = ','.join([csvloc,uid,tid,tweet])
	if outputline:
		outputline = ','.join([tweettime,outputline])			#Adding time iff there is something to output
	return [outputline,outcome,tid,tweetline]

def balanceandprint(tl,mintids,maxtids,searchesleft,wf):
	maxoutcutoff = 2 			#A search is considered to have maxed out if this many searches left
	maximin = float("+inf")
	print "Balancing multi-location search results."
	#print searchesleft
	#print maxtids
	#print mintids
	ranges = [0]*len(maxtids)
	for locnum in range(0,len(maxtids)):
		ranges[locnum] = (maxtids[locnum]-mintids[locnum])
		if searchesleft[locnum] <= maxoutcutoff:
			maximin = min(maximin,ranges[locnum])	#maximin is the max min tid of searches that did max out
	#print ranges
	print "maximin:",maximin
	for locnum in range(0,len(tl)):
		cutoffs = 0
		#print "accept after", long(maxtids[locnum]-maximin), "for loc", locnum
		for resnum in range(0,len(tl[locnum])):
			#print "curr tweet: ", tl[locnum][resnum][2]
			#weight = str(maximin/ranges[locnum])			#Weights for a search location as relative rate to most productive search
			if maximin==float("+inf"):
				wf.write(tl[locnum][resnum][0][:-1]+",1\n")
			elif tl[locnum][resnum][2] >= (maxtids[locnum]-maximin):	#If current hit comes after the cutoff
				wf.write(tl[locnum][resnum][0][:-1]+",1\n")
			else:
				wf.write(tl[locnum][resnum][0][:-1]+",0\n")
				cutoffs = cutoffs + 1
		print cutoffs, "cutoffs for loc", locnum
	return
		


################################################################################
#
# Recognizing additional options
#
################################################################################

#loclist = ["39.8,-98.6"]
loclist = ["30.8,-98.6","39.8,-95.6","32.8,-117.6","37.8,-122.6"]
radius = "2500km"
multiloc = True
tweetspersearch = 50
maxpages = 20
maxid = float("+inf")
importcsv = ''
overwrite = 'w'
outfile = ''
keeptweets = True
startat = 0
header = True
throttle = True
checklimits = 3 		#To avoid overquerying the rate_limit function, only check every N iterations
importmultiloc = False
newmultiloc = False
onlyincltweets = False
wff = False
trackfails = False
MAXERRORS = 3

if (len(sys.argv) > 2):
	for arg in sys.argv[2:]:
		tag = arg[0:2]
		featval = arg[3:]
		if tag == '-l':					#-l: latitude,longitude pair
			loclist = [featval]				#e.g., -l=39.8,-98.6
			multiloc = False
		elif tag == '-r':				#-r: radius
			radius = featval				#e.g., -r=2500km
		elif tag == '-p':				#-p: max number of search pages (1/50 number of tweets)
			maxpages = int(featval)			#e.g., -p=20
		elif tag == '-b':				#-b: return tweets before this tweetid
			maxid = long(featval)			#e.g., -b=1032034034
		elif tag == '-c':				#-c: import tweetids from a separate csv
			importcsv = featval				#e.g., -c=needs+done.csv
		elif tag == '-t':				#-t: change number of tweets requested per search
			tweetspersearch = int(featval)
		elif tag == '-a':				#-a: append results to existing outfile
			overwrite = 'a+'
			header = False
		elif tag == '-f':				#-f: specify outfile name (incl. extension)
			outfile = featval
		elif tag == '-k':				#-k: keep an archive of found tweets for re-processing
			keeptweets = False
		elif tag == '-s':				#-s: start with tweet number... (to be used with -c tag)
			startat = int(featval)
			overwrite = 'a+'
			header = False
		elif tag == '-h':				#-h: omit commented header on csv file 
			header = False
		elif tag == '-T':				#-T: turn throttling off
			throttle = False
		#elif tag == '-L':				#-L: use the four locations that cover the U.S.
		#	loclist = ["30.8,-98.6","39.8,-95.6","32.8,-117.6","37.8,-122.6"]
		#	multiloc = True
		elif tag == '-o':				#-o: omit excluded tweets (incl=0) when constructing a baseline
			onlyincltweets = True
		elif tag == '-F':
			trackfails = True
		else:
			raise ValueError("Inappropriate option "+tag)

tweetcount = 0

if (importcsv and multiloc):
	importmultiloc = True
elif multiloc:
	newmultiloc = True

#Loading city data
infile = 'NationalFile_20120204.txt.cities'
rf = open(infile,'r')
for line in rf:
	splitline = line.split(',')
	state = splitline[1]
	if state not in cities:
		cities[state] = {}
	cities[state][splitline[0]] = [float(splitline[2]),float(splitline[3])]
rf.close()
cities = replacecitystate(cities)

if importcsv:
	rf = open(importcsv,'r')
	firstline=True
	tidnum = 0
	tids = []
	centers = []
	incls = []
	for line in rf:
		if line[0] == '#':
			continue
		splitline = line.strip().split(',')
		if firstline:
			tidnum = splitline.index('tid')
			if importmultiloc:
				centernum = splitline.index('center')
				inclnum = splitline.index('incl')
			firstline=False
		else:
			if onlyincltweets:							#If we're excluding excluded tweets from baseline calc, skip to next line if incl=0
				if int(splitline[inclnum])==0:
					continue
			tids.append(long(splitline[tidnum])-1)
			if importmultiloc:
				centers.append(int(splitline[centernum]))
				incls.append(int(splitline[inclnum]))
	tids = tids[startat:]
	if importmultiloc:
		centers = centers[startat:]
		incls = incls[startat:]
	maxpages = len(tids)
	tids.append(0)
	firsthit = tids[0]
	rf.close()
else:
	firsthit = float("+inf")

outcomes = {}
locnum = -1
if newmultiloc:
	tweetlist = [0]*len(loclist)
	searchesleft = [0]*len(loclist)
	mintids = [0]*len(loclist)
	maxtids = [0]*len(loclist)
elif importmultiloc:
	tweetlist = [0]*maxpages		#tweetlist[tweetnum][locnum][resnum] = [outline,loc,tid] for the resnum-th baseline tweet in loc locnum on testtweet tweetnum
	mintids = [0]*maxpages
	maxtids = [0]*maxpages
	
	
#Establishing the search & opening to output files
term1 = sys.argv[1]
term = re.sub('\"','%22',term1)
#tsearch = Twitter(auth=OAuth("1561556856-T5Ghc0hknos9hkomMha3bFmTDROlGEhcmH9fiRT","38FBa6J0ZWTo4RHN0VIgJiH04mdclP741UhjSmqFQ","Brhj5ftfRjqbrQ2VzP9FgQ","TswFCXCvJprccThSuGatJyBCmTny7HvJNPQeY7aKbU"))

app_oauth_file = 'app.oauth'
cons_oauth_file = 'cons.oauth'

apptoken, appsecret = read_token_file(app_oauth_file)
constoken, conssecret = read_token_file(cons_oauth_file)
tsearch = Twitter(auth=OAuth(apptoken,appsecret,constoken,conssecret))

if importcsv:
	if not outfile:
		outfile = 'base.'+term1.strip('\"')+'.'+importcsv
else:
	if not outfile:
		outfile = term1.strip('\"')+'.csv'
wf = open(outfile,overwrite)
latlong = loclist[0]
if header:
	wf.write('#Compiled by SeeTweet '+versionnum+'.\n')
	wf.write('#Search performed at '+strftime('%Y-%m-%d %H:%M')+'\n')
	if not multiloc:
		wf.write('#Search location: '+latlong+','+radius+'\n')
	else:
		wf.write('#Search location: U.S. 4-location coverage points (Texas, KC, SD, SF)\n')
	wf.write('#Search term: '+term1+'\n')
if (overwrite=='w' and not multiloc):
	wf.write('day,year,month,date,hour,minute,second,source,city,state,lat,long,uid,tid\n')
elif (overwrite=='w' and newmultiloc):
	wf.write('day,year,month,date,hour,minute,second,source,city,state,lat,long,uid,tid,center,incl\n')
elif (overwrite=='w' and importmultiloc):
	wf.write('day,year,month,date,hour,minute,second,source,city,state,lat,long,uid,tid,origtid,origincl,center,incl\n')
if keeptweets:
	tweetdir = 'tweetarchive'
	if not os.path.exists(tweetdir):
		os.mkdir(tweetdir)
	outtweetfile = tweetdir+'/'+os.path.splitext(outfile)[0]+'.tweets'
	wft = open(outtweetfile,overwrite)
	if overwrite=='w':
		wft.write('loc,uid,tid,tweet\n')
if trackfails:
	faildir = 'failures'
	if not os.path.exists(faildir):
		os.mkdir(faildir)
	outfailfile = faildir+'/'+os.path.splitext(outfile)[0]+'.fails'
	wff = open(outfailfile,'w')
	
	
	
	
for latlong in loclist:
	locnum = locnum + 1
	geocodestr = latlong+","+radius
	print "Search centered at:", latlong, "(locnum "+str(locnum)+")"
	if newmultiloc:
		currloctweets = []
		tidbycurrloc = []
	
	for pagenum in range(0,maxpages):
		print ''
		if importmultiloc:
			if (locnum==0):
				tweetlist[pagenum] = []
				maxtids[pagenum] = []
				mintids[pagenum] = []
			#print maxtids
			currloctweets = []
			tidbycurrloc = []
		#Examining the rate limit
		if (pagenum % checklimits == 0):
			r = getlimits()
			if r['remaining'] <= checklimits:
				print "\n\n**Paused because of rate limit.**"
				print "Current time:",strftime('%I:%M:%S')
				print "Reset time:  ",strftime('%I:%M:%S',localtime(r['reset']))
				if not multiloc:
					print "Resume with flag -s="+str(startat+pagenum)
				else:
					print "Stopped on location "+str(locnum)+", tweet "+str(startat+pagenum)+"/"+str(maxpages)
				print "--"
				print tweetcount, 'tweets found. Centered at', geocodestr
				print outcomes
				if throttle:
					waittime = r['reset']-time()+30
					print "Waiting", round(waittime), "seconds before resuming."
					sleep(waittime)
				else:
					sys.exit()
			elif r['remaining'] < 11:
				print "\n\n**WARNING:", r['remaining'], "queries remaining.**"
				print "Current time:",strftime('%I:%M:%S')
				print "Reset time:  ",strftime('%I:%M:%S',localtime(r['reset']))
				print ""
				print "\n\n"
				sleep(10)
		
		#Adding a catch for various Twitter errors
		errors = 0
		while (errors < MAXERRORS):
			try:
				if (firsthit == float("+inf")):
					res = tsearch.search.tweets(q=term+'+-rt',geocode=geocodestr,count=str(tweetspersearch),result_type="recent")
				else:
					res = tsearch.search.tweets(q=term+'+-rt',geocode=geocodestr,count=str(tweetspersearch),result_type="recent",max_id=str(firsthit))
				break
			except TwitterHTTPError as e:
				errors = errors + 1
				print "Twitter Error encountered. Retrying",MAXERRORS-errors,"more times."                                                       
				print "\n"+e.response_data
				sleep(5)
		if (errors==MAXERRORS):
			print "Repeated errors encountered, possibly due to rate limit."
			print "Will wait 15 minutes and try once more before quitting."
			sleep(900)
			try:
				if (firsthit == float("+inf")):
					res = tsearch.search.tweets(q=term+'+-rt',geocode=geocodestr,count=str(tweetspersearch),result_type="recent")
				else:
					res = tsearch.search.tweets(q=term+'+-rt',geocode=geocodestr,count=str(tweetspersearch),result_type="recent",max_id=str(firsthit))
			except:			
				raise Exception("Gave up because of repeated errors, sorry.")
		res = res['statuses']
			
		print len(res), 'hits on page', startat+pagenum+1, '(max_id='+str(firsthit)+')'
		print r['remaining']-1, 'queries remaining.'
		if (len(res)==0):
			break
		for i in range(0,len(res)):
			tweetcount = tweetcount + 1
			[outline,outcome,tid,tline] = extractinfo(res[i],wff)
			if outline:
				if not multiloc:
					wf.write(outline)
				elif newmultiloc:
					currloctweets.append([outline[:-1]+','+str(locnum)+'\n',locnum,long(tid)])
					tidbycurrloc.append(float(tid))
					#wf.write(outline[:-1]+','+str(locnum)+'\n')
				elif importmultiloc:
					currloctweets.append([outline[:-1]+','+str(tids[pagenum]+1)+','+str(incls[pagenum])+','+str(locnum)+'\n',locnum,long(tid)])
					tidbycurrloc.append(float(tid))
			if keeptweets:
				wft.write(tline.encode('ascii','ignore'))
			outcomes[outcome] = outcomes.get(outcome,0)+1
			if importcsv:
				firsthit = tids[pagenum+1]
			else:
				if firsthit > long(tid):			#if current tweet came before previous oldest, update oldest
					firsthit = long(tid)-1
		if importmultiloc:
			if len(tidbycurrloc) > 0:
				maxtids[pagenum].append(max(tidbycurrloc))
				mintids[pagenum].append(min(tidbycurrloc))
			else:
				maxtids[pagenum].append(0)
				mintids[pagenum].append(0)				
			tweetlist[pagenum].append(currloctweets)
	#endfor searches within a location
	if newmultiloc:
		if len(tidbycurrloc) > 0:
			maxtids[locnum] = max(tidbycurrloc)
			mintids[locnum] = min(tidbycurrloc)
		else:
			maxtids[locnum] = 0
			mintids[locnum] = 0
		searchesleft[locnum] = maxpages-pagenum-1			#calculating how many pages were left in the most maxed-out search
		tweetlist[locnum] = currloctweets
	overwrite = 'a+'
	header = False
	if importcsv:
		firsthit = tids[0]
	else:
		firsthit = float("+inf")

#Endfor multiple locations
if newmultiloc:
	balanceandprint(tweetlist,mintids,maxtids,searchesleft,wf)
elif importmultiloc:
	for pagenum in range(0,maxpages):
		balanceandprint(tweetlist[pagenum],mintids[pagenum],maxtids[pagenum],[0]*len(loclist),wf)
wf.close()
if keeptweets:
	wft.close()
if trackfails:
	wff.close()
	
print '---'
print 'Searched for', term1
print tweetcount, 'tweets found. Centered at ', geocodestr
print 'Locations:', outcomes
print '---'
#r = getlimits()
print 'Queries remaining:',r['remaining']
print "Current time:",strftime('%I:%M:%S')
print "Reset time:  ",strftime('%I:%M:%S',localtime(r['reset']))
