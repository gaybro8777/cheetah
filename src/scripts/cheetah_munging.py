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
	dataPath = "../../data/stories_election_web_cheetofied.csv"
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

# load harvard data
df = loadData()
# filter by org
df = filterBySource(df, ["cnn.com"])
# get topics, group by week, and plot aggregate cheetah values by week
topicLists = [["clinton","hillary"], ["trump","donald"] ]
minDt = datetime.datetime(year=2015, month=1, day=1)
maxDt = datetime.datetime(year=2016, month=12, day=31)
df = convertPublishDate(df)
plotTopicalCheetahTimeSeries(df, topicLists, minDt, maxDt)




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





