import os
import json
import matplotlib.pyplot as plt
from lexica import Lexicon, SentimentLexicon
import cheetah
from data_transformer import DataTransformer


"""
Random scripts for transforming and presenting cheetah results.
"""

"""
Given a sequence of say, floats for some plot, and an integer k, this computes
the k-window average sequence of the same size as @seq. For the left and right ends,
the segments which may be less than k, a smaller avg is used: k-1 to the left of seq[k],
k-2 for left of seq[k-1], etc. So the end values will just converge to the actual values there.

A perferred option is to simply pass in a sequence for which you're interested in only the center len-2k
portion, such that the k-length ends can just be trimmed, such that all values are true radial averages of size k.

Returns: k-window smoothed sequence of @seq values
"""
def _kAverageSequence(seq,k):
	avgSeq = []
	for i in range(len(seq)):
		left = int(max(0, i-k/2))
		right = int(min(len(seq), i+k/2))	
		avgSeq.append(float(sum(seq[left:right])) / float(right-left+1))

	return avgSeq


def getColor(topics, colors, index):
	redTopics = {"progressive","progressives","dnc","dncs","liberal","liberals","democrat","democrats","clinton","hillary","clintons","hillarys","obama","obamas","barack","baracks"}
	blueTopics = {"conservative","conservatives","gop","gops","republican","republicans","rnc","rncs","donald","donalds","trump","trumps","romney","mitt","romneys"}

	#hack to preserve correspondence between conservative=red, liberal=blue, else returns random color
	if any([True for topic in topics if topic in redTopics]):
		color = "b"
	elif any([True for topic in topics if topic in blueTopics]):
		color = "r"
	else: #choose random color
		color = colors[index % len(colors)]

	return color

#assumes @headlines has already been analyzed by cheetah, with scores stored in @headline.cheetah
#Returns a single list of sum-scores for each time bin, along with the corresponding list of bin indices/names
def getCheetahScores(headlines, dtLow, dtHigh, dtGrouping, normalizeScores, cheetahKey="cheetah"):
	#single dim list
	netScores = []
	#plot weekly sentiment
	binKeys = []
	i = 0
	timeBins = DataTransformer.BinHeadlinesByTimespan(headlines, dtLow, dtHigh, dtGrouping)
	for timeBin in timeBins:
		binKeys.append(timeBin[0])
		netScore = sum([headline.Attrib[cheetahKey] for headline in timeBin[1]])
		if normalizeScores and len(timeBin[1]): # average score over headline count, instead or raw
			netScore /= float(len(timeBin[1]))
		netScores.append(netScore)

	return netScores, binKeys

def plotCheetahHistogram(resultCollection, asDensity=False, numBins=150, savePath=None, cheetahKey="cheetah"):
	"""
	Plots a histogram of cheetah sentiment values for a result collection.
	This could be extended to weight by social shares simply by using the @weights parameter of numpy.histogram
	@asDensity: If true, each plot will be normed, such that its integral is 1.0
	"""

	#get the max/min value to determine the range of the histogram over 
	maxValue = -100000000000
	minValue =  100000000000
	for result in resultCollection.QueryResults:
		for headline in result.Headlines:
			sent = headline.Attrib[cheetahKey]
			if sent > maxValue:
				maxValue = sent
			if sent < minValue:
				minValue = sent

	topics = []
	for result in resultCollection.QueryResults:
		sents = [headline.Attrib[cheetahKey] for headline in result.Headlines]
		plt.hist(sents, numBins, (minValue, maxValue), alpha=0.5, density=asDensity)
		if len(sents) > 0:
			avgSent = float(sum(sents)) / float(len(sents))
			plt.axvline(avgSent, color='k', linestyle='dashed', linewidth=1)
		topics.append(result.Topics[0])

	plt.title("Gross Cheetah Score 100-bin Histogram")
	plt.xlabel("Score")
	plt.ylabel("Frequency")
	plt.legend(topics, loc="best")
	if savePath is None:
		plt.show()
	else:
		plt.savefig(savePath)
		plt.clf()

	for result in resultCollection.QueryResults:
		sents = [headline.Attrib[cheetahKey] for headline in result.Headlines]
		weights = [headline.Attrib["share_count"] if "share_count" in headline.Attrib and headline.Attrib["share_count"] > 0 else 1 for headline in result.Headlines]
		plt.hist(sents, numBins, (minValue, maxValue), alpha=0.5, weights=weights, density=asDensity)

	plt.title("Gross Cheetah Score 100-bin Histogram, Share Weighted")
	plt.xlabel("Sentiment")
	plt.ylabel("Share Frequency")
	plt.legend(topics, loc="best")
	if savePath is None:
		plt.show()
	else:
		plt.savefig(savePath)
		plt.clf()

