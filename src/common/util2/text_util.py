import sys
if sys.version_info.major < 3:
	print("ERROR use python3 instead of python 2.7")
	exit()

import re


#Simple wraper object for passing around library sentiment analyzers as dependency injection; both just implement GetSentiment
class TextBlobAnalyzer(object):
	def __init__(self):
		pass
	def GetName(self):
		return "TextBlob"
	def GetSentiment(self, text):
		return TextBlob(text).sentiment[0]
		
class VaderAnalyzer(object):
	def __init__(self):
		self._analyzer = vsent.SentimentIntensityAnalyzer()
	def GetName(self):
		return "VADER"
	def GetSentiment(self, text):
		return self._analyzer.polarity_scores(text)["compound"]
		#return self._analyzer.polarity_scores(t1Text)["negative"]
		#return self._analyzer.polarity_scores(t1Text)["negative"] + self._analyzer.polarity_scores(t1Text)["positive"]

"""
A small python3 class for text normalization. 3, because str is unicode by default.

Other text normalization methods exist (nltk, etc) I just don't like their overly simple methods
and many don't even support unicode uses-cases, which are the primary use-case for web-text normalization
of utf-text.
"""
class TextNormalizer(object):

	#matches only singular possessives; simply dropping all punctuation should work for most plural possessives and singulars ending with s: "Los Angeles' roads..." "Los Angeles roads.."
	#possessiveRegex = re.compile("\w's")
	

	"""
	Normalizes @text via params.

		@lowercase: return @text as lowercase
		@punctReplace: replace punctuation with blankspace ' '
		@punctDelete: delete punctuation instead of replacing it
		@dropPossessives: delete "'s" word endings instead of, for instance, converting "Trump's" to "Trumps". Likewise
			plural possessives or singular possessives ending in 's': "Johnsons'" will become "Johnsons", "Los Angeles'" becomes "Los Angeles"
		@stripNum: Delete numerical characters

	Note there is an ordering to the above constructions. @dropPossessives must be applied before punctuation is deleted, for instance.
	Likewise, @punctDelete and @punctReplace are mutually exclusive: only one may be true.
		
	Also note this method still has a lot of corner cases:
		-Should hyphenated terms be reduced to a single word, or split?
	"""
	@staticmethod
	def normalize(text, lowercase=True, punctReplace=True, punctDelete=False, dropPossessives=True, deleteNum=True):
		if dropPossessives:
			text = text.replace("'s "," ")
		if deleteNum:
			text = numRe.sub(text,"")

		if punctReplace:
			
		elif punctDelete:
			

		if lowercase:
			text = text.lower()

		return text


