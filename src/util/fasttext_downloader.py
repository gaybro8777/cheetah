"""
A downloader for fasttext models. This depends entirely on the static structure of the fasttext page,
so any changes to the page will break this script.
"""

import requests
import os
from bs4 import BeautifulSoup
from http_file_downloader import HTTPFileDownloader

"""
A simple FastTextDownloader class for downloading FastText models from the facebook research page 'Word Vectors for 157 languages'.
This class relies directly on the page structure of the FastText '157 languages' page (https://fasttext.cc/docs/en/crawl-vectors.html)
so this is fragile, single-shot code. This can list the available languages, and then download selected 'bin' or 'text' model gzips.
If a failure occurs (e.g., timeout on slow connections), this class offers no error handling and you will have to delete the model and re-download.

Many thanks to the facebook ai group for all of these models.
"""
class FastTextDownloader(object):
	def __init__(self):
		self._downloader = HTTPFileDownloader()
		self._modelPageUrl = "https://fasttext.cc/docs/en/crawl-vectors.html"

	def listLanguages(self):
		"""
		Returns a list of the available fasttext model languages (english, afrikaans, etc).
		All languages have both bin and text versions (see the fb page).
		Clients can use this to list available languages, and select one.
		"""
		html = self._getModelPage()
		return self._listLanguages(html)

	def download(self, languages=["english"], modelVersion="text", destFolder="./"):
		"""
		Downloads fasttext language models from the fb research page per the specified language and model version.
		The models are huge (~2Gb+) and may take an hour or more to download on mediocre connections.
		To download multiple models/versions etc, just generalize this function or create multiple downloaders over different networks.
		@languages: A list of languages to download serially.
		@modelVersion: Either 'text' or 'bin'. See the fb page for the meaning of this. Bin models are huge, text models
		are much smaller (~1.5+GB), but include only term vectors.
		"""
		if not destFolder.endswith(os.sep):
			destFolder+=os.sep
		print("Downloading language models for "+",".join(languages)+" in "+modelVersion+" format, to "+destFolder+".")

		html = self._getModelPage()
		linkMap = self._buildLinkMap(html)
		if any(language not in linkMap.keys() for language in languages):
			raise Exception("Language not found in models. Available models: {} Requested: {}".format(linkMap.keys(), languages))
		for language in languages:
			modelUrl = linkMap[language][modelVersion]
			self._downloader.download(modelUrl, destFolder=destFolder+language)

	def _getElemText(self, elem):
		# Returns only the immediate html element text, not including its childrens' text.
		return ''.join(elem.find_all(text=True, recursive=False)).strip()

	def _listLanguages(self, html):
		"""
		@html: Unparsed raw, utf8 html bytes.
		"""
		languages = []
		parsedHtml = BeautifulSoup(html, "html.parser")
		tableElem = parsedHtml.body.find('tbody')
		for tr in tableElem.find_all('tr'):
			for td in tr.find_all('td'):
				language = self._getElemText(td).split(" ")[0].replace(":", "").lower()
				languages.append(language)
		#print("Available anguages: ",languages)
		return languages

	def _getModelPage(self):
		return requests.get(self._modelPageUrl).content

	def _buildLinkMap(self, html):
		"""
		@html: Raw utf8 page bytes
		Given the facebook fasttext page, parses the page and builds a dictionary mapping language names
		to dicts of (bin,text) links. E.g.: {"english" : {"bin":"https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.af.300.bin.gz", "text":"https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.af.300.vec.gz"}}
		Access like the 'text' model url link to a specific language like so: linkMap["afrikaans"]["text"]
		"""
		linkMap = dict() # language -> ("bin" OR "text") -> model link
		parsedHtml = BeautifulSoup(html,"html.parser")
		tableElem = parsedHtml.body.find('tbody')
		for tr in tableElem.find_all('tr'):
			for td in tr.find_all('td'):
				language = self._getElemText(td).split(" ")[0].replace(":", "").lower()
				linkMap[language] = dict()
				for alink in td.find_all('a'):
					if alink.text.lower() == "bin":
						linkMap[language]["bin"] = alink["href"]
					if alink.text.lower() == "text":
						linkMap[language]["text"] = alink["href"]
		return linkMap

# Unit testing
#ftd = FastTextDownloader()
#ftd.download(languages=["afrikaans"], modelVersion="bin", destFolder="../models/")
#url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ka.300.vec.gz"
#opath = "georgian"
#downloader = FileDownloader()
#downloader.download(url, opath)
