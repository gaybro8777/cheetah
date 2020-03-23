"""
A wrapper around a word2vec implementation for experimental usage only, just playing
around with different implementations for evaluation.

The code libraries used are the property of their respective authors.


***GenSim implements a bunch of nice training data stream objects, for training from files of line-based
training sequences (sentences), and so forth. Moving stuff into ABLE/Sentinel could be as easy as
inheriting from those classes to implement ones that would read and preprocess headline objects
and so on. Use good practices and recognize that most of the etl boilerplate can probably be covered
via stream classes that perform all that internal logic. Think oop.
"""

import sys
sys.path.append('../common')
sys.path.append('../util')

from lexica import Lexicon
from ascii_text_normalizer import AsciiTextNormalizer

import json
import re
import os
import gensim
import traceback
import numpy as np


"""
I generate training sequence for word2vec based on sentences in the Covid dataset: https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/tasks
Each json object in the dataset is a research paper, each containing an id, abstract, list of authors, body text (as a sequence of 'text' sentences with citation
metadata), a full list of citations (each with a one-sentence description), and some other metadata.

This stream just decomposes the document into a seequence of sentences: the title, abstract, authors, and body text.

"""

class CovidDocument(object):
	# Just a wrapper for the covid dataset documents..
	# NOTE: I'm assuming the documents all have the same schema
	# TODO: vector serialization. Clients should be able to access raw numpy vectors as soon as this is read. (What are those inverse methods
	# again, used by json.loads and json.dumps? __dict__ and __str__???
	def __init__(self, d):
		"""
		@d: A dictionary parsed from a covid-dataset json document using json.loads()
		"""
		self._dict = d

	# TODO: make these fields instead of functions; add throw/catches for missing fields/keys
	def Abstract(self):
		abstractList = self._dict["abstract"]
		if len(abstractList) > 0:
			return abstractList[0]["text"]
		return ""

	def AddRootKvp(self, key, value):
		# Add a key/value to the root-level of the document object dict
		# @value must be encoded as a string (or must implement __str__())
		self._dict[key] = value

	def NormalizeText(self, textNormalizationFunc):
		#@normalizer: the text normalizer
		# NOTE: This only normalizes the text fields of the document, not the authors, etc.

		# normalize the title
		self._dict["metadata"]["title"] = textNormalizationFunc( self._dict["metadata"]["title"] )

		#normalize the abstract(s) (papers seem to only have 0 or 1, though it is stored as a list)
		abstracts = self._dict["abstract"]
		if len(abstracts) > 0:
			for abstract_ in abstracts:
				abstract_["text"] = textNormalizationFunc( abstract_["text"] )

		# normalize the body text
		for textObject in self._dict["body_text"]:
			textObject["text"] = textNormalizationFunc( textObject["text"] )

	def DocVector(self):
		if not "vector" in self._dict:
			return None
		return self._dict["vector"]

	def Id(self):
		return self._dict["paper_id"]

	def Title(self):
		return self._dict["metadata"]["title"]

	def BodyText(self):
		return " ".join([textObject["text"] for textObject in self._dict["body_text"]])
		
	def Authors(self):
		raise Exception("Not implemented")

	def FullText(self):
		# The FullText is just the concatenation of the title, abstract, and body text, delimited by '. ' to facilitate sentence breaking.
		return ". ".join([self.Title(), self.Abstract(), self.BodyText()])

	def WordSequence(self):
		return [word for sentence in self.FullText().split(".") for word in sentence.split()]

	def AuthorList(self):
		raise Exception("not implemented")

	def __iter__(self):
		for sentence in self.FullText():
			sentence = sentence.strip()
			if len(sentence) > 3:
				yield sentence

	def ToJson(self):
		return json.dumps(self._dict)

	@staticmethod
	def TryParse(jsonString):
		# Parses a CovidDocument from its json representation.
		# Returns <bool, CovidDocument> tuple. If the bool is true, parse succeeded and CovidDocument is not None; if false, then the parse
		# failed and document is None.
		success = False
		try:
			docDict = json.loads(jsonString)
			doc = CovidDocument(docDict)
			success = True
		except:
			print("Failed to parse string: "+jsonString[0:500]+"...")
			traceback.print_exc()
			doc = None

		return success, doc

