"""
Remember: the only goal is to prove the method is effective, not to compete among imdb models.

Simple algorithm for evaluation on imdb sentiment classification dataset:
- import word model
- convert every document to doc vector
- calculate cheetah scores per document (this should be an interface/utility somewhere: input a model, document, and sentiment classes, and output score)
- regress +/- rating classification based on cheetah scores.

* Retry with sentiment classes derived from training data, and compare results.
* Retry with Word2Vec model trained, derive both document vecs and sentiment classes from it.


Other algorithms:

1	- Derive sentiment class vectors (e.g. 2,000 and 2,000 split), then assign a weight to the dot product of each and each document vector
	- This is explosive complexity, but then find ways to reduce/simplify algebraically

2	- Direct training: regress directly on ratings predictions to train word embeddings.
	- Options: 
		RNN -> doc vec -> prediction +/- (sequential modeling)
		Direct model of some form: backprop outputs directly to embeddings somehow. The trick here is definining the architecture.
			- backprop directly to multi-hot term vector representing document
			- backprop to n-grams somehow. This is interesting: could it be done w/out fixed 'n'?

"""

import os
import sys
sys.path.append('../common')
sys.path.append('../util')
sys.path.append('../model')

from lexica import SentimentLexicon
from ascii_text_normalizer import AsciiTextNormalizer
import sys
#import sklearn
import cheetah


sentimentLexiconPath = "../../lexica/sentiment/my_gensim/"
modelDir = "../../models/english/"
dataDir = "../../data/aclImdb/"


class Review(object):
	# Important note: I hacked this to satisfy the same interface as Headline in cheetah.py: FullText() and Attrib
	def __init__(self, source="", text="", binClass=0.0):
		self.Source = "" #file name or path
		self.GetFullText = "" # full text
		self.Vector = None
		self.Sentiment = 0.0
		self.Class = binClass # 1 or -1 binary class label
		self.Attrib = dict() # other data

# future
class ImdbDataset(object):

	def __init__(self, rootFolder):
		self._rootFolder = rootFolder
		self._data = self.Read(rootFolder)

	def __iter__(self):
		# Iterates all reviews in the dataset, test and train
		for review in self.GetTrainingSet():
			yield review
		for review in self.GetTestSet():
			yield review

	def GetTrainingSet():
		return self._data["train"]

	def GetTestSet():
		return self._data["test"]

	def Read(self, rootFolder):
		# Read in both the training and test set 
		testFolder = os.path.join(rootFolder,"test")
		trainFolder = os.path.join(rootFolder,"train")
		data = dict()
		data["train"] = dict()
		data["test"] = dict()

		data["train"]["pos"] = self._readSubset(os.path.join(trainFolder,"pos"), "pos")
		data["train"]["neg"] = self._readSubset(os.path.join(trainFolder,"neg"), "neg")
		data["test"]["pos"] = self._readSubset(os.path.join(testFolder,"pos"), "pos")
		data["test"]["neg"] = self._readSubset(os.path.join(testFolder,"neg"), "neg")

		return data

	def _readSubset(self, subFolder, sentKey):
		# subFolder: either train/ or test/ path
		# sentkey: "pos" or "neg"
		if sentKey not in ["neg","pos"]:
			raise Exception("sentKey must be pos or neg")
		return self._readReviews(subFolder, 1.0 if sentKey == "pos" else -1.0)

	def _readReviews(self, path, binClass):
		if binClass != 1.0 and binClass != -1.0:
			raise Exception("binary class must be either +1 or -1")

		print("Reading class={} from {}".format(binClass,path))
		reviews = []
		# Reads 
		for fname in os.listdir(path):	
			reviewPath = os.path.join(path, fname)
			with open(reviewPath, "r") as ifile:
				review = Review(source=reviewPath, text=ifile.read(), binClass=binClass)
				reviews.append(review)

		return reviews

def normalizeDataset(dataset):
	normalizer = AsciiTextNormalizer()

	for review in dataset:
		review.GetFullText = normalizer.NormalizeText(review.GetFullText, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)

def loadFastTextModel():
	modelPath = os.path.join(modelDir, "english/cc.en.300.vec")
	if not os.path.exists(modelPath):
		print("ERROR: model not found at {}. Select 'Download fasttext model' in main menu to download model before running analysis.".format(modelPath))
		return
	return cheetah.loadFastTextModel(modelPath=modelPath)

