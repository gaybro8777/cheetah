"""
Headline results are grouped by topics, and source. This primitive class just puts this into a formal
object instead of using lists of lists and tuples, like (["trump","donald"],[bunch of Headlines]), (["clinton","hillary"],[bunch of headlines on hillary]), ...
Instead, the results are returned as [TopicSearchResult,TopicSearchResult]. SourceResultCollection just holds this list
along with the name of the source.

Since queries are deployed to multiple source collections, each of which comprises multiple organizations, the results
are also grouped by source name. Hence, as they would be group in folders, the organization is:
	name/
		topic/
			headlines/

A query down into a SourceCollection would thus return a list of these as a SourceResultCollection




QueryTopicResult: an individual pair of topic terms and Headlines on those topic terms
	@QueryTopics: the search terms
	@TopicHeadlines: the headline objects on these terms

SourceResultCollection: a container for one source's search results
	@Name: name of the source
	@TopicalResults: the QueryTopicResult objects for this source and query

"""
import json
from headline import Headline
import traceback
import inspect

class QueryResult(object):
	"""
	@queryTopics: A list of query terms comprising one topic: ["donald", "trump", "djt"]
	@headlines: A list of Headline objects presumably on @queryTopics, aggregated and returned from one ContentSource
	"""
	def __init__(self, queryTopics, headlines):
		self.Topics = sorted(queryTopics)
		self.Headlines = headlines

	def GetSummary(self):
		return "{}:{}".format(str(self.Topics), len(self.Headlines))

