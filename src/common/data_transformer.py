import sys
if sys.version_info.major < 3:
	print("ERROR use python3 instead of python 2.7")
	exit()

import urllib.parse
import datetime
import string
import traceback
#from analysis import *
from ascii_text_normalizer import AsciiTextNormalizer


"""
Everything within this class is basically stateless, just transforming data and returning the results.
It seems worthwhile to circumscribe that in a class, to preserve that statelessness. In C++, this
might be a class with all static members.

The pattern is sort of pipe-filter, which might be a good direction for researching how to build this class.
It seems like you always end up with a static filter class in data analytics code.

"""
class DataTransformer(object):

	def __init__(self):
		pass

	"""
	Given a list of Headline objects, fetches all their associated Articles, and builds/returns a frequency dict
	of their outlinks as {url<string>: freq<int>}. Outlinks are resolved to their host, for instance, "www.cnn.com", "thinktank.org", etc

	"""	
	@staticmethod
	def GetArticleHostOutlinks(self, headlines, orgDb):
		hostDict = dict()
		misses = 0
		hits = 0

		for headline in headlines:
			uri = headline.URI.strip()

			if "/index.html" in uri:
				uri = uri.replace("/index.html","")
		
			#print("searching for: "+uri)
		
			article = orgDb.FetchArticleByUrl(uri)
			if article is not None:
				hits += 1
				for link in article.Outlinks:
					#resolve org/web addresses to their target hosts
					if "org/web" in link:
						link = link.split("org/web")[1][16:]
						#print("fixed: "+link)
					#clean the links a bit
					if "http" != link[0:4]:
						link = "http://"+link	
					
					#get the network location (host address) from the url
					try:
						host = urllib.parse.urlparse(link).netloc
					except:
						print("Exception thrown parsing url: "+link)
						host = link
					
					#print(host)
					if host in hostDict:
						hostDict[host] += 1
					else:
						hostDict[host] = 1
			else:
				misses += 1
				#print("Missed url: "+uri)

			#if hits > 100:
			#	break

		print("Headline Hits: "+str(hits)+"  Misses: "+str(misses))
	
		return hostDict

	#Util for getting the total shares of an iterable of headlines
	@staticmethod
	def GetNetShares(headlines):
		totalShares = 0
		for headline in headlines:
			if "share_count" in headline.Attrib:
				totalShares += headline.Attrib["share_count"]
			else:
				print("HEADLINE LACKS SHARES")
				headline.Print()
		print("Total shares: "+str(totalShares))

		return totalShares

	"""
	Same as prior, but specifically models only social media links: twitter and facebook
	The objective is to model links as social media users and sites.

	This method is more focused on uri's than network locations or urls, compared with the previous method.
		-twitter uri's
		-facebook site uri's
	
	Shortened twitter addresses are expanded; eg, t.co/1h4hh -> twitter.com/AnnoyingTwitterUser
	"""
	@staticmethod
	def GetArticleSocialMediaOutlinks(headlines, orgDb):
		uriDict = dict()
		misses = 0
		hits = 0

		for headline in headlines:
			uri = headline.URI.strip()

			if "/index.html" in uri:
				uri = uri.replace("/index.html","")
		
			#print("searching for: "+uri)
		
			article = orgDb.FetchArticleByUrl(uri)
			if article is not None:
				hits += 1
				for link in article.Outlinks:			
					#clean the links a bit
					if "http" != link[0:4]:
						link = "https://"+link	
					
					#get the network location (host address) from the url
					try:
						uri = urllib.parse.urlparse(link).path
					except:
						print("Exception thrown parsing url: "+link)
						if ".com/" in link:
							uri = link.split(".com/")[-1]
						else:
							uri = link
					
					#print(host)
					if uri in hostDict:
						uriDict[uri] += 1
					else:
						uriDict[uri] = 1
			else:
				misses += 1
				#print("Missed url: "+uri)

			#if hits > 100:
			#	break

		print("Headline Hits: "+str(hits)+"  Misses: "+str(misses))
	
		return uriDict

	"""
	Removes stop words from headlines in passed result collections.
	"""
	@staticmethod
	def RemoveStopWords(resultCollections, stopWords):
		for resultCollection in resultCollections:
			for queryResult in resultCollection.QueryResults:
				for headline in queryResult.Headlines:
					headline.StripTerms(stopWords)
		return resultCollections

	"""
	Removes off-topic topic terms from all of the text for a headline on a specific topic. Hence if headline H1 is about
	topic T1, but contains some topic terms from T2, then these terms are removed. This is a criticizable filter, but the intuition is that
	a headline about T1 and its language distribution identifies T1, not any opposiing topics that may also be in the text.
	This is helpful because a headline 'about' a topic will often also mention related or opposed topics. A headline on Trump
	would often also contain mentions of Clinton, even though the distribution of words is meant to describe Trump, so the
	co-occurrences should only be counted between 'Trump' and signal terms.
	
	NOTE: This should be called after soft-match expansion has been applied, and likely other text normalizations, especially lowercasing.
	"""
	@staticmethod
	def RemoveOffTopicTerms(resultCollections):
		topicSets = resultCollections[0].GetTopicSets(resultCollections)
		allTerms = set(term for topicSet in topicSets for term in topicSet)

		#no need to filter single-topicset queries
		if len(topicSets) > 1:
			#warn if topic sets are not disjoint; this could implement non-disjoint term removal (just ignore common terms) but I dislike the ambiguity
			for topicSet in topicSets:
				for otherSet in topicSets:
					if topicSet != otherSet and any(topicSet.intersection(otherSet)):
						print("WARNING topic terms not disjoint in RemoveOffTopicTerms: {} {}".format(topicSet, otherSet))
						print("Only disjoint terms will be removed")

			for collection in resultCollections:
				for result in collection.QueryResults:
					offTopicTerms = allTerms.difference(set(result.Topics))
					print("Removing {} from topical {} headlines".format(offTopicTerms, result.Topics))
					for headline in result.Headlines:
						headline.StripTerms(offTopicTerms)

			"""
			print("Removing off-topic terms...")
			for topicSet in topicSets:
				offTopicTerms = allTerms.difference(topicSet)
				print("Off topic terms: {}  On topic terms: {}".format(str(offTopicTerms), str(topicSet)))
				for collection in resultCollections:
					for result in collection.QueryResults:
						#only filter if result.Topics shares NO terms with offTopicTerms
						if set(result.Topics) != topicSet:
							if not any( offTopicTerms.intersection(set(result.Topics)) ):
								print("HERE: off: {}   on: {}".format(offTopicTerms, result.Topics))
								for headline in result.Headlines:
									headline.StripTerms(offTopicTerms)
							else:
								print("WARNING result.Topics={} but topicSet={}. Topic sets must be disjoint to apply cross-topic term removal.".format(result.Topics, topicSet))
								print("Intersection {} ^ {} {}: {}".format(offTopicTerms, set(result.Topics), topicSet, offTopicTerms.intersection(set(result.Topics))))
						else:
							print("Result.Topics {}   topicSet {}".format(result.Topics, topicSet))
			"""

	"""
	NOTE: Removed this because it only resolves query terms with their approximate matches (e.g. 'trumpian' is replaced with query term 'trump').
	However, add this stage in filtering we only have the query terms, not signal terms, so it only does half the work. Its better to perform matching
	at a lower level during term frequency calculations.

	For any fixed lexicon of words, say [trump, donald], there may be a lot of documents containing
	"trump's" "trumps" "donald's" and so forth, which are not a hard match, but are clearly the same reference
	and should be counted as co-occurrence. This searches over the word tokens of all headlines for a given topic,
	and checks if any of that topics terms are substrings of each word; if so, the word will be appended to the topic
	list. This could be a costly operation for large datasets. But it effectively implements an "IN" operator instead
	of an == operator when detecting co-occurrences, since the soft matching terms will no be included in the topic list.

	Algorithm: Given all headlines on a list of topic terms, detect any words which are a substring of any topic terms; these
	will then be added to the topic list. The param @headlineList is modified in-place.

	NOTE: Preferably call this AFTER text normalization of punctuation, case, etc. And call it before topic term cross-filtering/removal.
	Also note that the scope of soft-matches for a particular topic is over ALL headlines, not just that topic's headlines.

	@resultCollections: An iterable of ResultCollection objects
	@caseInsensitive: case insensitive matching, but note that the returned set must be treated as such and will be all lowercase

	@staticmethod
	def TopicTermSoftmatchExpansion(resultCollections, caseInsensitive=True):
		addedWords = set()
		queryTerms = set()

		for collection in resultCollections:
			for result in collection.QueryResults:
				for headline in result.Headlines:
					headline.MapSoftTermMatches(queryTerms)

				result.Headlines = DataTransformer.UniquifyHeadlinesByDay(result.Headlines, "URI")


		for tup in enumerate(headlineList):
			i = tup[0]
			headlinePair = tup[1]
			topicTerms = headlinePair[0]
			#get the lexicon
			print("Building softmatch lexicon...")
			if caseInsensitive:
				lexicon = set(word for headlinePair in headlineList for headline in headlinePair[1] for word in headline.GetFullText().lower().split())
			else:
				lexicon = set(word for headlinePair in headlineList for headline in headlinePair[1] for word in headline.GetFullText().split())

			softMatches = set()
			for word in lexicon:
				for topic in topicTerms:
					if len(topic) < len(word) and topic in word: #detect if a topic word is a substr of another longer word; the length check prevents soft-matching equal strings needlessly
						softMatches.add(word)

			if any(softMatches):
				print("Appending softmatches to topicList: {} for topics {}".format(softMatches, topicTerms))
				tup[1][0].append(word for word in softMatches)
				addedWords.union(softMatches)

		return addedWords
	"""

	@staticmethod
	def FilterResultCollectionsByDtRange(resultCollections, dtLow, dtHigh):
		for collection in resultCollections:
			for result in collection.QueryResults:
				result.Headlines = DataTransformer.FilterHeadlinesByDtDate(result.Headlines, dtLow, dtHigh)

	"""
	A best effort to convert html/xml escaped characters using html.unescape(), and unicode/latin-1 encoded chars to ascii
	equivalents using unidecode, remove unusual characters, and lowercase

	@filterNonAlphaNum: If true, filter non-alphanumeric chars
	@deleteFiltered: Only meaningful if @filterNonAlphaNum=True; if true, filtered chars will be deleted rather than replace with spaces.
	@lowercase: Lowercase the terms in the headlines.
	"""
	@staticmethod
	def TextNormalizeHeadlines(headlines, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True):
		normalizer = AsciiTextNormalizer()
		for headline in headlines:
			DataTransformer.TextNormalizeHeadline(headline, normalizer, filterNonAlphaNum=filterNonAlphaNum, deleteFiltered=deleteFiltered, lowercase=lowercase)

	@staticmethod
	def TextNormalizeHeadline(headline, normalizer, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True):
		headline.Headline    = normalizer.NormalizeText(headline.Headline, filterNonAlphaNum=filterNonAlphaNum, deleteFiltered=deleteFiltered, lowercase=lowercase)
		headline.Description = normalizer.NormalizeText(headline.Description, filterNonAlphaNum=filterNonAlphaNum, deleteFiltered=deleteFiltered, lowercase=lowercase)
		headline.FullText    = normalizer.NormalizeText(headline.FullText, filterNonAlphaNum=filterNonAlphaNum, deleteFiltered=deleteFiltered, lowercase=lowercase)

	@staticmethod
	def TextNormalizeTerms(terms, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True):
		normalizer = AsciiTextNormalizer()
		return [normalizer.NormalizeText(term, filterNonAlphaNum=filterNonAlphaNum, deleteFiltered=deleteFiltered, lowercase=lowercase) for term in terms]

	"""
	The result collection contains results and their corresponding query terms. During analysis, 
	"""
	@staticmethod
	def CondenseMultiwordQueryTerms(resultCollections):
		queryTerms = [queryTerm for collection in resultCollections for result in collection.QueryResults for queryTerm in result.Topics]
		multiWordQueries = [query for query in queryTerms if " " in query]

		if any(multiWordQueries):
			termMap = {term:term.replace(" ","") for term in multiWordQueries}
			#first, update the resultCollection query terms themselves
			print("Condensing multiword query-terms {} to --> {}".format(termMap.keys(), termMap.values()))
			for collection in resultCollections:
				for result in collection.QueryResults:
					result.Topics = [topic.replace(" ","") for topic in result.Topics]

			#condense the multiword terms in the result content
			for collection in resultCollections:
				for result in collection.QueryResults:
					for headline in result.Headlines:
						for term, condensedTerm in termMap.items():
							headline.ReplaceTerm(term, condensedTerm)

	"""
	This is a very high level function for a recurring pattern. There is a standard query for many analyses,
	where given headlines on multiple topics, we want to uniquify them, cross-filter, clean them, and so forth.
	This requires passing the headline lists, each with their list of topics.

	NOTE: The standard applied to this function is that the returned documents/headlines can be analyzed exactly as-is without
	further processing (word resolution, conditioning, etc), such that any analysis function can treat the output of this function as-is
	without handling textual or other data transformation, except in exotic cases.

	Note: This method condenses multi-word queries to single words as a precondition for analysis. Thus "North Korea" becomes "northkorea" anywhere it is detected.

	@headlineLists: A list of lists of type ([topic list], [headlines on @topic list])
	@topicCrossFilter: Filters out ambiguous headlines containing terms on more than one topic; hence preserving only headlines uniquely about each topic
	@removeOffTopicTerms: Removes off-topic topic terms from all of the text for a headline on a specific topic. Hence if headline H1 is about
	topic T1, but contains some topic terms from T2, then these terms are removed. This is a criticizable filter, but the intuition is that
	a headline about T1 and its language distribution identifies T1, not any opposiing topics that may also be in the text.
	Returns: all headlines as a list, after all selected filters have been applied
	"""
	@staticmethod
	def PrimaryResultCollectionFilter(resultCollections, dtLow, dtHigh, topicCrossFilter=False, removeOffTopicTerms=False, uniquify=False):
		topicSuperset = set(tuple(result.Topics) for collection in resultCollections for result in collection.QueryResults)
		topicLists = [list(topics) for topics in topicSuperset]

		print("Filtering results by date...")
		DataTransformer.FilterResultCollectionsByDtRange(resultCollections, dtLow, dtHigh)

		if uniquify:
			print("Uniquifying results by day/uri...")
			#filter by unique uri, but only by day
			for collection in resultCollections:
				for result in collection.QueryResults:
					result.Headlines = DataTransformer.UniquifyHeadlinesByDay(result.Headlines, "URI")

		#normalize all text
		print("Normalizing headline text AND query terms (keep in mind for foreign character sets)...")
		for collection in resultCollections:
			for result in collection.QueryResults:
				#get the topics to remove from the headlines on this topic
				DataTransformer.TextNormalizeHeadlines(result.Headlines, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)
				#normalize the query terms themselves, to match the headline normalization (otherwise term-matching won't work)
				result.Topics = DataTransformer.TextNormalizeTerms(result.Topics, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)

		#resolve multiword query terms to single terms, for analyses ("north korea" --> "northkorea"); NOTE: Its easier for this to occur after text normalization/lowercasing
		if any(" " in queryTerm for topicList in topicLists for queryTerm in topicList):
			DataTransformer.CondenseMultiwordQueryTerms(resultCollections)
			#update the topic list info local to this function
			topicSuperset = set(tuple(result.Topics) for collection in resultCollections for result in collection.QueryResults)
			topicLists = [list(topics) for topics in topicSuperset]

		#should run after text normalization
		for topicList in topicLists:
			ct = sum(collection.CountTopicalHeadlines(topicList) for collection in resultCollections)
			print("({} #headlines: {}".format(topicList[0],ct))

		#disambiguate topics for better statistics
		if topicCrossFilter:
			print("Cross filtering topical headlines...")
			topicUnion = [topic for topicList in topicLists for topic in topicList]
			for collection in resultCollections:
				for result in collection.QueryResults:
					#get the topics to remove from the headlines on this topic
					filterTopics = [topic for topic in topicUnion if topic not in result.Topics]
					result.Headlines = DataTransformer.TopicFilterHeadlines(result.Headlines, filterTopics)

		""" REMOVED: Run this in frequency calculation, so as to boost query terms and signal term hits alike. At this point we can only soft-match
		query terms.

		#note that this can also be achived by using the "IN" operator to resolve terms to topical terms. E.g., "trump" in "Trumps", but "trump" != "Trumps"
		#soft-match replacement: replaces strings with a topical stubstr with the topical term; this should be done before term cross filter below.
		if useSoftMatch:
			print("Replacing softmatching terms with topic terms; e.g., 'trumpian'->'trump' ...")
			DataTransformer.TopicTermSoftmatchReplacement(resultCollections, caseInsensitive=True)
		"""

		#experimental: strip opposed topic terms from within the textual data of other topic's headlines
		if removeOffTopicTerms:
			print("Removing off-topic terms...")
			DataTransformer.RemoveOffTopicTerms(resultCollections)

		"""
		This was an important experiment, borne out of my fear of potential bias due to coverage volume differences for different topics.
		One sanity check is to make the two document sets equal in size, by randomly selecting articles. Alternatively, could bin 
		per day, then randomly select articles from the larger set until equal to the smaller topic set.
		"""
		#topic1Headlines, topic2Headlines = EqualifyHeadlineSets(topic1Headlines, topic2Headlines, strategy="uniform-random")

		#add full text to each article/headline set; the lexicon difference is taken to eliminate co-occurrences of topics in eachother's context
		#For example, an exclusively 'Trump' headline will nearly always include 'Clinton' but such a co-occurrence distorts the exclusive relationship of this language to 'Trump', and vice versa.
		#AppendArticleFullTextSignalHits(topic1Headlines, db, lexicon.difference(t2), hostUrl, ignoreUrlSubstrs)  # (headlines, orgDb, signalTerms, hostUrl="", ignoredUrlSubstrs=[]):
		#AppendArticleFullTextSignalHits(topic2Headlines, db, lexicon.difference(t1), hostUrl, ignoreUrlSubstrs)  # (headlines, orgDb, signalTerms, hostUrl="", ignoredUrlSubstrs=[]):

		#lastly, after all headline filtering, look up article fulltexts for the smallest, filtered set of articles
		#AppendArticleFullTextSignalHits(allHeadlines, db, lexicon, hostUrl, ignoreUrlSubstrs)  # (headlines, orgDb, signalTerms, hostUrl="", ignoredUrlSubstrs=[]):

		return resultCollections

	"""
	This is a negative filter:
	Given an headline list, remove all headlines containing any of @topicWords in the headline or description.
	Example usage, get all clinton headlines, then remove any referencing Sanders:
		clintonHeadlines = db.GetHeadlines("clinton")
		clintonHeadlines = TopicFilterHeadlines("sanders")
	This could be done in the sqlite query, or in post-processing like this function.

	@topicWords: A list of words by which to remove headlines
	"""
	@staticmethod
	def TopicFilterHeadlines(headlineList, topicWords):
		topics = [topic.lower() for topic in topicWords]
		return [headline for headline in headlineList if not headline.HasTopicalHeadlineHit(topics)]

	"""
	A positive grep filter: return only headlines in headlineList containing any of @topicWords strings in headline
	or description.
	"""
	@staticmethod
	def FilterHeadlinesInclusive(headlineList, topicWords):
		return [headline for headline in headlineList if headline.HasTopicHit(topicWords)]

	"""
	Filters headlines below a certain rank
	"""
	@staticmethod
	def FilterHeadlinesByRank(headlineList, rank):
		return [headline for headline in headlineList if headline.Rank >= rank]

	"""
	Utility for getting earliest headline in some list of headlines
	"""
	@staticmethod
	def GetEarliestHeadline(headlines):
		earliestDt = datetime.datetime.max
		earliestHeadline = None

		for headline in headlines:
			if earliestDt > headline.DT:
				earliestDt = headline.DT
				earliestHeadline = headline

		return earliestHeadline

	@staticmethod
	def GetLatestHeadline(headlines):
		latestDt = datetime.datetime.min
		latestHeadline = None

		for headline in headlines:
			if latestDt < headline.DT:
				latestDt = headline.DT
				latestHeadline = headline

		return latestHeadline

	"""
	Given a date string formatted as YYYY/MM/DD, returns YYYY, MM, DD as a three-ple
	"""
	@staticmethod
	def GetDateFromDateStr(ymdStr):
		year  = int(ymdStr.split("/")[0])
		month = int(ymdStr.split("/")[1])
		day   = int(ymdStr.split("/")[2])
	
		return datetime.date(year, month, day)

	"""
	Both @dateStr params must be formatted as YYYY/MM/DD.
	"""
	@staticmethod
	def IsHeadlineInDateStrRange(headline, lowDateStr, highDateStr):
		lowDate  = GetDateFromDateStr(lowDateStr)
		highDate = GetDateFromDateStr(highDateStr)
	
		return lowDate <= headline.DT.date() <= highDate

	@staticmethod
	def _getHeadlinesDtMin(headlines):
		minDt = datetime.datetime.max

		for headline in headlines:
			if headline.DT < minDt:
				minDt = headline.DT

		return minDt

	@staticmethod
	def _getHeadlinesMaxDt(headlines):
		maxDt = datetime.datetime.min

		for headline in headlines:
			if headline.DT > maxDt:
				maxDt = headline.DT

		return maxDt

	"""
	I should be more robust, but pass dataStr as yyyy/mm/dd: "2016/02/03", and use the zero prefixes for single digit dates.

	@lowDateStr: the low range to include, but not prior to; pass None if no lower range
	@highDateStr: the high range to include, but not after; pass None if no higher range
	"""
	@staticmethod
	def FilterHeadlinesByDate(headlineList, lowDateStr, highDateStr):
		if lowDateStr == None:
			lowDateStr = "1970/01/01"
		if highDateStr == None:
			highDateStr = "2050/12/31"
	
		return [headline for headline in headlineList if IsHeadlineInDateStrRange(headline, lowDateStr, highDateStr)]

	"""
	Way better than the previous function. Filters based on comparable datetime.date objects.
	"""
	@staticmethod
	def FilterHeadlinesByDtDate(headlineList, dtLow, dtHigh):
		print("Filtering "+str(len(headlineList))+" headlines by dtLow-dtHigh: "+str(dtLow)+" "+str(dtHigh))
		filtered = [headline for headline in headlineList if headline.IsInDateRange(dtLow, dtHigh)]
		print(str(len(filtered))+" headlines after date filtering.")
		return filtered

	"""
	 Same as FilterHeadlines, but a list of topic words may be passed, of which the returned headlines will
	contain one or more.
	"""
	@staticmethod
	def UnionFilterHeadlines(headlineList, topicList):
		filtered = []
		for headline in headlineList:
			if any(topic.lower() in headline.Headline.lower()+headline.Description.lower() for topic in topicList):
				filtered.append(headline)
	
		return filtered

	"""
	Given a list of headlines returned by some query, returns only those with unique
	values for @field (eg, their uri, to prevent double-counting, etc). Only the first
	headline with a unique value for @field will be preserved; be mindful of the order dependence.

	Note this function should only be used to eliminate redundancy of items that are the same, for instance duplicate items for the
	same headline. OTOH, say a bunch of different headlines all had the same date; uniquifying by data would result only one of the
	headlines being randomly selected (unfiltered) and the rest filtered.

	NOTE: Its probably much better to do this in the sql query, rather than in post-processing of results.
	"""
	@staticmethod
	def UniquifyHeadlines(headlineList,field):
		uniqVals = set()
		filteredList = []
	
		for headline in headlineList:
			value = headline.GetValue(field)
			if value not in uniqVals:
				filteredList.append(headline)
				uniqVals.add(value)

		return filteredList

	"""
	Uniquifies headlines by the @field value (eg, 'uri', for deduplication), but only within
	the scope of the same day.
	"""
	@staticmethod
	def UniquifyHeadlinesByDay(headlineList, field):
		uniqVals = set()
		filteredList = []

		print("Uniquifying "+str(len(headlineList))+" headlines...")
		for headline in headlineList:
			#store unique value as a tuple of (@field, date)
			value = (headline.GetValue(field), headline.DT.date())
			if value not in uniqVals:
				filteredList.append(headline)
				uniqVals.add(value)
		print(str(len(filteredList))+" headlines after uniquify by day.")

		return filteredList

	"""
	Initializes the headline db, then performs basic differential volumetric analyses. IOW, just compares quantity of content.

	This will be used to dig into overall coverage disparities, as well as type-based disparities (eg, # of opinions about
	Clinton, vs. Trump).

	For binning problems, note that its also possible to bin at high resolution, and then average by grouping together
	consecutive days, weeks, etc. Could also use moving exponential average, and so on.

	Volumetric questions:
		-overall disproportion of coverage, Trump v. Clinton, broken out by day, week, month (note that breaking out by day should
			solve all larger bins, by summing over ranges of days)

		-volumes, overlaid with major events

		-use of exclamatories in headlines '!'
		-use of connective words that describe latent sentiments? See Texas group

	NOTE: For sentiment analysis, consider not uniquifying headlines, or otherwise weighting headlines by their frequency/duration. Another
	good idea is to run metrics on only the top-10 highest ranked headlines, since these have highest impact. There are likely to be mathematical
	schemes by which to combine sentiment analysis with impact metrics like rank, duration, and so on, to lend a more accurate picture of sentiment.


	Interesting sentiment-mining idea: Using PMI metrics (see _buildPMIMatrix()), check for nearest neighbors of extremely positive/negative
	words. Grow outward, absorbing more neighbors into positive/negative clusters, using the discriminants to determine a relative
	measure of "nearness" wrt positive/negative groupings. Could use annealing.
	"""

	"""
	Currently only implements day, month, since these are the radix date format of archive-source
	string which looks like:  "Mon_Oct_10_03:49:27_UTC_2016"

	@resolution: day, month, dow (day of week)
	"""
	@staticmethod
	def _getDatePrefix(archiveSource, resolution):
		#get month and day from archive-source string
		month = archiveSource[4:7]
		day = archiveSource[8:10]
	
		if month == "Jan":
			month = "01"
		elif month == "Feb":
			month = "02"
		elif month == "Mar":
			month = "03"
		elif month == "Apr":
			month = "04"
		elif month == "May":
			month = "05"
		elif month == "Jun":
			month = "06"
		elif month == "Jul":
			month = "07"
		elif month == "Aug":
			month = "08"
		elif month == "Sep":
			month = "09"
		elif month == "Oct":
			month = "10"
		elif month == "Nov":
			month = "11"
		elif month == "Dec":
			month = "12"

		if resolution == "day":
			prefix = month+day
		elif resolution == "month":
			prefix = month
		elif resolution == "dow":
			dow = archiveSource[0:3]
			if dow == "Mon":
				prefix = "0"
			elif dow == "Tue":
				prefix = "1"
			elif dow == "Wed":
				prefix = "2"
			elif dow == "Thu":
				prefix = "3"
			elif dow == "Fri":
				prefix = "4"
			elif dow == "Sat":
				prefix = "5"
			elif dow == "Sun":
				prefix = "6"
			else:
				print("ERROR dow bin not found")
		else:
			print("ERROR resolution not found")

		return prefix

	"""
	Bins headlines by ISO Week number. See python isocalendar(). Using a direct mapping in this way is far more
	robust, but remember '53' is a valid week number. For instance, in 2016 Jan 1-3 were Fri/Sat/Sun, and hence
	have weeknum = 53; it was not until Jan 4th 2016 that the week-num restarted at 1.

	Note: Clearly the assumption is that this is for only a single year

	Returns: @weekBins, a sequential list of headlines binned by week; the 0th element are headlines for the first
	week in the year. Just index based, so there is no binding of each week's headlines to their date; just use the headlines
	themselves for that. The list will always be 53 items long.
	"""
	@staticmethod
	def BinHeadlinesByWeek(headlines):
		weekBins = [[] for i in range(0,54)] #see isocalendar format: 53 is valid

		for headline in headlines:
			#print("iso week: "+str(headline.IsoWeek))
			weekBins[headline.IsoWeek].append(headline)

		#print("len weekbins: "+str(len(weekBins)))
		return weekBins

	"""
	Given a list of headline objects, returns them binned by calendar day according to the uri prefix: 'uri': '/2016/06/18/...'
	For week bins, use BinByweek.

	Months lie in range 01-12; days-of-week range 0-6

	TODO: Rewrite this and all other date oriented predicate code using only python datetime and other builtin modules


	@headlines:  list of Headline objects
	@resolution: "day", "month", or "dow" (day of week). Determines the binning strategy. No weeks, since this would require converting calendar days
	into calendar weeks, which is weird.
	@year: an integer, eg 2016

	Returns: bins as a dict. The keys are the 'uri' headline field day prefixes, eg '/2016/06/18', the values are list of headlines.
	"""
	@staticmethod
	def BinHeadlinesByDate(headlines,resolution,year=2016):
		headlineDict = {}
	
		#first initialize the bins, per resolution
		if resolution == "day":
			#iterate all months, and days w/in months
			dt = datetime.date(year, 1, 1)
			dtEnd = datetime.date(year+1, 1, 1)
			delta = datetime.timedelta(days=1)
			while dt < dtEnd:
				dayBin = dt.strftime("%m%d")
				headlineDict[dayBin] = []
				dt += delta
		elif resolution == "month":
			for month in range(1,13):
				if month < 10:
					monthBin = "0"+str(month)
				else:
					monthBin = str(month)
				headlineDict[monthBin] = []
		elif resolution == "dow":
			#days of week are encoded as 0-6, representing mon-sun
			for day in range(0,7):
				headlineDict[str(day)] = []
		else:
			print("ERROR resolution not found in BinHeadlinesByDate(): "+resolution)

		#bin the headlines themselves
		for headline in headlines:
			datePrefix = _getDatePrefix(headline.ArchiveSource, resolution)
			headlineDict[datePrefix].append(headline)

		return headlineDict

	"""
	Many sentiment metrics only rely on direct co-occurrence between topics and signal terms,
	meaning only the signal terms from the full article text are needed. This fetches the
	article's FullText from the Articles table, where available, and extracts only the signal
	term hits, appending these to the FullText field of the Headline.

	@ignoredUrlSubsts: Substrings which, if detected, will cause a fulltext lookup to be skipped, such as for '/video/...' urls for which we expect no text for some orgs and articles.


	Returns: Nothing, the Headline objects in @headlines list are modified as described
	"""
	@staticmethod
	def AppendArticleFullTextSignalHits(headlines, orgDb, signalTerms, hostUrl="", ignoredUrlSubstrs=[]):
		dbMisses = 0
		hits = 0
		i = 0

		for headline in headlines:
			uri = headline.URI.strip()
		
			if not any(ignoredSubstr in uri for ignoredSubstr in ignoredUrlSubstrs):
				#print("WARNING: AppendArticleFullTextSignalHits hardcoded to www.politico.com; change as needed (code revision needed)")
				#HACK: TODO: Need to fix the uri standards for all snapshots; basically the schema and rules about uris, archiveSource, etc.
				if hostUrl in uri:
					uri = hostUrl+uri.split(hostUrl)[-1]
				#CHOPS '/index.html' from url!
				uri = uri.replace(".html","").replace("/index.html","").rstrip("/\\")
		
				#CHOP search, query, and pagination params: ?, #, etc
				if "?" in uri:
					uri = uri.split("?")[0]
				if "#" in uri:
					uri = uri.split("#")[0]

				#print("searching for: "+uri)
		
				#if hostUrl != "": #prepend host address
				#	uri = hostUrl + uri
				article = orgDb.FetchArticleByUrl(uri)
				if article is not None:
					signalHits = []
					for term in article.FullText.lower().split(" "):
						if term in signalTerms:
							signalHits.append(term)
					
					#print(uri+"SIGNAL HITS: "+str(signalHits))
					headline.FullText += " ".join(signalHits)
					hits += 1
				else:
					dbMisses += 1
					#print("Missed url: "+uri)
	
			i += 1
			if i % 50 == 49:
				print("\rUrl article fulltext Hits: "+str(hits)+"  Misses: "+str(dbMisses)+"   "+str(i)+" processed of "+str(len(headlines))+"     ",end="")

		print("ARTICLE FULL TEXT MISSES: "+str(dbMisses)+" of "+str(len(headlines))+" headlines")
		
	"""
	Checks is a word is NOT a member of a stopword set; if @validWords is not None,
	this instead checks if word IS a member of some positive set of words.
	"""
	@staticmethod
	def _isIncludedWord(w, stopwords=None, validWords=None):
		if validWords != None:
			return w in validWords
		else:
			return w not in stopwords

	"""
	A consistent worry is that things like sentiment metrics could end up being biased by differences in the coverage volume per
	each topic. One sanity check is to bin the headlines coarsely by timespan, then to randomly select only a subset of headlines
	from the larger topic bin for that month. This accounts for the time distribution of headline sets, and maximizes the amount of
	information available. Precisely, bin by some resolution (day, week, month), then for each bin one has a b1 and b2 on topic1 and
	topic2. Make these sets equal by random selections from the larger set, to make the two bins of equal size. Then return the union 
	of bins for each topic as the final result. Notice that for certain weeks this could reduce headlines for one topic, then reduce
	headline count on the other topic the next week, hence its sort of a mini-max scheme for making the sets equal. However, if one
	topic is reported on more often one week, one should probably treat the sentiment and its magnitude as reflecting the actual sentiment.


	Another strategy is a completely random one: randomly select articles from the larger of @set1 or @set2 until equal in size. For large
	headline sets, this strategy should work well, since any difference in selection per article data should be uniformly distributed.

	@strategy: 

	Returns: s1, s2, headline sets of equal size on separate topics
	"""
	@staticmethod
	def EqualifyHeadlineSets(set1, set2, strategy="uniform-random"):
		s1 = list()
		s2 = list()


		def _equalifySets(largerSet, smallerSet):
			randSet = list()
			l1 = list(largerSet)
			for i in range(len(smallerSet)):
				randSet.append(l1[random.randint(0,len(smallerSet))])		
			return randSet, list(smallerSet)

		#degenerate case
		if len(set1) == len(set2):
			return set1, set2

		if strategy == "uniform-random":
			if len(set1) > len(set2):
				s1, s2, = _equalifySets(set1, set2)
			else:
				s2, s1 = _equalifySets(set2, set1)

		return s1, s2

	"""
	Returns rate at which headlines on a given topic/candidate were the headline.
	"""
	@staticmethod
	def GetHeadlineCount(headlines):
		headlineCt = 0.0
		for headline in headlines:
			if headline.Rank == 0:
				headlineCt += 1
		return headlineCt

	"""
	Counts number of times headlines on a topic included either audio or an image.

	Decided this wasn't valid; almost every headline object has a thumbnail, even if its not displayed. Not sure where that info is.
	The banner/headline will always be the one displayed, so perhaps the page is organized such that the stories' thumbnails are displayed
	if they get rotated to the top position.

	@staticmethod
	def GetMultimediaCount(headlines):
		count = 0.0
		for headline in headlines:
			if "/video" in headline.URI or len(headline.Thumbnail) > 2:
				print("thumb: "+headline.Thumbnail)
				count += 1.0
		return count
	"""

	"""
	Counts number of times headlines on a topic included video.
	"""
	@staticmethod
	def GetVideoCount(headlines):
		count = 0.0
		for headline in headlines:
			if "/video" in headline.URI:
				count += 1.0
		return count


	#Just a wrapper around binning
	@staticmethod
	def BinHeadlinesByTimespan(headlines,dtLow,dtHigh,dtGrouping):
		if dtGrouping == "weekly":
			print("Binning headlines by week...")
			bins = DataTransformer.BetterBinHeadlinesByWeek(headlines, dtLow, dtHigh)
		elif dtGrouping == "monthly":
			print("Binning headlines by month...")
			bins = DataTransformer.BetterBinHeadlinesByMonth(headlines, dtLow, dtHigh)
		else:
			print("ERROR: date bin not implemented: %s. Use only weekly and monthly"%dtGrouping)

		return bins			

	"""
	Pass a list of headlines, and bin in monthly bins betwee dtLow and dtHigh, two datetime.date objects.

	@headlines: headline list, PRE FILTERED by dtLow/dtHigh
	@dtLow/dtHigh: high and low datetime filter boundaries; if None, the min/max dt in the headlines will be used

	Returns: A date-ordered list of tuples as ((month-int, year-int),[headlines...]) representing a month and values are lists of headlines for that month.
	"""
	@staticmethod
	def BetterBinHeadlinesByMonth(headlines, dtLow, dtHigh):

		if dtLow is None:
			dtLow  = _getHeadlinesDtMin(headlines)
		if dtHigh is None:
			dtHigh = _getHeadlinesDtMax(headlines)

		#sanity check: verify 
		for headline in headlines:
			if headline.DT.date() < dtLow:
				print("ERROR headline "+headline.URI+" < dtLow in BetterBinHeadlinesByMonth() dtLow="+str(dtLow))
				print("Headlines must be pre-filtered per dtLow/dtHigh")
				exit()
			elif headline.DT.date() > dtHigh:
				print("ERROR headline "+headline.URI+" > dtHigh in BetterBinHeadlinesByMonth() dtHigh="+str(dtHigh))
				print("Headlines must be pre-filtered per dtLow/dtHigh")
				exit()
	
		iterDate = datetime.date(dtLow.year, dtLow.month, dtLow.day)
		endDate = datetime.date(dtHigh.year, dtHigh.month, dtHigh.day)
	
		delta = datetime.timedelta(days=1)
		monthIndices = {}
		monthBins = []
		while iterDate <= endDate:
			monthKey = (iterDate.month, iterDate.year)
			if monthKey not in monthIndices.keys():
				monthBins.append((monthKey,[]))
				monthIndices[monthKey] = len(monthBins)-1
			iterDate += delta

		#fill the bins
		for headline in headlines:
			monthKey = (headline.DT.month, headline.DT.year)
			if monthKey in monthIndices.keys():
				index = monthIndices[monthKey]
				monthBins[index][1].append(headline)
			else:
				#inly should happen if @headlines was not pre-filtered by dtLow, dtHigh, as required
				print("WARNING headline not found in weekIndices in BetterBinHeadlinesByMonth() ???")
				print("Prefilter headlines by dtLow/dtHigh before calling.")

		return monthBins


	"""
	bins returns as ordered list of tuples (year-int,[headlines])
	"""
	@staticmethod
	def BinHeadlinesByYear(headlines):
		maxYear = datetime.MINYEAR
		minYear = datetime.MAXYEAR
	
		for headline in headlines:
			if headline.DT.year > maxYear:
				maxYear = headline.DT.year
			if headline.DT.year < minYear:
				minYear = headline.DT.year

		#create dict of integer year keys
		yearKeys = range(minYear,maxYear+1)
		bins = []
		yearIndex = {}
		for year in yearKeys:
			bins.append((year,[]))
			yearIndex[year] = bins[-1]
		
		for headline in headlines:
			yearIndex[headline.DT.year][1].append(headline)

		return bins

	"""
	bins headlines by week

	@headlines: headline list, FILTERED by dtLow/dtHigh
	@dthigh/dtLow: Datetime filtering boundaries; passing None for both will select the min/max from the headlines and just use that
	@trimEnds: if true, trim the leading/trailing empty bins from the week bins

	Returns bins ordered by key ((isoweek-int,year-int),[headlines]) as a list
	"""
	@staticmethod
	def BetterBinHeadlinesByWeek(headlines, dtLow, dtHigh, trimEnds=False):

		if dtLow is None:
			dtLow  = _getHeadlinesDtMin(headlines)
		if dtHigh is None:
			dtHigh = _getHeadlinesDtMax(headlines)

		#sanity check: verify 
		for headline in headlines:
			if headline.DT.date() < dtLow:
				print("ERROR headline "+headline.URI+" Dt < dtLow in BetterBinHeadlinesByWeek() dtLow="+str(dtLow))
				print("Headlines must be pre-filtered per dtLow/dtHigh")
				return []
			elif headline.DT.date() > dtHigh:
				print("ERROR headline "+headline.URI+" DT > dtHigh in BetterBinHeadlinesByWeek() dtHigh="+str(dtHigh))
				print("Headlines must be pre-filtered per dtLow/dtHigh")
				return []
	
		iterDate = datetime.date(dtLow.year, dtLow.month, dtLow.day)
		endDate = datetime.date(dtHigh.year, dtHigh.month, dtHigh.day)

		print("Binning "+str(len(headlines))+" headlines by week...")
	
		delta = datetime.timedelta(days=1)
		weekIndices = {}
		weekBins = []
		while iterDate <= endDate:
			weekKey = (iterDate.isocalendar()[1], iterDate.year)
			if weekKey not in weekIndices.keys():
				weekBins.append((weekKey,[]))
				weekIndices[weekKey] = len(weekBins)-1
			iterDate += delta

		#fill the bins
		for headline in headlines:
			weekKey = (headline.IsoWeek, headline.DT.year)
			if weekKey in weekIndices.keys():
				index = weekIndices[weekKey]
				weekBins[index][1].append(headline)
			else:
				#inly should happen if @headlines was not pre-filtered by dtLow, dtHigh, as required
				print("WARNING headline not found in weekIndices in BetterBinHeadlinesByWeek() ???")
				print("Prefilter headlines by dtLow/dtHigh before calling.")

		#two exceptions: isoweek is 52 or 53 for the last week of the year (53 is leap week), since it occurs in the new year
		if weekBins[0][0][0] == 52:
			weekBins.append(weekBins[0])
			weekBins = weekBins[1:]

		if weekBins[0][0][0] == 53:
			weekBins.append(weekBins[0])
			weekBins = weekBins[1:]


		"""
		#trim the leading and trailing empty bins
		if trimEnds:
			#trim the leading empty bins
			startIndex = -1
			i = 0
			while i < len(weekBins):
				if len(weekBins[i][1]) > 0:
					startIndex = i
				i+=1

			#error case: all bins empty
			if startIndex >= len(weekBins):
				print("ERROR passed trimEnds to BetterBinHeadlinesByWeek, but bins empty")
				return weekBins

			if startIndex > 0:
				#trim leading empty bins
				weekBins = weekBins[startIndex:]

			#trim the trailing empty bins
			endIndex = len(weekBins) - 1
			while endIndex >= 0 and len(weekBins[endIndex]) == 0:
				endIndex -= 1
			if endIndex > 0:
				weekBins = weekBins[:endIndex+1]
		"""

		#print("len weekbins: "+str(len(weekBins)))
		#print("week zero: "+str(len(weekBins[0][1])))
	
		return weekBins

	#utility for topical frequency analysis
	@staticmethod
	def _topicalAnalysisHeadlineFilter(db, primaryActorTerms, secondaryActorTerms, verbs, dtLow, dtHigh, uniqColumn):
		headlines = db.FetchHeadlinesByYear(fields=["headline","description"], targetStrs=primaryActorTerms, yearStr="2016")
		headlines += db.FetchHeadlinesByYear(fields=["headline","description"], targetStrs=primaryActorTerms, yearStr="2017")
		headlines = FilterHeadlinesByDtDate(headlines, dtLow, dtHigh)
		if len(uniqColumn) > 0:
			headlines = UniquifyHeadlinesByDay(headlines, uniqColumn)
		#AND-filter based on associate topics
		headlines = FilterHeadlinesInclusive(headlines, secondaryActorTerms)
		#filter based on action/verb terms
		headlines = FilterHeadlinesInclusive(headlines, verbs)
	
		#YOU NEED TO DO THIS TO HUMAN VERIFY RESULTS: false positives (think of false negatives too!!!)
		for headline in headlines:
			headline.PrintTerse()

		return headlines





