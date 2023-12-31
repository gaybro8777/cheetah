"""
Scripts for munging cheetafied harvard shorenstein csv data, where the csv has been appended with a column of cheetah
scores per content item.
* load data
* filter, bin, and plot scores by organization, topic, week, etc

"""

import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def queryTopic(df, topics):
	"""
	@df: The stories_election_csv data frame
	@topics: Topic terms by which to filter on 'title'; may include regex'es.
	"""

	#if querying all records, just return all records. Note this will return even those with empty titles.
	if isKleene(topics):
		return df

	pattern = "|".join(topics)
	#print("PATTERN: ",pattern)
	tf = df[ df['title'].str.contains(pattern, case=False, regex=True, na=False) ]
	print("Got {} records on topic query {}".format(tf.size, topics))
	return tf

def convertPublishDate(df):
	# converts publish_date string values in format "2015-12-28 07:00:00" to datetime objects
	df['publish_date'] = pd.to_datetime(df['publish_date'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
	return df

def loadData():
	#TODO: only read columns of interest. This reads tons on unused data.
	dataPath = "../../data/stories_election_web_cheetofied2.csv"
	if not os.path.isfile(dataPath):
		dataPath = "../data/stories_election_web_cheetofied2.csv"

	print("Loading dataset from "+dataPath)
	df = pd.read_csv(dataPath, header=0)
	return convertPublishDate(df)

def filterByDateTimeRange(df, minDt, maxDt):
	return df[ (df['publish_date'] >= minDt) & (df['publish_date'] <= maxDt) ]

# groupby isoweek+year, sum cheetah values per week
def groupByWeekYear(df):
	return df.groupby(pd.Grouper(key='publish_date', freq="W-MON"))

def sumAndPlotCheetahValues(grp, label=None, spanAvg=None):
	"""
	@grp: the dt-grouped content
	@label: A legend label for this group (e.g. the topic)
	@spanAvg: If not None, then avg binned values by this span. E.g., if span=2, then average over adjacent weeks.
	"""

	summed = grp['cheetah'].sum()
	#print("SUMMED: ", summed)
	if summed.size > 0:
		if label is not None and len(label) > 0:
			if spanAvg is not None and spanAvg > 1:
				summed = summed.ewm(span=spanAvg).mean()
			ax = summed.plot(label=label)
			ax.legend(loc=0)
		else:
			summed.plot()
	else:
		print("Error, sum contains no data")

def weightCheetahScoresByShares(df, shareCol="facebook_share_count"): #harvard data only has fb shares; other share columns are all zero or bad data.
	df["cheetah"] = df["cheetah"] * df[shareCol]
	return df

def filterCheetahNans(df):
	# Missing cheetah values (e.g. not headline/language data) are stored as NaN. This filters them.
	return df[ df['cheetah'].notnull() ]

def prettyGrid():
	# Updates the current plot state with a nice grid.
	plt.grid(b=True, which='major', color='#666666', linestyle='-')
	# Show the minor grid lines with very faint and almost transparent grey lines
	plt.minorticks_on()
	plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)

def filterCheetahZeroes(df):
	"""
	It is a good idea to filter cheetah scores which are zero, because for the harvard dataset (which has only short headlines, not much language),
	a score of zero often means there is no score or an indeterminate one due to insufficient language data. It is possible for content to
	have data, and still result in a score of zero, but this is exceedingly rare in floating point. So filtering zeroes will stand little chance
	of loss of real zero scores.
	"""
	return df[ df['cheetah'] != 0.0 ]

def plotTopicalCheetahTimeSeries(df, topicLists, minDt, maxDt, weightByShares=False):
	spanAvg = 2
	shareCol = "facebook_share_count"
	# Plot topical cheetah values as time series, for multiple time series on a single plot
	#@df: A source-filtered df derived from the harvard data frame. NOTE: Must have publish_date values converted to datetime before calling!
	for topicList in topicLists:
		dtf = filterByDateTimeRange(df, minDt, maxDt)
		tf = queryTopic(dtf, topicList)
		tf = filterCheetahNans(tf)
		if weightByShares:
			tf = weightCheetahScoresByShares(tf, shareCol)
		grp = groupByWeekYear(tf)
		s = sumAndPlotCheetahValues(grp, label=topicList[0], spanAvg=spanAvg) #plot 2-week average

	title = "Cheetah{}".format(" {}-week average".format(spanAvg) if spanAvg > 1 else "")
	if weightByShares:
		title += ", weighted by {}".format(shareCol)
	plt.title(title)
	plt.show()

def plotHist(df, col, numBins=100, weightCol=None, bestFit=True, label=None, asDensity=False):
	# Plots, but does not show, a histogram of @col values; if weightCol is not None, then hist is weighted by this column (e.g., social shares)
	# The pattern is just to call this multiple times to plot histograms, then call plt.show() or savefig().
	series = df[col]
	weights = df[weightCol] if weightCol is not None else None
	density = 1 if asDensity else None
	prettyGrid()
	n, bins, patches = plt.hist(series, bins=numBins, weights=weights, label=label, density=density, alpha=0.5)
	# add a best-fit line using normal-dist
	if bestFit:
		mu = series.mean()
		sigma = series.std()
		lastColor = patches[0].get_facecolor()
		ys = np.exp(-0.5 * ((bins - mu)**2 / sigma**2))  / (np.sqrt(2 * np.pi) * sigma)
		if not asDensity:
			# converts pdf back into the space of the frequency-histogram
			ys = ys * np.sum(np.diff(bins) * n)
		plt.plot(bins, ys, "--", color=lastColor, lw=2.0, alpha=1.0)
	return n, bins, patches

def plotTopicalCheetahHistograms(df, topicLists, minDt, maxDt):
	"""
	Plot topical cheetah values as histograms. One plot, multiple histograms, one for each topic.
	@df: A source-filtered df derived from the harvard df. NOTE: Must have publish_date values converted to datetime before calling!
	"""
	# plot basic, unweighted cheetah histogram
	bins = 100
	for topicList in topicLists:
		df = filterByDateTimeRange(df, minDt, maxDt)
		tf = queryTopic(df, topicList)
		tf = filterCheetahNans(tf)
		# filtering zeroes must be done since zero is an ambiguous value: it could mean no-score or that the actual cheetah score is zero. The latter would be extremely rare, in floating point.
		tf = filterCheetahZeroes(tf)
		plotHist(tf, "cheetah", bins, bestFit=True, label=topicList[0])

	#plt.grid(b=True, which='major', color='#666666', linestyle='-')
	plt.legend(loc=0)
	plt.title("Cheetah histogram")
	plt.show()

	# plot weighted histogram, by one of the social networks
	bins = 200
	fb_column = "facebook_share_count"
	bitly_column = "bitly_click_count" # bitly and tweet counts suck; too much missing data, or none at all
	tweet_column = "normalized_tweet_count"
	share_column = fb_column
	for topicList in topicLists:
		df = filterByDateTimeRange(df, minDt, maxDt)
		tf = queryTopic(df, topicList)
		tf = filterCheetahNans(tf)
		# filtering zeroes must be done since zero is an ambiguous value: it could mean no-score or that the actual cheetah score is zero. The latter would be extremely rare, in floating point.
		tf = filterCheetahZeroes(tf)
		plotHist(tf, "cheetah", bins, weightCol=share_column, bestFit=True, label=topicList[0])	

	plt.legend(loc=0)	
	plt.title("Cheetah histogram, weighted by "+share_column) 
	plt.show()

def filterBySource(df, urls):
	print("Getting by source per urls: ", urls)

	# If querying for all, just return all records
	if isKleene(urls):
		return df

	return df[ df['media_url'].str.contains("|".join(urls), case=False, na=False) ]

def getSourceUrls(df):
	valid = False
	while not valid:
		urls = [url.strip() for url in input("Enter urls separated by commas, by which to substring match on media_url: ").split(",") if len(url.strip()) > 0]
		if len(urls) == 0:
			print("Empty list. Re-enter urls.")
		else:
			if isKleene(urls):
				urlSeries = df["media_url"]
			else:
				urlSeries = df[ df['media_url'].str.contains("|".join(urls), case=False) ]['media_url']
			hitCount = urlSeries.size
			hits = urlSeries.values.tolist()
			# uniquify hits
			hits = sorted(list(set(hits)))
			print("{} matching urls in data {}".format(len(hits), "\n\t"+"\n\t".join(hits)))
			print("{} org hits (records)".format(hitCount))
			valid = len(hits) > 0
			if not valid:
				print("No hits. Re-enter urls.")

	return urls

def isKleene(queryTerms):
	return "*" in queryTerms

def getTopics(prompt="Enter comma-separated terms on a topic (or regex): "):
	valid = False
	while not valid:
		topics = [topic.strip() for topic in input(prompt).split(",") if len(topic.strip()) > 0] 
		valid = len(topics) > 0
		if not valid:
			print("Empty list. Re-enter topics.")

	if "*" in topics:
		topics = ["*"]

	return topics

def getTopicLists():
	done = False
	topicLists = []
	while not done:
		topics = getTopics("Enter comma-separated terms on a topic, '*' for all records, and 'done' when complete: ")
		if len(topics) == 1 and (topics[0] == "done" or topics[0] == "*"):
			if topics[0] == "*":
				topicLists.append(topics)
			done = len(topicLists) > 0
			if not done:
				print("Error: no topics entered. Re-enter.")
		else:
			topicLists.append(topics)

	return topicLists

def seriesMunging():
	# load harvard data
	harvardDf = loadData()

	done = False
	while not done:
		# filter by source/organization via the media_url field
		urls = getSourceUrls(harvardDf)
		df = filterBySource(harvardDf, urls)
		# get multiple topic sets to plot
		topicLists = getTopicLists()
		# get topics, group by week, and plot aggregate cheetah values by week
		minDt = datetime.datetime(year=2015, month=1, day=1)
		maxDt = datetime.datetime(year=2016, month=12, day=31)
		plotTopicalCheetahTimeSeries(df, topicLists, minDt, maxDt)
		plotTopicalCheetahTimeSeries(df, topicLists, minDt, maxDt, weightByShares=True)
		plotTopicalCheetahHistograms(df, topicLists, minDt, maxDt)
		done = input("Analyze another topic and source? Enter y or n: ").lower() == "n"


def main():
	"""
	#seriesMunging()
	topicLists = [["trump", "donald"], ["clinton", "hillary"]]
	df = loadData()
	#df = filterCheetahNans(df)
	minDt = datetime.datetime(year=2015, month=1, day=1)
	maxDt = datetime.datetime(year=2016, month=12, day=31)
	#plotTopicalCheetahHistograms(df, topicLists, minDt, maxDt)
	"""
	
	seriesMunging()

if __name__ == "__main__":
	main()

"""
def 
	srcs = [
		["cnn.com"],
		["wsj.com", ],
		["nbc.com"],
		["rt.com"],
		["foxnews.com", "foxbusiness.com"],
		["wapo.com", "washingtonpost.com"]
	]

	for orgUrls in srcs:
"""	





