"""
Given a very large file (>1GB or so), split the file into multiple chunks.
Given a collection of chunks, reassemble into file. This is basically the
same as the linux split command, but using python for platform independence.
"""
import os
import math
import gzip

"""
Just a wrapper around FileSplitter to gzip and split a large file into chunks, then reassemble
and gunzip on the outro.
"""
class GzSplitter(object):
	def __init__(self):
		self._splitter = FileSplitter()

	def _gzipFile(self, bigFile, opath):
		print("Gzipping file {} to {}".format(bigFile, opath))
		with open(bigFile, "rb") as src:
			with gzip.open(opath, "wb+") as dst:        
				dst.write(src.read())
		print("Done.")

	def Split(self, bigFile, outputFolder, chunkMb=25):
		destPath = bigFile+".gz"
		self._gzipFile(bigFile, destPath)
		self._splitter.Split(destPath, outputFolder, chunkMb)

	def Unsplit(self, inputFolder, bigOutputFile):
		gzPath = bigOutputFile+".gz"
		self._splitter.Unsplit(inputFolder, gzPath)
		with open(bigOutputFile, "w+") as ofile:
			with gzip.open(gzPath, 'rb') as gzFile:
				ofile.write(gzPath.read())

class FileSplitter(object):
	def __init__(self):
		pass

	def Split(self, inputFile, outputFolder, chunkMb=25):
		"""
		@inputFile: The input file to split into chunks of size @chunkMb
		@chunkMb: The size of the output file. The last file will be smaller.
		@outputFolder: An output location. Must be empty.
		"""

		if os.path.isdir(outputFolder) and len(os.listdir(outputFolder)) > 0:
			print("ERROR: output folder is not empty. Empty it before calling.")
			return -1
		if not os.path.isfile(inputFile):
			print("ERROR: no such file "+inputFile)
			return -1
		if chunkMb < 1 or chunkMb > 1000:
			# no reason for this except a sanity check
			print("ERROR chunkMb must be between 1MB and 1000MB.")
			return -1

		if not os.path.isdir(outputFolder):
			os.mkdir(outputFolder)

		print("Splitting input file {} into chunks of size {}MB".format(inputFile, chunkMb))
		with open(inputFile, "rb") as ifile:
			i = 0
			while True:
				bytesRead = ifile.read(chunkMb * 1000000)
				if not bytesRead:
					break
				ofname = str(i).zfill(8)
				print("Writing {} bytes to {}".format(len(bytesRead), ofname))
				with open(ofname, "wb+") as ofile:
					ofile.write(bytesRead)
				i+=1
		print("Done.")

	def Unsplit(self, inputFolder, outputFile, sanityChecking=True):
		if sanityChecking and os.path.isfile(outputFile):
			print("ERROR output path {} already exists. Move or delete existing file before running".format(outputFile))
			return

		inputFiles = [os.path.join(inputFolder, fname) for fname in sorted(os.listdir(inputFolder))]
		if len(inputFiles) == 0:
			print("ERROR: input files empty.")
			return

		print("Unsplitting files in {} and outputting to {}".format(inputFolder, outputFile))

		with open(outputFile, "wb+") as ofile:
			for fname in inputFiles:
				with open(fname, "rb") as ifile:
					ofile.write(ifile.read())

def main():
	bigFile = "test.csv"
	outputFolder = "test/"
	gzSplitter = GzSplitter()
	gzSplitter.Split(bigFile, outputFolder, 25)
	gzSplitter.Unsplit(outputFolder, "test_result.csv")

if __name__ == "__main__":
	main()

