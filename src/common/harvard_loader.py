import csv
import sys
import traceback
import datetime
from headline import Headline
from data_transformer import DataTransformer
from ascii_text_normalizer import AsciiTextNormalizer

def harvardRecordToHeadline(record):
	"""
	Attempts to build a Headline object from a harvard record, which only have a headline (no extended language text).
	1) This will return many headlines with DT == None, as many records have 'undateable' in datetime field
	3) Returned headline may be None, if record is insufficient length, or error occurs
	"""
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
			fbShares = int(record[11])
			h = Headline()
			h = h.BuildFromHarvardRecord(headline, dt, fbShares)
		except:
			traceback.print_exc()

	return h

#A completely one-time-use function for retrieving headlines directly from a csv formatted as per Harvard media 2017 study
def getHeadlinesFromHarvardCsv(csvPath, targetYear=None, targetTerms=None):
	print("Reading headlines from {}, targetTerms={} (case insensitive, if not None), targetYear={} (ignored if None))".format(csvPath, targetTerms, targetYear))
	headlines = []
	if targetTerms is not None:
		targetTerms = [term.lower() for term in targetTerms]

	normalizer = AsciiTextNormalizer()

	with open(csvPath,"r", encoding="utf-8") as infile:
		csvReader = csv.reader(infile)
		next(csvReader)
		i = 0
		for record in csvReader:
			try:
				headline = harvardRecordToHeadline(record)
				if headline is not None:
					DataTransformer.TextNormalizeHeadline(headline, normalizer, filterNonAlphaNum=True, deleteFiltered=False, lowercase=True)
					dt = headline.DT
					# match on year, if passed
					if targetYear is None or (dt is not None and dt.year == targetYear):
						# match on topics, if passed
						if targetTerms is None or headline.HasTopicalHeadlineHit(targetTerms):
							headlines.append(headline)
					#	else:
					#		print("topic miss: ", targetTerms, headline.GetFullText())
					#else:
					#	print("year miss")
			except:
				traceback.print_exc()

			i+=1
			if i % 10000 == 9999:
				hitRate = 100.0 * (float(len(headlines)) / float(i))
				print("\r{} records processed, {} hits, {}% hit rate      ".format(i, len(headlines), str(hitRate)[0:8]), end="")
				sys.stdout.flush()

	#for headline in headlines:
	#	headline.PrintTerse()
	print("Parsed {} csv lines, {} hits.".format(i, len(headlines)))
	
	return headlines
