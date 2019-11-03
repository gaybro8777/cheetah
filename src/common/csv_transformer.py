import csv
import sys
import traceback

"""
Iterator for csv data.
See Pandas before reusing this--they may have better interfaces for transforming csv data.
"""
class CsvRecordGenerator:
	def __init__(self, csvPath, delimiter=',', encoding="utf-8"):
		self._csvFile = open(csvPath,"r")
		self._csvReader = csv.DictReader(self._csvFile, delimiter=delimiter)
		self.fieldnames = self._csvReader.fieldnames

	def __iter__(self):
		i = 0
		for record in self._csvReader:
			i+=1
			if i % 10000 == 9999:
				print("\r{} records processed    ".format(i), end="")
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
	if path.exists(opath):
		print("ERROR: output path already exists. Move or delete it before running: {}".format(opath))
		return

	try:
		print("Transforming {} and outputting to {}...".format(csvath, opath))
		reader = CsvRecordGenerator(csvPath, delimiter=delimiter)
		with open(opath, "w+") as outputFile:
			writer = csv.DictWriter(ouptutFile, delimiter=delimiter)
			# Copy the header out, with new fields using @headerTransformFunc
			outputFields = headerTransformFunc(reader.fieldnames)
			writer.write(outputFields)
			for rec in reader:
				outputRec = transformFunc(rec)
				outputCsv.write(outputRec)
			print("Transform completed")
	except:
		traceback.print_exc()