def loadSentimentLexicon(sentFolder):
	lexicon = cheetah.SentimentLexicon(sentFolder)
	normalizer = AsciiTextNormalizer()

	lexicon.Positives = [normalizer.NormalizeText(term, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True) for term in lexicon.Positives]
	lexicon.Negatives = [normalizer.NormalizeText(term, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True) for term in lexicon.Negatives]

	return lexicon

# Taken from cheetah
def loadFastTextModel():
	modelPath = os.path.join(modelDir, "english/cc.en.300.vec")
	if not os.path.exists(modelPath):
		raise Exception("ERROR: model not found at {}. Select 'Download fasttext model' in main menu to download model before running analysis.".format(modelPath))

	return cheetah.loadFastTextModel(modelPath=modelPath)

"""
# Taken from covid19 repo
def getAverageTermVec(terms, model):
	#Returns the average vector of all passed terms, via @model's term-vectors.
	# Warns if no model hits occur.
	avgVec = np.zeros(model.vector_size)
	hits = 0.0
	misses = 0
	#average all words into a single vector
	for word in terms:
		if word in model.wv.vocab:
			avgVec += model.wv[word]
			hits += 1.0
		else:
			misses += 1

	if hits == 0:
		print("WARNING: term list contains no model hits in getAverageVec: ", terms)

	if hits > 0:
		avgVec /= hits

	return avgVec


def vectorizeDataset(normalizedDataset, vecModel):
	print("Vectorizing dataset...")

	#From covid: neat pattern
	#normalizer = AsciiTextNormalizer()
	#def normalizeText(text):
	#	text = re.sub("([\(\[]).*?([\)\]])", "\g<1>\g<2>", text)
	#	return normalizer.NormalizeText(text, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)

	for review in normalizedDataset:
		docTerms = review.GetFullText.split()
		avgVec = getAverageTermVec(docTerms, vecModel)
		#TODO: serialize vector
		review.Vector = avgVec
"""

def cheetifyDataset(vectorizedDataset):
	# load sentiment lex
	sentLex = loadSentimentLexicon(sentimentLexiconPath)
	#TODO: stop words handling?
	model = loadFastTextModel()
	reviews = [review for review in vectorizedDataset]

	analysis3(model, reviews, sentLex)

	return vectorizedDataset

def oneDimCheetahLogisticRegression(dataset):
	# Given a dataset with cheetah scores assigned to all training vectors...
	# Run one-dimensional logistic regression against the scores to get the single weight (haha)
	# Find 
	# This is just for fun. It should actually work! Just iterate over different sentiment lexica generated from the training data.

	# Convert training data to one column "matrix"
	trainingData = dataset.GetTrainingSet()
	sentimentScores = np.matrix([review.Sentiment for review in trainingData])
	targets = 		  np.matrix([review.Class     for review in trainingData])

	model = sklearn.linear_model.LogisticRegression(penalty='l2', dual=False, tol=0.0001, C=1.0, fit_intercept=True, intercept_scaling=1, class_weight=None, random_state=None, solver='lbfgs', max_iter=100, multi_class='auto', verbose=0, warm_start=False, n_jobs=None, l1_ratio=None)
	model.fit()

	testInput   = np.matrix([review.Sentiment for review in testData])
	predicted   = model.predict(testInput)
	testTargets = np.matrix([review.Class     for review in testData])

	score = accuracy_score(predicted, ttestTargets)

	print("Score: ", score)


"""
- Read the dataset
- Normalize the dataset
- Read a model, sentiment lexicon
- Convert training set to vectors+targets
- Calculate cheetah values
- Regress with sklearn with 1d cheetah scores as independent variable

- Retry, using dataset-derived sentiment lexicon
- Retry, regressing directly on k-dimensional document vectors as independent variable
- Weird: stack based architecture? Read vector, push on stack or discard. Pop from stack, if two adjacent vectors (nearby words) are high-information, use them.
	- Use stack to implement a strategy of 1) discarding least-valuable information 2) fixed-size data representation
	Action space: can either 1) push information onto stack 2) discard information (e.g. stop words)
	Push entire sequence, discarding some info. Pop from sequence, regress only on vectors with relevant information.
	Hm, kinda novel. In some way, train the learner to retain/discard certain vectors from the document representation:
		e.g. "[negative term] AND [inverter like "not"] AND [other language] AND ... (expression is unbounded, since the learner learns what to include)
	Riff on the similarity with LSTM for a while, since they also learn-to-forget.

"""

dataset = ImdbDataset(dataDir)

















