"""
Copyright: All other code in the cheetah project is copyright protected under the license in the root of the repo.
However this is a nice utility others may find useful, so this file has its own license.

LICENSE: this file is covered by the GNU General Public License v2.0, with the following restrictions.
This code is free for commercial or private use, and modification, et cetera, but with the following
attribution: Cheetah Project, 2019.
"""


"""
A rudimentary python version of the linux split command:
Given a very large file (>1GB or so), split the file into multiple chunks.
Given a collection of chunks, reassemble into file. This is basically the
same as the linux split command, but using python for platform independence.

- FileSplitter: the file splitter.
- GzSplitter: pass this a large uncompressed file, compress it to a gz file, then split the gz into multiple files of size @chunkMb.
  The Unsplit command just does the inverse: pass it a folder of split file fragments, cat them into a single gz, and uncompress.

In a professional setting, you'll want more file system checks and other error handling (e.g., no 
naughty user paths, zip slip prevention, more basic checks).

"""
import os
import math
import gzip
import filecmp

class GzSplitter(object):
	"""
	Just a wrapper around FileSplitter to gzip and split a large file into chunks,
	then reassemble and gunzip on the outro.
	"""
	def __init__(self):
		self._splitter = FileSplitter()

	def _gzipFile(self, bigFile, opath, fsChecking=True):
		"""
		@bigFile: Path to some big file.
		@opath: The output path to which @bigFile will be g-zipped, as bifFile+".gz".
		@fsChecks: Non-essential file system checks, e.g., to prevent overwriting existing content.
		"""

		if fsChecking and os.path.isfile(opath):
			print("ERROR: output file already exists {}".format(opath))
			return -1
		if not os.path.isfile(bigFile):
			print("ERROR: input file does not exist {}".format(bigFile))
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

	def Split(self, bigFile, outputFolder, chunkMb=25, fsChecking=True):
		"""
		@bigFile: A large, uncompressed input file.
		@outputFolder: An output directory to which the file will be compressed to a gz and then fragmented over multiple files.
		@chunkMb: The MB chunk size of files.
		@fsChecking: Non-essential file system checks, e.g., to prevent overwriting existing content.
		"""
		if not os.path.isdir(outputFolder):
			print("ERROR: output folder does not exist.")
			return -1

		destPath = bigFile+".gz"
		result = self._gzipFile(bigFile, destPath, fsChecking)
		if result > 0:
			result = self._splitter.Split(destPath, outputFolder, chunkMb, fsChecking)
			#remove the temp gz file
			os.remove(destPath)
		return result

	def Unsplit(self, inputFolder, bigOutputFile, fsChecking=True):
		"""
		@inputFolder: An input folder containing the outputs (gz fragments) of the Split() method.
		@bigOutputFile: The file to which the gz will be reassembled and uncompressed.
		@fsChecking: Non-essential file system checks, e.g., to prevent overwriting existing content.
		"""
		if not os.path.isdir(inputFolder):
			print("ERROR: input folder does not exist.")
			return -1
		if fsChecking and os.path.isfile(bigOutputFile):
			print("ERROR: output file already exists {}".format(bigOutputFile))
			return -1

		result = -1
		gzPath = bigOutputFile+".gz"
		if self._splitter.Unsplit(inputFolder, gzPath, fsChecking) > 0:
			try:
				with open(bigOutputFile, "wb+") as ofile:
					with gzip.open(gzPath, "rb") as gzFile:
						ofile.write(gzFile.read())
				#remove temp gz file
				os.remove(gzPath)
				result = 1
			except:
				traceback.print_exc()

		return result

class FileSplitter(object):
	"""
	A class for splitting an input into multiple fragments of maximum size @chunkMb, and writing those
	fragments to an (empty) output directory with sortable names ("000000","000001"...).
	"""
	def __init__(self):
		pass

	def Split(self, inputFile, outputFolder, chunkMb=25, fsChecking=True):
		"""
		@inputFile: The input file to split into chunks of size @chunkMb
		@chunkMb: The size of the output file. The last file will be smaller.
		@outputFolder: An output location. Must be empty.
		@fsChecking: If true, include non-essential file system checking, e.g., abort instead of just overwriting existig content.
		"""
		if fsChecking and os.path.isdir(outputFolder) and len(os.listdir(outputFolder)) > 0:
			print("ERROR: output folder is not empty. Empty it before calling.")
			return -1
		if not os.path.isfile(inputFile):
			print("ERROR: no such file "+inputFile)
			return -1
		chunkMb = int(chunkMb)
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

	def Unsplit(self, inputFolder, outputFile, fsChecking=True):
		"""
		@inputFolder: A folder containing the output of the Split() method.
		@outputFile: The file to which the fragments in @inputFolder will be reassembled to a gz and uncompressed.
		@fsChecking: If true, include non-essential file system checking, e.g., abort instead of just overwriting existig content.
		"""
		if fsChecking and os.path.isfile(outputFile):
			print("ERROR output path {} already exists. Move or delete existing file before running".format(outputFile))
			return -1

		inputFiles = [os.path.join(inputFolder, fname) for fname in sorted(os.listdir(inputFolder)) if fname.isdigit()]
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

def filesEqual(path1, path2):
	"""
	Returns true if two files are equal in content, or both are empty:
	"""
	if not os.path.isfile(path1):
		print("ERROR path does not exist: "+path1)
		return False
	if not os.path.isfile(path2):
		print("ERROR path does not exist: "+path2)
		return False

	return filecmp.cmp(path1, path2)	

def selfTest():
	print("Running self-test. Place a large (>100MB) file named test.csv in this directory as input.") 
	bigFile = "test.csv"
	outputFile = "test_result.csv"
	resultGzTemp = outputFile+".gz"
	gzTemp = bigFile+".gz"
	outputFolder = "test/"
	if not os.path.isdir(outputFolder):
		os.mkdir(outputFolder)

	gzSplitter = GzSplitter()
	result = "FAIL"

	try:
		if gzSplitter.Split(bigFile, outputFolder, 25) > 0:
			if gzSplitter.Unsplit(outputFolder, outputFile) > 0:
				result = "PASS" if filesEqual(bigFile, outputFile) else "FAIL"
	except:
		traceback.print_exc()
	
	print("Test result: "+result)

	#clean up
	outputFiles = [os.path.join(outputFolder, fname) for fname in os.listdir(outputFolder)]
	if len(outputFiles) > 0:
		for fpath in outputFiles:
			os.remove(fpath)
	if os.path.isfile(outputFile):
		os.remove(outputFile)
	if os.path.isfile(gzTemp):
		os.remove(gzTemp)
	if os.path.isfile(resultGzTemp):
		os.remove(resultGzTemp)


def main():
	selfTest()

if __name__ == "__main__":
	main()

