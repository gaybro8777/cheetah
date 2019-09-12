


"""
TODO:
	0) Lint
	1) Other algorithms, share regression, visualization, 
	2) Test scripts
"""

import sys
sys.path.append('./common')
sys.path.append('./util')

import os
from datetime import datetime
from common import cheetah
from common import cheetah_present
from result_collection import ResultCollection
from zipfile import ZipFile
from util.fasttext_downloader import FastTextDownloader

dataDir = "../data/"
reproDir = "../repro/"
modelDir = "../models/"
resultDir = "../results/"
lexicaDir = "../lexica/"
licensePath = "../license.md"
logoDir = "../misc/logos"


def printLicense():
	"""
	
	"""
	with open(licensePath, "r") as licenseFile:
		print(licenseFile.read())

def listFiles(dirPath, extension="", verbose=True):
	# Lists files in DirPath by name, with optional extension filter.
	fList = [fname for fname in os.listdir(dirPath) if fname.endswith(extension)]
	if verbose:
		print("Found {} files in {} with {} extension:".format(len(fList), dirPath, extension))
		print("  ".join(["{}. {}\n".format(i,fname) for i, fname in enumerate(fList)]))
	return fList

def unzipReproData(reproFname="cheetah_repro.zip"):
	"""
	Unzips a filename in @reproFolder to @dataDir under a folder of the file's same name, e.g.
	'cheetah_repro.zip' will be unzipped to ../data/cheetah_repro.
	If the output folder already exists, the unzip is aborted to prevent overwriting.
	@reproFname: The output folder to which dataset will be unzipped
	"""
	zipPaths = [fname for fname in listFiles(reproDir, ".zip") if reproFname in fname]
	if not zipPaths:
		zipPath = zipPaths[0]
		outputFolder = reproFname.replace(".zip","")
		odir = os.path.join(dataDir, outputFolder)
		if os.path.exists(odir):
			print("WARNING: the output folder {} already exists. Data unzip aborted. Delete output folder and retry.".format(odir))
			return
		with ZipFile(zipPath, "r") as zipFile:
			print("Unzipping {}. Files in zipped repro:".format(zipPath))
			zipFile.printdir()
			zipFile.extractall(path=odir)

def selectOption(validOptions, prompt="Select option: "):
	#Returns selected option as str
	#@validOptions: must be a list of strings
	option = input(prompt)
	while option not in validOptions:
		print("Invalid option. Re-enter.")
		option = input(prompt)
	return option

def selectFromFileList(flist, prompt="File list"):
	# Select a file from the provided list, and return its name
	print(prompt)
	print("\t"+"\t".join(["{}: ".format(i)+fname+"\n" for i, fname in enumerate(flist)]).rstrip())
	options = [str(i) for i in range(len(flist))]
	selectedOption = selectOption(options)
	selectedIndex = int(selectedOption)
	return flist[selectedIndex]

def selectDataFile():
	# Select a file by name in some directory
	jsonPaths = listFiles(dataDir, "json", verbose=False)
	jsonPath = selectFromFileList(jsonPaths, prompt="Select a json dataset: ")
	return os.path.join(dataDir,jsonPath)

def downloadEnglishModel():
	# One-shot, downloads English text model. This could support listing, selecting, and downloading instead, but not needed now.
	modelSource = "https://fasttext.cc/docs/en/crawl-vectors.html"
	print("English word vector model will be downloaded from "+modelSource)
	print("These models are quite large (>2Gb) which can take an hour or more to download on slow connections.")
	print("Alternatively, use a browser to manually download models to the models/[language] folder from "+modelSource)
	confirmation = input("Do you wish to proceed? Enter y or n: ").lower() in ["y", "yes"]
	if confirmation:
		ftd = FastTextDownloader()
		ftd.download(["english"], modelVersion="text", destFolder=modelDir)

def loadDataset():
	cheetahFolder = "cheetah_repro"
	cheetahDir = os.path.join(dataDir, cheetahFolder)
	# unzip cheetah_repro.zip file if not already unzipped to ../data/cheetah_repro/
	if not os.path.exists(cheetahDir):
		print("Unzipping dataset to "+cheetahFolder)
		unzipReproData(cheetahFolder)
	else:
		print("Dataset already unzipped to "+cheetahFolder+". Proceeding to dataset selection.")
	jsonPath = selectDataFile()
	return ResultCollection.LoadCollections(jsonPath)

