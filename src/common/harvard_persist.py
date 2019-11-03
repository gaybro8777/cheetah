"""
A stand-alone script, likely to become outdated.

Run an algorithm against each record in the harvard data and output a new record, savings
this to a new location.

Use-case: you want to run cheetah against every content item, append its score the record, and
save/persist all records such that you can analyze them later without re-running the full analysis/algorithm.
"""

import csv
import sys
import traceback
import datetime
from headline import Headline

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


def inputToOutputRec(inputRec, transformFunc):
	"""
	Given an input csv record from the Hahvuhd data, transform it with @inputTransformer to produce an output record.
	@inputRec: An input csv record
	@inputTransformer: Function for transforming @inputRec into an output csv record
	"""
	headline = harvardRecordToHeadline(inputRec)
	#(headline, avgVec, posCache, negCache, model):
	sumSimilarity = cheetifyHeadline(headline, avgVec, posCache, negCache, model)
	#append similarity to rec, output that to csv
	...
	return outputRec


def harvardRecordToHeadline(rec):
	h = None
	if len(rec) >= 11:
		dtString = rec[3]
		if dtString != "undateable":
			headline = rec[1].lower()
			fbShares = int(rec[11])
			try:
				dt = datetime.datetime.strptime(dtString,'%Y-%m-%d %H:%M:%S')
				h = Headline()
				h = h.BuildFromHarvardRecord(headline, dt, fbShares)
			except:
				traceback.print_exc()
	return h

"""
Iterate harvard data, taking in each record, appending some calculations, and outputing
new records to @opath.
"""
def csvTransformer(csvPath, transformFunc, opath):
	# IO checks
	if opath == csvPath:
		print("ERROR: input cannot be output: {} {}".format(csvPath, opath))
		return
	if path.exists(opath):
		print("ERROR: output path already exists. Move or delete it before running: {}".format(opath))
		return

	try:
		with open(opath, "w+") as outputCsv:
			for rec in csvRecordGenerator(csvPath):
				outputRec = transformFunc(rec)
				outputCsv.write(outputRec)
	except:
		traceback.print_exc()

"""
Iterates content items in the Harvard Shorenstein data, applying @scoreFunc to each record, mapping
it to a real-value/score: f(content-item) -> R1. @outputFunc maps the record to an output record.


"""
def csvRecordGenerator(csvPath):
	with open(csvPath,"r", encoding="utf-8") as infile:
		csvReader = csv.reader(infile)
		next(csvReader)
		i = 0
		for record in csvReader:
			i+=1
			if i % 10000 == 9999:
				print("\r{} records processed, {} hits      ".format(i, len(headlines)), end="")
				sys.stdout.flush()
			yield record