#Container for many TopicSearchResults, for a unique source. 
class ResultCollection(object):
	"""
	@name: Name of the ContentSource, e.g. "cnn" per the content-source, NOT the org
	@topicalResults: A list of QueryResults for this source.
	"""
	def __init__(self, name, topicalResults=[]):
		self.Name = name
		self.QueryResults = topicalResults

	def _isHeadline(self, o):
		try:
			if isinstance(o, common.headline.Headline):
				return True
		except:
			pass
		try:
			if isinstance(o, headline.Headline):
				return True
		except:
			pass
		try:
			if isinstance(o, Headline):
				return True
		except:
			pass
		return False

	def _json_default(self, o):
		#print("Type: {}".format(type(o)))
		if self._isHeadline(o):  #isinstance much safer and more stable than 'type(o)==Headline' which gets fucked by relative imports and qualified class names common.headline.Headline for some reason
			return o.ToDict()
		else:
			#print("Returning __dict__ for object type {}".format(type(o)))
			return o.__dict__

	def Serialize(self, ofile):
		#Obsolete; replaced by WriteJSON. This fails for large datasets because it allocates an entire json string representation of potentially huge datasets.
		#json.dumps(self, ensure_ascii=False, default=self._json_default, sort_keys=True, indent=4)
		success = False
		try:
			json.dump(self, ofile, ensure_ascii=False, default=self._json_default, sort_keys=True, indent=4)
			success = True
		except:
			traceback.print_exc()

		return success

	def GetMinMaxDt(self):
		# Given a list of ResultCollection's, returns the min/max headline datetimes for auto-scaling results.
		minDt = datetime.max
		maxDt = datetime.min
		for queryResult in self.QueryResults:
			for headline in queryResult.Headlines:
				if headline.DT < minDt:
					minDt = headline.DT
				if headline.DT > maxDt:
					maxDt = headline.DT
		return minDt, maxDt

	@staticmethod
	def GetMinMaxDt(resultCollections):
		"""
		Returns the min and max DT (as datetimes) from a collection of ResultCollections, as a (min, max) pair
		"""
		minDt = datetime.max
		maxDt = datetime.min
		for resultCollection in resultCollections:
			rcMinDt, rcMaxDt = resultCollection.GetMinMaxDt()
			if rcMinDt < minDt:
				minDt = rcMinDt
			if rcMaxDt > maxDt:
				maxDt = rcMaxDt

		return minDt, maxDt

	@staticmethod
	def FromHeadlines(headlines, topicLists, name="default"):
		"""
		Doesn't belong here, but given a raw list of headlines, and topics possibly relating to those headlines, partitions @headlines list
		of Headline objects into ResultCollections per the lists in @topicLists. In english, that means one ResultCollection for each topic-list
		in @topicLists, each of which includes all headlines containing any terms in that topic-list.
		"""
		results = []
		for topicList in topicLists:
			hits = [headline for headline in headlines if headline.HasTopicHit(topicList)]
			result = QueryResult(topicList, hits)
			results.append(result)

		return ResultCollection(name, results)

	"""
	Another doesn't-belong-here, but a useful pattern. Give a list of ResultCollection objects, get the unique topic sets
	over all resultCollections.
	NOTE: SETS DESTROY ORDERING!
	"""
	@staticmethod
	def GetTopicSets(resultCollections, frozen=False):
		print("WARNING: GetTopicSets() returns UNORDERED topic sets. Verify that this is desired, or analyses may be attributed to incorrect topics.")
		allTopicSets = set()
		#get the unique topic sets; in truth, these should be exactly replicated for each ResultCollection
		for collection in resultCollections:
			topicSets = set(frozenset(result.Topics) for result in collection.QueryResults) #frozenset provides a hashable, immutable set
			for topicSet in topicSets:
				allTopicSets.add(topicSet)

		if frozen:
			allTopicSets = set(frozenset(topicSet) for topicSet in allTopicSets)

		return allTopicSets

	@staticmethod
	def GetTopicLists(resultCollections):
		return [list(topicSet) for topicSet in ResultCollection.GetTopicSets(resultCollections)]

	"""
	An emerging pattern. Given a list of ResultCollections, get the headlines grouped by topic-list,
	like in much of the old code. This is currently a potentially memory wasteful function, since it creates
	big merged lists from each individual topical list from each result.

	Returns: A list of pairs, [[topics], [headlines on @topics]].
	"""
	@staticmethod
	def GetTopicalHeadlinePairs(resultCollections, dtLow=None, dtHigh=None):
		topicalDict = dict() #maps topics to headlines on that topic
		topicSets = ResultCollection.GetTopicSets(resultCollections, frozen=True)
		for topicSet in topicSets:
			topicalDict[topicSet] = []

		for collection in resultCollections:
			for result in collection.QueryResults:
				if dtLow is not None and dtHigh is not None:
					headlines = [headline for headline in result.Headlines if headline.IsInDateRange(dtLow, dtHigh)]
				else:
					headlines = result.Headlines
				topicalDict[frozenset(result.Topics)] += headlines

		headlinePairs = [(sorted(list(t[0])), t[1]) for t in list(topicalDict.items())]

		return sorted(headlinePairs, key=lambda p: p[0]) #this sorts the pairs by topic lists, which is pretty dumb, since the sorts compares ordered lists of strings, not strings

	"""
	This doesn't really belong here, but in an outer container class, which is always simply <list>, so leaving this here instead for simplicity.

	@resultCollections: A list of result collection objects.
	"""
	@staticmethod
	def SaveCollections(resultCollections, savePath):
		print("Saving collections to {}".format(savePath))
		#save the raw data as one big pot, in a single file, as list of ResultCollection json objects
		with open(savePath,"w+") as ofile:
			ofile.write("[\n")
			for i, resultCollection in enumerate(resultCollections):
				resultCollection.Serialize(ofile)
				#ofile.write(json.dumps(resultCollection.__dict__))
				if i < len(resultCollections) - 1:
					ofile.write(",\n")
			ofile.write("\n]\n")

	@staticmethod
	def LoadCollections(jsonPath): #loads ResultCollection from saved json; inverse of SaveCollections()
		resultCollections = []
		
		with open(jsonPath,"r") as jsonFile:
			dictList = json.load(jsonFile)
			for d in dictList:
				print(str(d))
				collection = ResultCollection(name=d["Name"])
				for qrDict in d["QueryResults"]:
					topics = qrDict["Topics"]
					topicalHeadlines = []
					for headlineDict in qrDict["Headlines"]:
						headline = Headline()
						if headline.FromDict(headlineDict):
							topicalHeadlines.append(headline)
						else:
							print("WARNING: load failed for headline dict: "+str(headlineDict))
					queryResult = QueryResult(topics, topicalHeadlines)
					collection.QueryResults.append(queryResult)
				resultCollections.append(collection)

		return resultCollections

	@staticmethod
	def PrintResultCollectionSummary(resultCollections):
		for collection in resultCollections:
			collection.PrintQueryResultSummary()

	def PrintQueryResultSummary(self):
		summaries = " ".join([result.GetSummary() for result in self.QueryResults])
		print("Collection: {}  {}".format(self.Name, summaries))

	"""
	Given a list of topic strings @topicList, counts the headlines collected on that topic. Every term in @topicList must be included
	for it to be counted, so there is an integrity requirement that QueryResults maintain consistent @Topics topics per queries.
	"""
	def CountTopicalHeadlines(self, topicList):
		topicSet = set(topicList)
		count = 0

		for result in self.QueryResults:
			if set(result.Topics) ==  topicSet:
				count += len(result.Headlines)

		return count

	def AddResult(self, queryTopics, headlines):
		result = QueryResult(queryTopics, headlines)
		self.QueryResults.append(result)

	def Save(self, savePath):
		print("NOT YET IMPLEMENTED; COULD BE AS SIMPLE AS JSON.DUMPS(). MAYBE WRITE A COUPLE TOSTRING() METHODS")

	def Load(self, loadPath):
		print("NOT YET IMPLEMENTED")

