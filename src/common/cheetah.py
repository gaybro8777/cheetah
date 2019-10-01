
"""
From VecSent. This is all duplicated code, so maintain both copies appropriately.

"""

import gensim
from random import shuffle
import numpy as np
import traceback
from lexica import SentimentLexicon
from lexica import Lexicon

#A wrapper to make fasttext KeyedVector model look like a gensim Word2Vec model
class FastTextModelWrapper(object):
	def __init__(self, model):
		self.wv = model
		self.vector_size = model.vector_size

"""
Fasttext models can be loaded into gensim, although it aint clear how long this will last, or fasttext will overtake gensim
From the developer:
	'For .bin use: load_fasttext_format() (this typically contains full model with parameters, ngrams, etc).
	For .vec use: load_word2vec_format (this contains ONLY word-vectors -> no ngrams + you can't update an model).
	Note:: If you are facing issues with the memory or you are not able to load .bin models, then check the pyfasttext model for the same.'

Also, gensim.models.wrappers.FastText.load_word2vec_format is deprecated, and it cannot continue to be trained upon (in gensim, at least; surely it
can in fasttext). But it also sounds like bullshit: if vectors (models) can be loaded, they can be trained upon.

"""
def loadFastTextModel(modelPath):
	#for .vec models only; see header comment
	if modelPath.endswith(".vec"):
		print("Loading fasttext model from {}... this can take up to fifteen minutes...".format(modelPath))
		#model = gensim.models.wrappers.FastText.load_word2vec_format(modelPath, limit=100000)
		model = gensim.models.KeyedVectors.load_word2vec_format(modelPath, limit=100000)
		return FastTextModelWrapper(model)
	else:
		print("ERROR fasttext model must end in .vec. See loadFasttestModel()")
		return None

"""

"""
def loadCheetahModel(modelPath):
	print("Loading model for cheetah. WARNING: model path must contain 'fasttext' to load as fasttext. Default is word2vec.")
	if "fasttext" in modelPath.lower():
		return loadFastTextModel(modelPath)
	return gensim.models.Word2Vec.load(modelPath)

def sumCossim(sigTerms1, sigTerms2, model):
	"""
	Returns the net cossine similarity between two term sets using the term vectors in @model, and the number of term-misses in 
	@sigTerms1 and @sigTerms2. The misses must be returned so the caller can weight the score by term hits.
	"""
	st1 = [w for w in sigTerms1 if w in model.wv.vocab]
	st2 = [w for w in sigTerms2 if w in model.wv.vocab]
	#Track and at least output the number of terms missing from @model
	print("SumCossim(): num sigTerms1={}, {} after model filter. sigTerms2={}, {} after model filter.".format(len(sigTerms1), len(st1), len(sigTerms2), len(st2)))

	netSim = 0.0
	# cossim def: v1.dot(v2) / (|v1| * |v2|).  The norms can be cached and reused.
	for s1 in st1:
		s1Vec = model.wv[s1]
		s1Norm = np.linalg.norm(s1Vec)
		for s2 in st2:
			s2Vec = model.wv[s2]
			s2Norm = np.linalg.norm(s2Vec)
			netSim += (s1Vec.dot(s2Vec) / (s1Norm*s2Norm))

	sig1Misses = len(sigTerms1) - len(st1)
	sig2Misses = len(sigTerms2) - len(st2)

	return netSim, sig1Misses, sig2Misses

def netAlgebraicSentiment(queryTerms, sentLex, model, avgByHits=True):
	"""
	@queryTerms: A list of terms representing a single topic, e.g. ["dog", "canine"]
	@sentLex: A SentimentLexicon object
	@model: A cheetah model, a dumbly-named wrapper for a term vector model returned by loadCheetahModel()
	Given a list of topical terms, a SentimentLexicon, and a term-vector model, returns the net distance between
	@queryTerms and positive/negative sentiment as a single real-value. This is defined as the sum 
	similarity between @queryTerms and @sentLex.Positives, MINUS the similarity between @queryTerms and @sentLex.Negatives,
	where similarity function is dot-product.
	@weightByHits: If true, scores will be weighted by term hits in @model. For example, if topic t1 has two hits, and topic
	t2 has 30, clearly this will scale their net sentiment if not averaged. 

	The purpose of doing this is to analyze @model, not really @queryTerms nor @sentLex, even though they are function parameters. A
	vector-based language model may have been biased by its training data (in some cases its the point of one), so this gives a
	simple way of comparing that bias for different topics. For the most part this is "showing your work". I'm not yet sure how a model
	could be normalized w.r.t. some topics to 'un-bias' the model algebraically, but its an important topic.
	"""
	posSim, qMisses, posMisses = sumCossim(queryTerms, sentLex.Positives, model)
	negSim, qMisses, negMisses = sumCossim(queryTerms, sentLex.Negatives, model)
	
	if not avgByHits:
		return posSim - negSim

	posHits = len(sentLex.Positives) - posMisses
	negHits = len(sentLex.Negatives) - negMisses

	# Kludgiest normalization ever...
	return posSim / posHits - negSim / negHits

