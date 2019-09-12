import random


"""
A class for a single signal lexicon: e.g., given a topic, measures its distance to some lexicon representing a topic/concept.
"""
class Lexicon(object):
	def __init__(self, path=None):
		if path is not None:
			#read the terms
			self.Words = self._loadTerms(path)
		else:
			self.Words = []
	def loadTerms(self, path):
		if "words" in path.lower():
			self.Words = self._loadTerms(path)
		else:
			print("ERROR lexicon file not found: "+path)
	def _loadTerms(self, fpath):
		with open(fpath, "r") as ifile:
			return [word.strip().lower() for word in ifile.readlines()]
		return []

"""
A class for a sentiment lexicon, of the sort defined by two Lexicon's: a positive term set, and a negative term set.
Provides some logic for balancing imbalanced sets when the positive/negative term sets are of unequal size, but
note that formally term balancing should be done by some method that weights by term frequency, or prior class probability
like in Bayesian stats.
"""
class SentimentLexicon(object):
	def __init__(self, sentFolder=None):
		if sentFolder is not None:
			#read the terms
			if sentFolder[-1] != "/":
				sentFolder = sentFolder + "/"
			self.Positives = self._loadTerms(sentFolder+"positive.txt")
			self.Negatives = self._loadTerms(sentFolder+"negative.txt")
		else:
			self.Positives = []
			self.Negatives = []
	def loadTerms(self, path):
		if "positive" in path.lower():
			self.Positives = self._loadTerms(path)
		elif "negative" in path.lower():
			self.Negatives = self._loadTerms(path)
		else:
			print("ERROR sentiment file not found: "+path)
	def _loadTerms(self, fpath):
		with open(fpath, "r") as ifile:
			return [word.strip().lower() for word in ifile.readlines()]
		return []
	def getBalancedSets(self):
		termLimit = min(len(self.Positives), len(self.Negatives)) #to balance the sets
		random.shuffle(self.Positives)
		random.shuffle(self.Negatives)
		return self.Positives[0:termLimit], self.Negatives[0:termLimit]