def loadModel():
	modelFname = "cc.en.300.vec.gz"
	modelPath = os.path.join(modelDir, modelFname)
	return cheetah.loadFastTextModel(modelPath)

def cheetahAnalysis():
	"""
	-Select and load a dataset
	-Run cheetah, outputting to results/ folder
	"""
	
	resultCollections = loadDataset()	
	modelPath=os.path.join(modelDir, "english/cc.en.300.vec")
	if not os.path.exists(modelPath):
		print("ERROR: model not found at {}. Select 'Download fasttext model' in main menu to download model before running analysis.".format(modelPath))
		return
	vectorModel = cheetah.loadFastTextModel(modelPath=modelPath)
	sentFolder=os.path.join(lexicaDir, "sentiment/BingLiu/")
	#TODO: get these from the result collection?
	dtLow, dtHigh = ResultCollection.GetMinMaxDt(resultCollections)
	cheetah_present.cheetahSentimentAnalysis(resultCollections, sentFolder, vectorModel, dtLow.date(), dtHigh.date(), dtGrouping="weekly", resultFolder=resultDir, useScoreWeight=False, useSoftMatch=False)

def modelAnalysis():
	print("Under construction")

def printLogo():
	logoPaths = [os.path.join(logoDir,logoPath) for logoPath in os.listdir(logoDir)]
	logoPath = logoPaths[datetime.now().second % len(logoPaths)]
	with open(logoPath, "r") as logoFile:
		print(logoFile.read())

def printIntro():
	desc = """

                   ________  _______________________    __  __
                  / ____/ / / / ____/ ____/_  __/   |  / / / /
                 / /   / /_/ / __/ / __/   / / / /| | / /_/ / 
                / /___/ __  / /___/ /___  / / / ___ |/ __  /  
                \____/_/ /_/_____/_____/ /_/ /_/  |_/_/ /_/  

                           Never trust--only verify.


Welcome to Cheetah, a cousin of the ABLE-ITEM deep web content extractor and Sentinel analysis
engine, by Jesse Waite. I am an American NLP developer and informatic security researcher
specializing in the use of machine/deep learning for counter-misinformation. Don't believe me?
I wouldn't either. That's why I'm publishing this tool to provide live-demos of open source
multi-language misinformation analysis methods. Also some other (and perhaps funner)
grand-nlp stuff too. This basic interface is just for algorithmic/dataset repro purposes.


To execute cheetah repro, begin by downloading the fasttext english '.text' model (option 0).
Then run Cheetah analysis (option 1).
"""
	"""
Upcoming analyses:
1) Vector model algebraic analysis: analyzing the prior bias built into vector space language
	models due to input data bias.
2) Vector/document clustering and 3d visualization
3) Attempts at share regression:
		Problem: "Map language vectors D to facebook/twitter/other social share counts."
    This is a fascinating and useful topic for analyzing the value of specific topics with respect
	to positive/negative sentiment. The approach allows us to correlate the value of 
	misinformation to different content platforms and organizations, to understand the economic
	incentives of bias and misinformation for different organizations. Put simply, you can regress
	on share/engagement counts to evaluate and compare the value of bias/topics for a website or
	any other content source.
4) Russian, Chinese, and other global analyses:
	Problem: How do sentiment dynamics, topical polarization generalize to other regions/regimes?
5) Lexicon generation: how generating signal lexica in any language is a snap.
6) Structured inference: given the distribution of search results returned by a biased search
	platform (e.g. Google/Youtube, Chinese-censored platforms, etc), learn the sentiment
	parameters of its output. This is simple transfer learning where given a set of ranked results
	for some query, you use a structured perceptron and doc-vectors to reproduce the same
	algorithm. One algorithm learns the other's behavior through learning-to-rank. By doing so, you
	can evaluate the biases of search algorithms as misinformation actors fiddle with their
	parameters to obtain some target behavior.

Cheers.
"""
	print(desc)

def mainMenu():

	printLogo()
	printIntro()

	cmdDict = {
		"0": downloadEnglishModel,
		"1": cheetahAnalysis,
		"2": modelAnalysis,
		"3": printIntro,
		"4": printLicense,
		"5": exit
	}

	while True:
		print("Main menu")
		print("\t0) Download English FastText model")
		print("\t1) Cheetah analyis")
		print("\t2) Model analysis")
		print("\t3) Intro")
		print("\t4) License info")
		print("\t5) Exit")
		option = selectOption(cmdDict.keys())
		cmd = cmdDict[option]
		cmd()

def main():
	mainMenu()

if __name__ == "__main__":
	main()
