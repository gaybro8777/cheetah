"""
Given a very large file (>1GB or so), split the file into multiple chunks.
Given a collection of chunks, reassemble into file. This is basically the
same as the linux split command, but using python for platform independence.
"""
import os
import math

"""
Just a wrapper around FileSplitter to gzip and split a large file into chunks, then reassemble
and gunzip on the outro.
"""
class GzSplitter(object):
	def __init__(self):
		self._splitter = FileSplitter()
	def Split(self, ifile):
		#gzip ifile to tempfile
		#call splitter
	def Unsplit(self, ofile):
		#call unsplitter
		#gunzip the file

class FileSplitter(object):
	def __init__(self):
		pass

	def Split(self, inputFile, chunkMb, outputFolder):
		if not os.path.isfile(inputFile):
			print("ERROR: no such file "+inputFile)
			return -1
		if chunkMb < 1 or chunkMb > 1000:
			# no reason for this except a sanity check
			print("ERROR chunkMb must be between 1MB and 1000MB.")
			return -1

		print("Splitting input file {} into chunks of size {}MB".format(inputFile, chunkMb))
		with open(inputFile, "rb") as ifile:
			while True:
				bytesRead = ifile.read(chunkMb)
				if not bytesRead:
					break
				ofname = str(i).zfill(8)
				print("Writing {} bytes to {}".format(len(bytesRead), ofname))
				with open(ofname, "wb+") as ofile:
					ofile.write(bytesRead)
		print("Done.")

	def Unsplit(self, inputFolder, outputFile, sanityChecking=True):
		if sanityChecking and os.path.isfile(outputFile):
			print("ERROR output path {} already exists. Move or delete existing file before running".format(outputFile))
			return

		print("Unsplitting files in {} and outputting to {}".format(inputFolder, outputFile))

		with open(outputFile, "wb+") as ofile:
			inputFiles = os.listdir(inputFolder)
			for fname in inputFiles:
				fname = os.path.join(inputFolder, fname)
				with open(fname, "rb") as ifile:
					ofile.write(ifile.read())