class CovidDataset(object):
	def __init__(self, dataDir):
		self._dataDir = dataDir

	def __iter__(self):
		"""
		Notes: Normalization will be difficult for the following reasons:
			* utf in text: "Calmette-Gu\u00e9rin"
			* weird academic symbols (not too bad)
			* citations within the text: all of these are contained in brackets []
			* 

		- Read the file
		- Parse it into an object from json string
		
		"""
		
		for fpath in self._getDataFilePaths():
			with open(fpath, "r", encoding="utf-8") as jsonFile:
				parseSucceeded, doc = CovidDocument.TryParse( jsonFile.read() )
				if parseSucceeded:
					yield doc
				else:
					print("Failed to parse document from ", fpath)

	def _getDataFilePaths(self):
		return [os.path.join(self._dataDir, fname) for fname in os.listdir(self._dataDir)]

class CovidDocumentStream(object):
	def __init__(self, dataDir, limit, filterStopWords=True):
		"""
		@dataset: An iterable CovidDataset
		@limit: The number of sequences to generate before terminating the stream. If -1, then no limit (entire file).
		"""
		self._filterStopWords = filterStopWords
		self._stopWords = self._loadStopWords()
		self._dataset = CovidDataset(dataDir)
		self._limit = limit
		self._normalizer = AsciiTextNormalizer()

	def _loadStopWords(self):
		normalizer = AsciiTextNormalizer()
		lexicaDir = "../../lexica/"
		stopPath = os.path.join(lexicaDir, "stop/stopwords.txt")
		stopLex = Lexicon(stopPath)
		return [normalizer.NormalizeText(word, filterNonAlphaNum=True, deleteFiltered=True, lowercase=True).strip() for word in stopLex.Words]

	def _stripCitations(self, text):
		"""
		Citations are stored in the text as "blah [1,2,3] blah".
		This removes all text within non-nested square brackets, and the brackets themselves.
		"""
		return re.sub("([\(\[]).*?([\)\]])", "\g<1>\g<2>", text)

	def _normalizeSentenceDelimiters(self, text):
		# Just standardizes sentence-delimiting punctuation to a single character
		return text.replace("!",".").replace("?",".").replace(";",".")

	def _normalizeText(self, text):
		"""
		Public utility for normalizing text. A covid document has its own definition for text-normalization, so this belongs here
		or as class method.

		Normalization rules:
			casing: lowercasing is used
			utf8 characters: I'm thinking of just stripping these for simplicity. I don't know of any case they must be preserved, except fancy names of fancy authors.
			punct: in progress. This will be policy based.
				* leave periods
				* convert hyphens to single space?
				* 
			numbers: as much as possible, these must be preserved since many scientific names include numbers.
			citations: anything within brackets is removed, e.g. "abc[22]def" -> "abcdef"
		"""
		text = self._normalizeSentenceDelimiters(text)
		text = self._stripCitations(text)
		return self._normalizer.NormalizeText(text, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)

	def _dropStopWords(self, text):
		# TODO: This is extremely slow: for every character in string, lookup in stopwords
		# 1) Find an algorithmic way to do this; e.g. pre-prepocessing
		# 2) Use regex or other faster method
		return " ".join([term for term in text.split() if term not in self._stopWords])

	def __iter__(self):
		"""
		Iterates the covid dataset documents' sentences, applying text-normalization to each one, e.g.:

			for doc in dataset:
				for sentence in doc:
					yield normalize(sentence)

		Notes: Normalization will be difficult for the following reasons:
			* utf in text: "Calmette-Gu\u00e9rin"
			* weird academic symbols (not too bad)
			* citations within the text: all of these are contained in brackets []
			* 

		- Read the file
		- Parse it into an object from json string
		
		"""
		docCount = 0
		for doc in self._dataset:
			fullText = doc.FullText()
			fullText = self._normalizeText(fullText)
			if self._filterStopWords:
				fullText = self._dropStopWords(fullText)

			for i, sentence in enumerate(fullText.split(".")):
				#print(seq)
				if len(sentence) > 2 and (self._limit < 0 or i < self._limit):
					yield sentence
			docCount += 1
			if docCount % 10 == 9:
				print("Doc count: {}     \r".format(docCount), end="")

def loadVectorModel(modelPath):
	#loads Word2Vec model; only w2v models are currently supported
	if not (modelPath.endswith(".vec") or modelPath.endswith(".w2v")):
		raise Exception("Only gensim/word2vec models are currently supported. Model path must end with '.vec'")
	return gensim.models.Word2Vec.load(modelPath)

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
		print("WARNING: term list contains no model hits in getAverageVec: ",terms)

	# TODO: hit count is very poor, about 10%
	#print("Hits/misses: ",hits,misses)

	if hits > 0:
		avgVec /= hits

	return avgVec

