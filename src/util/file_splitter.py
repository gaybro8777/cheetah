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
		if os.path.isfile(opath):
			print("ERROR: output file already exists {}".format(opath))
			return -1
		if not os.path.isfile(bigFile):
			print("ERROR: input file already exists {}".format(bigFile))
			return -1

		result = -1
		try:
			print("Gzipping file {} to {}".format(bigFile, opath))
			with open(bigFile, "rb") as src:
				with gzip.open(opath, "wb+") as dst:        
					dst.write(src.read())
			print("Done.")
			result = 1
		except:
			traceback.print_exc()
		return result

	def Split(self, bigFile, outputFolder, chunkMb=25):
		if not os.path.isdir(outputFolder):
			print("ERROR: output folder does not exist.")
			return -1

		destPath = bigFile+".gz"
		result = self._gzipFile(bigFile, destPath)
		if result > 0:
			result = self._splitter.Split(destPath, outputFolder, chunkMb)
		return result

	def Unsplit(self, inputFolder, bigOutputFile):
		if not os.path.isdir(inputFolder):
			print("ERROR: input folder does not exist.")
			return -1

		if os.path.isfile(bigOutputFile):
			print("ERROR: output file already exists {}".format(bigOutputFile))
			return -1

		result = -1
		gzPath = bigOutputFile+".gz"
		if self._splitter.Unsplit(inputFolder, gzPath) > 0:
			try:
				with open(bigOutputFile, "wb+") as ofile:
					with gzip.open(gzPath, 'rb') as gzFile:
						ofile.write(gzFile.read())
				result = 1
			except:
				traceback.print_exc()

		return result

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

		result = -1
		try:
			print("Splitting input file {} into chunks of size {}MB in {}".format(inputFile, chunkMb, outputFolder))
			with open(inputFile, "rb") as ifile:
				i = 0
				while True:
					bytesRead = ifile.read(chunkMb * 1000000)
					if not bytesRead:
						break
					ofname = os.path.join(outputFolder, str(i).zfill(8))
					print("Writing {} bytes to {}".format(len(bytesRead), ofname))
					with open(ofname, "wb+") as ofile:
						ofile.write(bytesRead)
					i+=1
			print("Done.")
			result = 1
		except:
			traceback.print_exc()
		return result

	def Unsplit(self, inputFolder, outputFile, sanityChecking=True):
		if sanityChecking and os.path.isfile(outputFile):
			print("ERROR output path {} already exists. Move or delete existing file before running".format(outputFile))
			return -1

		inputFiles = [os.path.join(inputFolder, fname) for fname in sorted(os.listdir(inputFolder))]
		if len(inputFiles) == 0:
			print("ERROR: input files empty.")
			return -1

		print("Unsplitting files in {} and outputting to {}".format(inputFolder, outputFile))

		result = -1
		try:
			with open(outputFile, "wb+") as ofile:
				for fname in inputFiles:
					with open(fname, "rb") as ifile:
						ofile.write(ifile.read())
			result = 1
		except:
			traceback.print_exc()
		return result


def main():
	bigFile = "test.csv"
	outputFolder = "test/"
	gzSplitter = GzSplitter()
	#gzSplitter.Split(bigFile, outputFolder, 25)
	gzSplitter.Unsplit(outputFolder, "test_result.csv")

if __name__ == "__main__":
	main()

