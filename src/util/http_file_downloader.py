"""
A downloader for fasttext models. This depends entirely on the static structure of the fasttext page,
so any changes to the page will break this script.
"""

from urllib.request import urlretrieve
from urllib.parse import urlparse
import os
from datetime import datetime

"""
A simple http file downloader; no error checking, no auth.
"""
class HTTPFileDownloader(object):
	def __init__(self):
		self._callbackCount = 0
		self._beginDt = None
	def download(self, url, destFolder="./"):
		"""
		Simply downloads a file to @destFolder, overwriting any existing file.
		"""
		if not destFolder.endswith(os.sep):
			destFolder += os.sep
		if not os.path.exists(destFolder):
			os.mkdir(destFolder)

		fname = urlparse(url.rstrip('/')).path.split('/')[-1]
		fpath = os.path.join(destFolder, fname)
		if os.path.exists(fpath):
			raise Exception("The output file {} already exists. Delete before re-downloading.".format(fpath))

		self._download(url, fpath)

	def _download(self, url, destFile):
		# Download the file	
		local_name, headers = urlretrieve(url, filename=destFile, reporthook=self._reportProgress)
		# Cleanup temp files left by the library. Needy api...
		urllib.request.urlcleanup()

	def _currentEta(self, bytesRead, totalBytes):
		time_delta = datetime.now() - self._beginDt
		bytesPerSecond = bytesRead / float(time_delta.total_seconds())
		remainingSeconds = totalBytes / bytesPerSecond
		seconds = int(remainingSeconds % 60)
		minutes = int(remainingSeconds // 60) % 60
		hours = int(remainingSeconds // 3600) % 84600
		days = int(remainingSeconds // 84600)
		return days, hours, minutes, seconds

	def _etaToString(self, days, hours, minutes, seconds):
		return "{}d:{:02d}h:{:02d}m:{:02d}s".format(days, hours, minutes, seconds)

	def _reportProgress(self, blockCount, blockSize, totalSize):
		if blockCount == 0:
			print("Beginning download.", end="")
			self._callbackCount = 0
			self._beginDt = datetime.now()
		# Calculate progress
		bytesRead = blockCount * blockSize
		percentComplete = 100.0 * float(bytesRead) / float(totalSize)
		self._callbackCount += 1
		if self._callbackCount % 40 == 39:
			eta = self._etaToString(*self._currentEta(bytesRead, totalSize))
			print("\rRead {}kb of {}kb, {:.2f}% complete. ETA {}         ".format(int(bytesRead/1000), int(totalSize/1000), percentComplete, eta), end="", flush=True)

