"""
Scripts for munging cheetafied harvard csv data, where the csv has been appended with a column of cheetah
scores per content item.
* load data
* filter, bin, and plot scores by organization, topic, week, etc

"""

import datetime
import pandas as pd
import matplotlib.pyplot as plt

def convertPublishDate(df):
	df['publish_date'] = pd.to_datetime(df['publish_date'], infer_datetime_format=True)
	return df

def loadData():
	#TODO: only read columns of interest. This reads tons on unused data.
	dataPath = "../../data/stories_election_web_cheetofied_test.csv"
	print("Loading dataset from "+dataPath)
	df = pd.read_csv(dataPath, header=0)
	return df

df = loadData()
# Filter by org
mediaUrl = "cnn.com"
print("Filtering by media_url: "+mediaUrl)
df = df[ df['media_url'].str.contains(mediaUrl, case=False) ]#.to_frame()
# Filter by subject in title
topic = "clinton"
print(str(type(df)))
print("cols: ", df.columns)
print("Filtering by topic: "+topic)
t1 = df[ df['title'].str.contains(topic, case=False) ]
topic = "trump"
print("Filtering by topic: "+topic)
t2 = df[ df['title'].str.contains(topic, case=False) ]
#filter cheetah nans
t1 = t1[ t1['cheetah'].notnull() ]
t2 = t2[ t2['cheetah'].notnull() ]

print(t1)
print(type(t1))
t1.hist(column="cheetah")
t2.hist(column="cheetah")
plt.show()

#Awesome time series resource: https://towardsdatascience.com/basic-time-series-manipulation-with-pandas-4432afee64ea
t1 = convertPublishDate(t1)
t2 = convertPublishDate(t2)





"""
def binByWeek(recs):


def plotSubset()
	""

	""

def orgQuery(df, orgUrls, topics=None):
	""
	Query the harvard csv dataframe by media_url column, with optional case insensitive topical filtering.

	@df: The harvard csv data loaded into a dataframe
	@orgUrls: A list of urls describing some organization or group of them, against which to match in the media_url column as a substring.
		Example: 'give me all records for 'foxnews.com' and 'foxbusiness.com' by matching these substrings in the media_url column'
	@topics: Optional set of substring to filter records by (case insensitive), over @filterCols
	""
	





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