def vectorizeDataset(dataDir, vecModel):
	# NOTE: The returned dataset will have its text normalized.
	# Stores average vector in each document, normalizes each doc, and stores this modified dataset.
	normalizer = AsciiTextNormalizer()

	#TODO: add stopword removal

	dataset = CovidDataset(dataDir)
	for doc in dataset:
		#normalize the document; this must be done consistently to maximize lookup hits; e.g. query "Foo" "foo" or "'fOo'" should ideally resolve to the term 'foo'.
		doc.NormalizeText(lambda text: normalizer.NormalizeText(text, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True))
		docTerms = doc.WordSequence()
		avgVec = getAverageTermVec(docTerms, vecModel)
		#TODO: serialize vector
		doc.AddRootKvp("vector", avgVec)

	#TODO: persist vectorized dataset? Do after gain confidence in doc-search
	return dataset

def isEmptyDir(dirPath):
	return len(os.listdir(dirPath)) == 0

def persistDataset(dataset, outputDir):
	# TODO/NOTE: This only normalizes the text in the dataset.
	if not isEmptyDir(outputDir):
		print("Clear output dir before attempting to persist dataset. Dataset not stored to "+outputDir)
		return

	for doc in dataset:
		docPath = os.path.join(outputDir, doc.Id()+".json")
		with open(docPath, "w+") as jsonFile:
			jsonFile.write( doc.ToJson() )

def buildWordVectorModel(dataDir, savePath=None):
	#**************************************************************************************************************************************
	#A wrapper that just hardcodes params used in VecSent project. These have hyper-parameters have not been optimized, they are just standard w2v params.
	limit=-1 #iterates all sequences; no cut-off
	vecSize=350
	numIterations=10
	minTermFrequency=1
	windowSize=3
	workers=1
	model="SKIPGRAM"
	#**************************************************************************************************************************************
	seqStream = CovidDocumentStream(dataDir, limit, filterStopWords=True)
	print("Building word-to-vec word-vector model...")
	vecModel = gensim.models.Word2Vec(seqStream, size=vecSize, window=windowSize, iter=numIterations, min_count=minTermFrequency, workers=workers, sg=(model == "SKIPGRAM" or model == "SKIP"))

	if savePath is not None:
		vecModel.save(savePath)

	return vecModel

def userQuery(normalizer, model):
	terms = input("Enter comma-separated search terms (case-insensitive): ").lower().split(",")
	#TODO: normalize query, filter non-model terms, make sure any query terms remain
	print("Normalized query terms: ", terms)
	return terms

def scoreDoc(queryVec, queryVecNorm, doc):
	docVec = doc.DocVector()
	# TODO: precompute the norms; this calculates them for every query
	docVecNorm = np.linalg.norm(docVec)
	# cossim the document vector and query vector
	return docVec.dot(queryVec) / (queryVecNorm * docVecNorm)

def runQuery(queryTerms, dataset, model):
	# Returns results as sorted list of (doc, similarity) tuples
	queryVec = getAverageTermVec(queryTerms, model)
	queryVecNorm = np.linalg.norm(queryVec)
	scoredDocs = [(doc, scoreDoc(queryVec, queryVecNorm, doc)) for doc in dataset]
	return sorted(scoredDocs, key=lambda t: t[1])

def main():
	# Train a word-2-vec model on covid-dataset, persist it.
	# Convert dataset to vectorized form
	# Query it

	#TODO: stopwords
	dataDir = "../../../covid/dataset/comm_use_subset/"
	newDataDir = "../../../covid/dataset/normalized_vec_dataset/"
	vecModel = buildWordVectorModel(dataDir, "./covid_temp.w2v")
	# TODO: this is temporary. Break out training and search paths
	#vecModel = loadVectorModel("../../models/covid/400d_iter10_window3_sg.w2v")
	dataset = vectorizeDataset(dataDir, vecModel)
	persistDataset(dataset, newDataDir)
	normalizer = AsciiTextNormalizer()

	while True:
		query = userQuery(normalizer, vecModel)
		query = [normalizer.NormalizeText(queryTerm) for queryTerm in query]
		results = runQuery(query, dataset, vecModel)
		print(str(results[0:100]))

if __name__ == "__main__":
	main()




