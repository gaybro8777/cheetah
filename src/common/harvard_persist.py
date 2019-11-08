"""
A stand-alone script, likely to become outdated.

Run an algorithm against each record in the harvard data and output a new record, savings
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
import csv_transformer

class HarvardCsvCheetahVisitor(object):
	def __init__(self, model, sentLex, stopLex):
		# initialize params used across visits to csv records
		self._sentLex, self._posCache, self._negCache, self._avgVec = cheetah.getCacheParams(model, sentLex)
		self._stopLex = stopLex
		self._model = model
		self._misses = 0
		self._recCount = 0

	def _harvardRecordToHeadline(self, record):
		#print("DEBUG: ", record, type(record))
		h = None
		if len(record) >= 11:
			dtString = record[3]
			if dtString != "undateable":
				headline = record[1].lower()
				fbShares = int(record[11])
				try:
					dt = datetime.datetime.strptime(dtString,'%Y-%m-%d %H:%M:%S')
					h = Headline()
					h = h.BuildFromHarvardRecord(headline, dt, fbShares)
				except:
					traceback.print_exc()
		return h

	def _transformRecord(self, inputRec):
		"""
		Given an input csv record from the Hahvuhd data, transform it with @inputTransformer to produce an output record.
		Records which don't fit the headline parse model requirements are stored with NAN.
		@inputRec: An input csv record
		@inputTransformer: Function for transforming @inputRec into an output csv record
		"""
		self._recCount += 1
		headline = self._harvardRecordToHeadline(inputRec)
		if headline is not None:
			#drop stop words from headline
			headline.StripTerms(self._stopLex.Words)
			sumSimilarity = cheetah.cheetifyHeadline(headline, self._avgVec, self._posCache, self._negCache, self._model)
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
		This is just a csv transformer for the Harvard Shorenstein csv data: consume the data, trasnform each record,
		and output to a new csv file.
		This transformer calculates cheetah scores for all records in the csv, appending a new 'cheetah' column for these scores,
		so they can be persisted and analyzed offline without re-running cheetah.
		NOTE: This will take up to 48 hours to run...
		"""
		self._misses = 0
		self._recCount = 0
		csv_transformer.transformCsv(csvPath, self._transformRecord, self._transformHeader, opath, delimiter=',')
	

