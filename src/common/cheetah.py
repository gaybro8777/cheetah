
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
		print("Loading fasttext model from {}... this can take several seconds to a few minutes...".format(modelPath))
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

def buildVectorCache(terms, vecModel):
	"""
	obsolete
	@terms: some terms to cache, e.g. ones we will repeatedly calculate/lookup like signal/sentiment terms
	@vecModel: A word2vec model with a .wv attribute 
	Builds and returns a dictionary mapping term strings to vector 2-ples. The first member of the tuple is
	the term's vector, and the second member is its norm. Caching these is more efficient
	for lookups and also since norms are repeatedly calculated for the same terms otherwise.
	"""
	# maps term keys to vector 2-ples as: term -> (termVec, termNorm)
	cache = dict() #pre-compute term vector norms and store vectors for faster lookups
	for term in terms:
		vec = vecModel.wv[term]
		vecNorm = np.linalg.norm(vec)
		cache[term] = (vec, vecNorm)
	return cache

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

def cheetifyHeadline_singleLex_optimized(headline, avgVec, sumUnitVec, model):
	"""
	The single-lexicon counterpart to cheetifyHeadline_optimized (see that func's header).
	NOTE: Single lexicon analyses are somewhat exploratory, since if you plot their values on a time series for instance,
	lower values ambiguously mean both less-information and/or lower scores. Both methods could use a method
	to improve on this property.
	"""
	avgVec[:] = 0.0
	n = 0.0
	sumSimilarity = 0.0 # TODO: Could instead return NaN for no-information, since zero is ambiguous with an actual score of zero
	#average all words in doc into a single vector
	for word in headline.GetFullText().split():
		if word in model.wv.vocab:
			avgVec += model.wv[word]
			n += 1.0

	if n > 0.0:
		avgVec /= n
		avgVecNorm = np.linalg.norm(avgVec)
		sumSimilarity = avgVec.dot(sumUnitVec) / avgVecNorm

	headline.Attrib["cheetah_lex"] = sumSimilarity
	return sumSimilarity

def cheetifyHeadline_optimized(headline, avgVec, sumPosUnitVec, sumNegUnitVec, model):
	"""
	As shown in src/util/test/sum_of_dot_products, the inner summation over cosine similarity factors such
	that the cheetah sentiment can be calculated by simply taking the dot product of the document's average
	term-vector and the sum signal norm vectors.
	That is:
		-get the average document term vector, v_avg
		-pre-calculate the sum-of-unit vectors for the signal lexica: v_sig = Sigma[ v / |v| ]
		-return (v_avg dot v_sig) / |v_avg|
	Note, that's the gist, but there may be errors in this description. But its mathematically sound, since
	a double sum over cosine similarities factors to a far more efficient form than actually calculating the
	full sum, since the signal lexica sum-of-norm vector can be pre-computed and re-used. 
	Or, just do the math...
	"""
	avgVec[:] = 0.0
	n = 0.0
	sumSimilarity = 0.0 # TODO: Could instead return NaN for no-information, since zero is ambiguous with an actual score of zero
	#average all words in doc into a single vector
	for word in headline.GetFullText().split():
		if word in model.wv.vocab:
			avgVec += model.wv[word]
			n += 1.0

	if n > 0.0:
		avgVec /= n
		avgVecNorm = np.linalg.norm(avgVec)
		sumSimilarity = (avgVec.dot(sumPosUnitVec) - avgVec.dot(sumNegUnitVec)) / avgVecNorm

	headline.Attrib["cheetah"] = sumSimilarity
	return sumSimilarity

"""
# OBSOLETE: used optimized version instead; much of the math algebraically factors to a much simpler, faster form.
# Leaving this here for reference only.
def cheetifyHeadline(headline, avgVec, posCache, negCache, model):
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
		#add all positive term vectors to sum-similarity...
		for posVec, posNorm in posCache:
			sumSimilarity += (avgVec.dot(posVec.T) / posNorm)
		#...and subtract all negative term vectors
		for negVec, negNorm in negCache:
			sumSimilarity -= (avgVec.dot(negVec.T) / negNorm)
		# Divide the sum-similarity by average vector norm.
		# This is an optimization, since the cosine-similarity in the above terms would have this in every denominator above, e.g. (avgVec.dot(posVec.T) / posNorm * avgVecNorm).
		# But since it is in every term of the sums above, it factors out.
		sumSimilarity /= avgVecNorm

	headline.Attrib["cheetah"] = sumSimilarity
	return sumSimilarity
"""

def filterLex(model, lexicon):
	return [w for w in lexicon if w in model.wv]

def filterSentLex(model, sentLex):
	"""
	Filters sentiment lexicon so it includes only terms in the model. Note few/no words will be removed
	if the lexicon was generated from the model itself.
	"""
	sentLex.Positives = filterLex(model, sentLex.Positives)
	sentLex.Negatives = filterLex(model, sentLex.Negatives)
	# Re-balance after filtering through model lexicon
	return sentLex.getBalancedSets()

def getSumUnitVec(model, words):
	"""
	Returns the sum of unit vectors from the passed model for some lexica.
	NOTE: This is not a unit vector, it is a sum of unit vectors.
	"""
	sumNormVec = np.zeros(model.vector_size)
	for w in words:
		vw = model.wv[w]
		sumNormVec += (vw / np.linalg.norm(vw))
	return sumNormVec

def analysis3(model, headlines, sentLex):
	print("Analysis 3...")
	
	sentLex = filterSentLex(model, sentLex)
	avgVec = np.zeros(model.vector_size)
	sumPosUnitVec = getSumUnitVec(model, sentLex.Positives)
	sumNegUnitVec = getSumUnitVec(model, sentLex.Negatives)

	try:
		for i, headline in enumerate(headlines):
			sumSimilarity = cheetifyHeadline_optimized(headline, avgVec, sumPosUnitVec, sumNegUnitVec, model)
			if i % 10000 == 9999:
				print("\rSim: {:.3f}, document {} of {}      ".format(sumSimilarity, i, len(headlines)), end="")
	except:
		traceback.print_exc()

#@lexicon: A Lexicon object with a Words attribute
def analysis3_SingleLexicon(model, headlines, lexicon):
	print("Analysis 3 single lexicon...")

	input("WARNING: I haven't tested/verified this yet. Enter any key to continue, and remove this input line once tested.")

	signalTerms = filterLex(model, lexicon.Words)
	avgVec = np.zeros(model.vector_size)
	sumLexUnitVec = getSumUnitVec(model, lexicon.Words)
	signalTerms = [term for term in lexicon.Words if term in model.wv]
	print("After filtering by model vocab, lexicon contains {} terms ({} before filtering)".format(len(signalTerms), len(lexicon.Words)))

	try:
		for i, headline in enumerate(headlines):
			sumSimilarity = cheetifyHeadline_singleLex_optimized(headline, avgVec, sumUnitVec, model)
			if i % 10000 == 9999:
				print("Sim: {:.3f}, object {} of {}".format(sumSimilarity, i, len(headlines)))
	except:
		traceback.print_exc()



