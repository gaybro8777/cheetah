"""
A stand-alone script, likely to become outdated.

Run an algorithm against each record in the harvard data and output a new record, saving
this to a new location.

Use-case: you want to run cheetah against every content item, append its score the record, and
save/persist all records such that you can analyze them later without re-running the full analysis/algorithm.
"""

import sys
import traceback
import datetime
import math
from headline import Headline
import cheetah
import numpy as np
import csv_transformer
from data_transformer import DataTransformer
import harvard_loader
from ascii_text_normalizer import AsciiTextNormalizer

class HarvardCsvCheetahVisitor(object):
	def __init__(self, model, sentLex, stopLex):
		# initialize params used across visits to csv records
		# self._sentLex, self._posCache, self._negCache, self._avgVec = cheetah.getCacheParams(model, sentLex)
		self._sentLex = cheetah.filterSentLex(model, sentLex)
		self._avgVec = np.zeros(model.vector_size)
		self._sumPosUnitVec = cheetah.getSumUnitVec(model, sentLex.Positives)
		self._sumNegUnitVec = cheetah.getSumUnitVec(model, sentLex.Negatives)

		self._textNormalizer = AsciiTextNormalizer()
		self._stopLex = stopLex
		self._model = model
		self._misses = 0
		self._recCount = 0

	"""
	def _harvardRecordToHeadline(self, record):
		\"""
		Attempts to build a Headline object from a harvard record, which only have a headline (no extended language text).
		1) This will return many headlines with DT == None, as many records have 'undateable' in datetime field
		2) Text is normalized and stored in the headline.Headline field (since the source data only has headline language anyway)
		\"""
		#print("DEBUG: ", record, type(record))
		h = None
		if len(record) >= 11:
			try:
				dtString = record[3]
				dt = None
				if dtString != "undateable":
					dt = datetime.datetime.strptime(dtString,'%Y-%m-%d %H:%M:%S')
				else:
					dt = None

				headline = record[1]
				headline = DataTransformer.TextNormalizeTerms(headline, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)
				fbShares = int(record[11])
				h = Headline()
				h = h.BuildFromHarvardRecord(headline, dt, fbShares)
			except:
				traceback.print_exc()

		return h
	"""

	def _transformRecord(self, inputRec):
		"""
		Given an input csv record from the Hahvuhd data, transform it with @inputTransformer to produce an output record.
		Records which don't fit the headline parse model requirements are stored with NAN.
		@inputRec: An input csv record
		@inputTransformer: Function for transforming @inputRec into an output csv record
		"""
		self._recCount += 1
		headline = harvard_loader.harvardRecordToHeadline(inputRec)
		if headline is not None:
			DataTransformer.TextNormalizeHeadline(headline, self._textNormalizer, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)
			#drop stop words from headline
			headline.StripTerms(self._stopLex.Words)
			sumSimilarity = cheetah.cheetifyHeadline_optimized(headline, self._avgVec, self._sumPosUnitVec, self._sumNegUnitVec, self._model)
			#sumSimilarity = cheetah.cheetifyHeadline(headline, self._avgVec, self._posCache, self._negCache, self._model)
			#append similarity to rec, output that to csv
			inputRec.append(sumSimilarity)
		else:
			inputRec.append(math.nan)
			self._misses += 1
			if self._misses % 100 == 99:
				print("Misses: {}".format(self._misses))

		return inputRec

	def _transformHeader(self, inputHeader):
		inputHeader.append("cheetah")
		return inputHeader

	def cheetifyHarvardCsv(self, csvPath, opath):
		"""
		This is just a csv transformer for the Harvard Shorenstein csv data: consume the data, transform each record,
		and output to a new csv file.
		This transformer calculates cheetah scores for all records in the csv, appending a new 'cheetah' column for these scores,
		so they can be persisted and analyzed offline without re-running cheetah.
		NOTE: This will take up to 48 hours to run...
		"""
		self._misses = 0
		self._recCount = 0

		print("Adding cheetah values to csv. Note: text normalization is done inline, and not retained. No stemmer is used.")
		csv_transformer.transformCsv(csvPath, self._transformRecord, self._transformHeader, opath, delimiter=',')
	

