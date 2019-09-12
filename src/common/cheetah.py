
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
	positives, negatives = sentLex.getBalancedSets()
	positives = [pw for pw in positives if pw in model.wv]
	negatives = [nw for nw in negatives if nw in model.wv]
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
				print("Sim: {:.3f}, object {} of {}".format(sumSimilarity, i, len(headlines)))
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