def netAlgebraicSentimentWrapper(queryTerms, sentimentFolder, model, avgByHits=True):
	sentLex = SentimentLexicon(sentFolder=sentimentFolder)
	return netAlgebraicSentiment(queryTerms, sentLex, model, avgByHits)

#Given a list of terms, rank all terms in @model by their sum cossine similary to these terms
def cossimLexiconGenerator(model, queryTerms):
	rankedTerms = []

	#get all query vectors and precompute their norms. no need to store any backward info, e.g. vec -> term
	qvecs = [(model.wv[qw], np.linalg.norm(model.wv[qw])) for qw in queryTerms if qw in model.wv.vocab]
	for w in model.wv.vocab:
		wvec = model.wv[w]
		wnorm = np.linalg.norm(model.wv[w])
		cossim = sum([wvec.dot(qtup[0]) / (qtup[1]*wnorm) for qtup in qvecs])
		rankedTerms.append( (w,cossim) )

	rankedTerms.sort(key=lambda t: t[1], reverse=True)

	return rankedTerms

def analysis3(model, headlines, sentLex):
	print("Analysis 3...")
	sentLex.Positives = [pw for pw in sentLex.Positives if pw in model.wv]
	sentLex.Negatives = [nw for nw in sentLex.Negatives if nw in model.wv]
	positives, negatives = sentLex.getBalancedSets()
	print("After balancing/filtering, lexicon contains {} positives, {} negatives".format(len(positives), len(negatives)))

	posNorms = dict() #pre-compute lexicon norms
	for posTerm in positives:
		posNorms[posTerm] = np.linalg.norm( model.wv[posTerm] )
	negNorms = dict() #pre-compute lexicon norms
	for negTerm in negatives:
		negNorms[negTerm] = np.linalg.norm( model.wv[negTerm] )

	worstScore = 0.0
	bestScore = 0.0
	worstHeadline = 0.0
	bestHeadline = 0.0
	avgVec = np.zeros(model.vector_size)
	try:
		for i, headline in enumerate(headlines):
			avgVec[:] = 0.0
			n = 0.0
			sumSimilarity = 0.0
			#average all words in doc into a single vector
			for word in headline.GetFullText().split():
				if word in model.wv.vocab:
					avgVec += model.wv[word]
					n += 1.0
			if n > 0.0:
				avgVec /= n
				avgVecNorm = np.linalg.norm(avgVec)
				#add all positive terms to sum-similarity...
				for posTerm in positives:
					posVec = model.wv[posTerm]
					posNorm = posNorms[posTerm]
					sumSimilarity += avgVec.dot(posVec.T) / (posNorm * avgVecNorm)
				#...and subtract all negative terms
				for negTerm in negatives:
					negVec = model.wv[negTerm]
					negNorm = negNorms[negTerm]
					sumSimilarity -= avgVec.dot(negVec.T) / (negNorm * avgVecNorm)

			headline.Attrib["cheetah"] = sumSimilarity
			if i % 10 == 9:
				print("\rSim: {:.3f}, document {} of {}      ".format(sumSimilarity, i, len(headlines)), end="")
	except:
		traceback.print_exc()

#@lexicon: A Lexicon object with a Words attribute
def analysis3_SingleLexicon(model, headlines, lexicon):
	print("Analysis 3 single lexicon...")
	signalTerms = [term for term in lexicon.Words if term in model.wv]
	print("After filtering by model vocab, lexicon contains {} terms".format(len(signalTerms)))

	norms = dict() #pre-compute lexicon norms
	for term in signalTerms:
		norms[term] = np.linalg.norm( model.wv[term] )

	avgVec = np.zeros(model.vector_size)
	try:
		for i, headline in enumerate(headlines):
			avgVec[:] = 0.0
			n = 0.0
			sumSimilarity = 0.0
			#average all words in doc into a single vector
			for word in headline.GetFullText().split():
				if word in model.wv.vocab:
					avgVec += model.wv[word]
					n += 1.0
			if n > 0.0:
				avgVec /= n
				avgVecNorm = np.linalg.norm(avgVec)
				#add all positive terms to sum-similarity...
				for sigTerm in signalTerms:
					sigVec = model.wv[sigTerm]
					sigNorm = norms[sigTerm]
					sumSimilarity += avgVec.dot(sigVec.T) / (sigNorm * avgVecNorm)

			headline.Attrib["cheetah_lex"] = sumSimilarity
			if i % 10 == 9:
				print("Sim: {:.3f}, object {} of {}".format(sumSimilarity, i, len(headlines)))
	except:
		traceback.print_exc()