"""
Cheetah analysis

Remember to filter lexicon of topic/target terms. For example 'trump' is both a topic term and often a positive lexicon term.

@normalizeScores: If true, normalize topical scores by headline count for that topic
"""
def cheetahSentimentAnalysis(\
		resultCollections,\
		lexicon,\
		model,\
		dtLow,\
		dtHigh,\
		dtGrouping="weekly",\
		resultFolder=None,\
		useScoreWeight=False,\
		useSoftMatch=False,\
		normalizeScores=True):

	print("Running cheetah sentiment analysis. Remember to filter input lexicon of topic/target terms to prevent ambiguity, e.g. 'trump'=positive term and topic term.")

	#analyze all the headlines; the values are stored in headline.Attrib["cheetah"]
	for result in resultCollections[0].QueryResults:
		cheetah.analysis3(model, result.Headlines, lexicon)
	#re-save data for testing
	#print("Resaving cheetah data...")
	#ResultCollection.SaveCollections(resultCollections, "cheetah.json")

	#netScores outer-list indexed by topicIndex, inner lists indexed via binKeys
	netScores = []
	topicLists = []
	for result in resultCollections[0].QueryResults:
		topicScores, binKeys = getCheetahScores(result.Headlines, dtLow, dtHigh, dtGrouping, normalizeScores, cheetahKey="cheetah")
		netScores.append(topicScores)
		topicLists.append(result.Topics)

	#save the raw netscores; this provides direct reproducibility of the output values, e.g. for regression
	if resultFolder is not None:
		if resultFolder[-1] != os.sep:
			resultFolder += os.sep
		topics = "_".join([topicList[0] for topicList in topicLists])
		src = resultCollections[0].Name
		filePrefix = resultFolder+src+"_"+topics
		fileStr = filePrefix+"_cheetah_netscores.json"
		#dictify the scores, topics, date-labels
		dicts = []
		for i in range(len(netScores)):
			scores = netScores[i]
			topicList = topicLists[i]
			scoreDict = {"scores": scores, "topics": topicList}
			dicts.append(scoreDict)
		reproDict = dict()
		reproDict["binKeys"] = binKeys
		reproDict["output"] = dicts
		with open(fileStr, "w+") as jsonReproFile:
			jsonReproFile.write(json.dumps(reproDict, indent=2))

	#print gross values
	print("Gross Cheetah Sentiment Values ")
	grossSents = []
	for topicListIndex in range(len(topicLists)):
		grossSents.append(int(sum([t for t in netScores[topicListIndex]])))
		print(topicLists[topicListIndex][0]+": "+str(int(sum([t for t in netScores[topicListIndex]]))))

	#plot raw pmi values
	colors = ["r","b","g","c","m","y","k"]
	legendLabels = []
	xs = [i for i in range(len(netScores[0]))]
	#plot each topic
	for topicIndex in range(len(topicLists)):
		color = getColor(topicLists[topicIndex], colors, topicIndex)
		plt.plot(xs, [t for t in netScores[topicIndex]], color=color)
		grossStr = str(grossSents[topicIndex])
		if grossSents[topicIndex] > 0:
			grossStr = "+" + grossStr
		legendLabels.append(topicLists[topicIndex][0]+" "+grossStr)
		
	xlabels = [str(binKey[0])+"-"+str(binKey[1]) for binKey in binKeys]
	#print("LABELS: "+str(xlabels))
	xlabels = [xlabels[i] for i in range(len(xlabels)) if i % 4 == 0]
	xticks = [i for i in range(len(binKeys)) if i % 4 == 0]
	#print("LABELS: "+str(xlabels))
	#time.sleep(30)
	if dtGrouping == "weekly":
		xAxisLabel="ISO Week"
	elif dtGrouping == "monthly":
		xAxisLabel = "Month" 

	plt.xticks(xticks, xlabels, rotation= 60)
	plt.title("Gross Cheetah Sentiment")
	plt.xlabel(xAxisLabel)
	plt.legend(legendLabels, loc="best")
	plt.grid()
	if resultFolder is not None:
		if useScoreWeight:
			plt.savefig(filePrefix+"_expected_cheetah_raw_"+dtGrouping+".png")
		else:
			plt.savefig(filePrefix+"_cheetah_raw_"+dtGrouping+".png")
	plt.show()
	#plt.clf()
	
	#smooth values over a k-bin window
	k = 2
	legendLabels = []
	meanScores = [_kAverageSequence([t for t in netScores[topicIndex]], k) for topicIndex in range(len(topicLists))]
	xs = [i for i in range(len(meanScores[0]))]
	#plot each topic
	for topicIndex in range(len(topicLists)):
		color = getColor(topicLists[topicIndex], colors, topicIndex)
		plt.plot(xs, meanScores[topicIndex], color=color)
		grossStr = str(grossSents[topicIndex])
		if grossSents[topicIndex] > 0:
			grossStr = "+" + grossStr
		legendLabels.append(topicLists[topicIndex][0]+" "+grossStr)

	plt.xticks(xticks, xlabels, rotation = 60)
	plt.title("Gross Cheetah Sentiment, "+str(k)+"-Bin Average")
	plt.legend(legendLabels, loc="best")
	plt.xlabel(xAxisLabel)
	plt.grid()
	if resultFolder is not None:
		if useScoreWeight:
			plt.savefig(filePrefix+"_expected_cheetah_smoothed_"+str(k)+"bin_avg.png")
		else:
			plt.savefig(filePrefix+"_cheetah_smoothed_"+str(k)+"bin_avg.png")
	plt.show()
	#plt.clf()

	#plot sentiment histogram
	plotCheetahHistogram(resultCollections[0], False, 75, filePrefix+"_cheetah_hist_75bin.png")
	plotCheetahHistogram(resultCollections[0], True, 75, filePrefix+"_cheetah_hist_as_density_75bin.png")

	return meanScores

