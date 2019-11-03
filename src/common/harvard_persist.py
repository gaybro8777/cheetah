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
from headline import Headline
import csv_transformer


def harvardRecordToHeadline(rec):
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

def transformRecord(inputRec):
	"""
	Given an input csv record from the Hahvuhd data, transform it with @inputTransformer to produce an output record.
	@inputRec: An input csv record
	@inputTransformer: Function for transforming @inputRec into an output csv record
	"""
	headline = harvardRecordToHeadline(inputRec)
	sumSimilarity = cheetifyHeadline(headline, avgVec, posCache, negCache, model)
	#append similarity to rec, output that to csv
	inputRec.append(sumSimilarity)

	return inputRec

def transformHeader(inputHeader):
	inputHeader.append("cheetah")
	return inputHeader

def cheetifyHarvardCsv(csvPath, opath):
	"""
	This is just a csv transformer for the Harvard Shorenstein csv data: consume the data, trasnform each record,
	and output to a new csv file.
	This transformer calculates cheetah scores for all records in the csv, appending a new 'cheetah' column for these scores,
	so they can be persisted and analyzed offline without re-running cheetah.
	NOTE: This will take up to 48 hours to run...
	"""
	transformCsv(csvPath, transformRecord, transformHeader, opath, delimiter=',')


