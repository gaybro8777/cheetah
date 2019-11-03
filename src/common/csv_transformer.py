import csv
import os
import sys
import traceback

"""
Iterator for csv data.
See Pandas before reusing this--they may have better interfaces for transforming csv data.
"""
class CsvRecordGenerator(object):
	def __init__(self, csvPath, delimiter=',', encoding="utf-8"):
		self._csvFile = open(csvPath,"r")
		self._csvReader = csv.reader(self._csvFile, delimiter=delimiter)
		self.fieldnames = next(self._csvReader)

	def __iter__(self):
		i = 0
		for record in self._csvReader:
			i+=1
			if i % 100 == 99:
				print("\r{} records processed     ".format(i), end="")
				sys.stdout.flush()
			yield record
		self._csvFile.close()

"""
This is for consuming csv data, performing transformations on each record, and outputing
a new csv file to an output path; with minimal in-memory data.

@csvPath: input path
@recTransformFunc: A function to apply to each record in the input csv, to generate an output csv record
@headerTransformFunc: The function to apply to the input csv's header (e.g., append a new set of columns)
@opath: The output path for the new csv file

Csv header is required.
"""
def transformCsv(csvPath, recTransformFunc, headerTransformFunc, opath, delimiter=','):
	# IO checks
	if opath == csvPath:
		print("ERROR: input cannot be output: {} {}".format(csvPath, opath))
		return
	if os.path.exists(opath):
		print("ERROR: output path already exists. Move or delete it before running: {}".format(opath))
		return

	try:
		print("Transforming {} and outputting to {}...".format(csvPath, opath))
		reader = CsvRecordGenerator(csvPath, delimiter=delimiter)
		with open(opath, "w+") as outputFile:
			writer = csv.writer(outputFile, delimiter=delimiter)
			# Copy the header out, with new fields using @headerTransformFunc
			fieldnames = headerTransformFunc(reader.fieldnames)
			writer.writerow(fieldnames)
			for rec in reader:
				outputRec = recTransformFunc(rec)
				writer.writerow(outputRec)
			print("Transform completed")
	except:
		traceback.print_exc()

