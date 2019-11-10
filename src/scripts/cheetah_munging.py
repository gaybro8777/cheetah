"""
Scripts for munging cheetafied harvard csv data, where the csv has been appended with a column of cheetah
scores per content item.
* load data
* filter, bin, and plot scores by organization, topic, week, etc

"""

import datetime
import pandas as pd
import matplotlib.pyplot as plt


def queryTopic(df, topics):
	"""
	@df: The stories_election_csv data frame
	@topics: Topic terms by which to filter on 'title'.
	"""
	return df[ df['title'].str.contains("|".join(topics), case=False) ]

def convertPublishDate(df):
	# converts publish_date string values in format "2015-12-28 07:00:00" to datetime objects
	df['publish_date'] = pd.to_datetime(df['publish_date'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
	return df

def loadData():
	#TODO: only read columns of interest. This reads tons on unused data.
	dataPath = "../../data/stories_election_web_cheetofied_test.csv"
	print("Loading dataset from "+dataPath)
	df = pd.read_csv(dataPath, header=0)
	return df

def filterByDateTimeRange(df, minDt, maxDt):
	return df[ (df['publish_date'] >= minDt) & (df['publish_date'] <= maxDt) ]

# groupby isoweek+year, sum cheetah values per week
def groupByWeekYear(df):
	return df.groupby(pd.Grouper(key='publish_date', freq="W-MON"))

def sumAndPlotCheetahValues(grp):
	summed = grp['cheetah'].sum()
	print("SUMMED: ", summed)
	summed.plot()

def filterCheetahNans(df):
	# Missing cheetah values (e.g. not headline/language data) are stored as NaN. This filters them.
	return df[ df['cheetah'].notnull() ]

def plotTopicalCheetahTimeSeries(df, topicLists, minDt, maxDt):
	# Plot topical cheetah values as time series
	#@df: NOTE: Must have publish_date values converted to datetime before calling!
	for topicList in topicLists:
		df = filterByDateTimeRange(df, minDt, maxDt)
		tf = queryTopic(df, topicList)
		tf = filterCheetahNans(tf)
		grp = groupByWeekYear(tf)
		s = sumAndPlotCheetahValues(grp)
	plt.show()

def filterBySource(df, urls):
	print("Getting by source per urls: ", urls)
	return df[ df['media_url'].str.contains("|".join(urls), case=False) ]

def getSourceUrls(df):
	valid = False
	while not valid:
		urls = [url.strip() for url in input("Enter urls separated by commas, to match org media_url fields by substring: ").split(",") if len(url.strip()) > 0]
		if len(urls) == 0:
			print("Empty list. Re-enter urls.")
		else:
			hits = df[ df['media_url'].str.contains("|".join(urls), case=False) ]['media_url'].values.tolist()
			# uniquify hits
			hits = list(set(hits))
			print("{} matching urls in data:  {}".format(len(hits), "|".join(set(hits))))
			valid = len(hits) > 0
			if not valid:
				print("No hits. Re-enter urls.")

	return urls

def getTopics(prompt="Enter comma-separated terms on a topic: "):
	valid = False
	while not valid:
		topics = [topic.strip() for topic in input(prompt).split() if len(topic.strip()) > 0] 
		valid = len(topics) > 0
		if not valid:
			print("Empty list. Re-enter topics.")
	return topics

def getTopicLists():
	done = False
	topicLists = []
	while not done:
		topics = getTopics("Enter comma-separated terms on a topic, or 'done' to exit: ")
		if len(topics) == 1 and topics[0] == "done":
			done = len(topicLists) > 0
			if not done:
				print("Error: no topics entered. Re-enter.")
		else:
			topicLists.append(topics)

	return topicLists

# load harvard data
harvardDf = loadData()
harvardDf = convertPublishDate(harvardDf)

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
	done = input("Analyze another topic and source? Enter y or n: ").lower() == "n"



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