"""
Cheetah analysis, using a single lexicon as input. This is used to analyze a topic or set of topics with respect to a single lexicon.
"""
def cheetahLexicalAnalysis(resultCollections, lexiconPath, model, dtLow, dtHigh, dtGrouping="weekly", resultFolder=None, useScoreWeight=False, useSoftMatch=False):
	#Topic terms are removed from sentiment lexica in GetNetPPmiSentimentScores..()
	lexicon = Lexicon(lexiconPath)
	cheetahKey = "cheetah_lex"

	#analyze all the headlines; the values are stored in headline.Attrib["cheetah"]
	for result in resultCollections[0].QueryResults:
		cheetah.analysis3_SingleLexicon(model, result.Headlines, lexicon)
	#re-save data for testing
	#print("Resaving cheetah data...")
	#ResultCollection.SaveCollections(resultCollections, "cheetah.json")
	#print("here")
	#time.sleep(5)

	#netScores outer-list indexed by topicIndex, inner lists indexed via binKeys
	netScores = []
	topicLists = []
	for result in resultCollections[0].QueryResults:
		topicScores, binKeys = getCheetahScores(result.Headlines, dtLow, dtHigh, dtGrouping, useScoreWeight, useSoftMatch, cheetahKey=cheetahKey)
		netScores.append(topicScores)
		topicLists.append(result.Topics)

	#save the raw netscores; this provides direct reproducibility of the output values, e.g. for regression
	if resultFolder is not None:
		if resultFolder[-1] != os.sep:
			resultFolder += os.sep
		topics = "_".join([topicList[0] for topicList in topicLists])
		src = resultCollections[0].Name
		filePrefix = resultFolder+src+"_"+topics
		fileStr = filePrefix+"_cheetah_lex_netscores.json"
		#dictify the scores, topics, date-labels
		dicts = []
		print(str(netScores))
		print(str(topicLists))
		for i in range(len(netScores)):
			scores = netScores[i]
			topicList = topicLists[i]
			scoreDict = {"scores": scores, "topics": topicList}
			dicts.append(scoreDict)
		reproDict = dict()
		reproDict["binKeys"] = binKeys
		reproDict["output"] = dicts
		with open(fileStr, "w+") as jsonReproFile:
			jsonReproFile.write(json.dumps(reproDict, indent=2))

	#print gross values
	print("Gross Cheetah Lexicon Values ")
	grossSents = []
	for topicListIndex in range(len(topicLists)):
		grossSents.append(int(sum([t for t in netScores[topicListIndex]])))
		print(topicLists[topicListIndex][0]+": "+str(int(sum([t for t in netScores[topicListIndex]]))))

	#plot raw pmi values
	colors = ["r","b","g","c","m","y","k"]
	legendLabels = []
	xs = [i for i in range(len(netScores[0]))]
	#plot each topic
	for topicIndex in range(len(topicLists)):
		color = getColor(topicLists[topicIndex], colors, topicIndex)
		plt.plot(xs, [t for t in netScores[topicIndex]], color=color)
		grossStr = str(grossSents[topicIndex])
		if grossSents[topicIndex] > 0:
			grossStr = "+" + grossStr
		legendLabels.append(topicLists[topicIndex][0]+" "+grossStr)
		
	xlabels = [str(binKey[0])+"-"+str(binKey[1]) for binKey in binKeys]
	#print("LABELS: "+str(xlabels))
	xlabels = [xlabels[i] for i in range(len(xlabels)) if i % 4 == 0]
	xticks = [i for i in range(len(binKeys)) if i % 4 == 0]
	#print("LABELS: "+str(xlabels))
	#time.sleep(30)
	if dtGrouping == "weekly":
		xAxisLabel="ISO Week"
	elif dtGrouping == "monthly":
		xAxisLabel = "Month" 

	plt.xticks(xticks, xlabels, rotation= 60)
	plt.title("Gross Cheetah Score")
	plt.xlabel(xAxisLabel)
	plt.legend(legendLabels, loc="best")
	plt.grid()
	if resultFolder is not None:
		if useScoreWeight:
			plt.savefig(filePrefix+"_expected_cheetah_lex_raw_"+dtGrouping+".png")
		else:
			plt.savefig(filePrefix+"_cheetah_lex_raw_"+dtGrouping+".png")
	#plt.show()
	plt.clf()
	
	#smooth values over a k-bin window
	k = 2
	legendLabels = []
	meanScores = [_kAverageSequence([t for t in netScores[topicIndex]], k) for topicIndex in range(len(topicLists))]
	xs = [i for i in range(len(meanScores[0]))]
	#plot each topic
	for topicIndex in range(len(topicLists)):
		color = getColor(topicLists[topicIndex], colors, topicIndex)
		plt.plot(xs, meanScores[topicIndex], color=color)
		grossStr = str(grossSents[topicIndex])
		if grossSents[topicIndex] > 0:
			grossStr = "+" + grossStr
		legendLabels.append(topicLists[topicIndex][0]+" "+grossStr)

	plt.xticks(xticks, xlabels, rotation = 60)
	plt.title("Gross Cheetah Score, "+str(k)+"-Bin Average")
	plt.legend(legendLabels, loc="best")
	plt.xlabel(xAxisLabel)
	plt.grid()
	if resultFolder is not None:
		if useScoreWeight:
			plt.savefig(filePrefix+"_expected_cheetah_lex_smoothed_"+str(k)+"bin_avg.png")
		else:
			plt.savefig(filePrefix+"_cheetah_lex_smoothed_"+str(k)+"bin_avg.png")
	#plt.show()
	plt.clf()

	#plot sentiment histogram
	plotCheetahHistogram(resultCollections[0], False, 75, filePrefix+"_cheetah_lex_hist_75bin.png", cheetahKey)
	plotCheetahHistogram(resultCollections[0], True, 75, filePrefix+"_cheetah_lex_hist_as_density_75bin.png", cheetahKey)

	return meanScores
