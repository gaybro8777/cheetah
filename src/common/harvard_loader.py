import csv
import sys
import traceback
import datetime
from headline import Headline

#A completely one-time-use function for retrieving headlines directly from a csv formatted as per Harvard media 2017 study
def getHeadlinesFromHarvardCsv(csvPath, targetYear=None, targetTerms=None):
	print("Reading headlines from {}, targetTerms={} (case insensitive, if not None), targetYear={} (ignored if None))".format(csvPath, targetTerms, targetYear))
	headlines = []
	if targetTerms is not None:
		targetTerms = [term.lower() for term in targetTerms]

	with open(csvPath,"r", encoding="utf-8") as infile:
		csvReader = csv.reader(infile)
		next(csvReader)
		i = 0
		for record in csvReader:
			if len(record) >= 11:
				dtString = record[3]
				if dtString != "undateable":
					headline = record[1].lower()
					fbShares = int(record[11])
					try:
						dt = datetime.datetime.strptime(dtString,'%Y-%m-%d %H:%M:%S')
						h = Headline()
						h = h.BuildFromHarvardRecord(headline, dt, fbShares)
						fullText = h.GetFullText().lower()
						if (targetYear is None or dt.year == targetYear) and (targetTerms is None or any([term in fullText for term in targetTerms])):
							headlines.append(h)
					except:
						traceback.print_exc()
			i+=1
			if i % 10000 == 9999:
				print("\r{} records processed, {} hits      ".format(i, len(headlines)), end="")
				sys.stdout.flush()

	#for headline in headlines:
	#	headline.PrintTerse()
	print("Parsed {} csv lines, {} hits.".format(i, len(headlines)))
	
	return headlines
