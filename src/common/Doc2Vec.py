import sys
import gensim

"""
Just a gensim wrapper for deriving vector representations of documents, as
a standalone script.

See the Doc2Vec constructor docs for reference of inputs, parameters, etc.
"""

class FbDocumentStream(object):
	def __init__(self, fname, limit):
		"""
		This class is completely ad hoc for experimenting with how quickly gensim can build a document-vector model from a large ABLE-based fbData.py file.
		Note this is very dirty anyway and does involve any text cleaning or normalization.

		@fname: The path to some file containing text which will be haphazardly broken into training sequences per-line.
		@limit: The number of sequences to generate before terminating the stream. If -1, then no limit (entire file).
		"""
		self._fname = fname
		self._limit = limit

	def __iter__(self):
		with open(self._fname, "r") as docFile:
			ct = 0
			for line in docFile:
				try:
					#print("line: {}".format(line))
					fbDict = eval(line)[1]["og_object"]
					#print(str(fbDict))
					#exit()
					if self._limit < 0 or ct < self._limit:
						seq = (fbDict["title"]+" "+fbDict["description"]).lower()
						doc = gensim.models.doc2vec.TaggedDocument(gensim.utils.simple_preprocess(line), [ct])
						ct += 1
						#exit()
						yield doc
					else:
						break
				except:
					pass

def isValidCmdLine():
	isValid = False

	if len(sys.argv) < 3:
		print("Insuffiient cmd line parameters")	
	elif not any("-fname=" in arg for arg in sys.argv):
		print("No fname passed")
	elif not any("-trainLimit=" in arg for arg in sys.argv):
		print("No training-example limit passed")
	elif not any("-iter=" in arg for arg in sys.argv):
		print("No n-iterations params passed")
	else:
		isValid = True

	return isValid

def usage():
	print("Usage: python3 ./Doc2Vec.py")
	print("\t-fname=[path to line-based training txt file]")
	print("\t-trainLimit=[num training sequences to extract from file; pass -1 for no limit]")
	print("\t-iter=[num iterations]")
	print("\t-vecSize=[OPTIONAL: non-default representation/encoding/feature vector size]")

def main():
	if not isValidCmdLine():
		print("Insufficient/incorrect args passed, see usage.")
		usage()
		return -1

	fname = ""
	limit = -1
	numIterations = 40
	minTermFrequency = 5
	vecSize = 300 #not sure what a good default is; need to check research papers; wikipedia claims 100 to 1000, which doesn't exactly narrow it down
	for arg in sys.argv:
		if "-fname=" in arg:
			fname = arg.split("=")[-1]
		if "-trainLimit=" in arg:
			limit = int(arg.split("=")[-1])
		if "-iter=" in arg:
			numIterations = int(arg.split("=")[-1])
		if "-minFreq=" in arg:
			minTermFrequency = int(arg.split("=")[-1])
		if "-vecSize" in arg:
			vecSize = int(arg.split("=")[-1])
		if "-window=" in arg or "-windowSize=" in arg:
			windowSize = int(arg.split("=")[-1])

	#yields facebook content objects' text as a stream of gensim.models.doc2vec.TaggedDocument objects
	stream = FbDocumentStream(fname, limit)

	print("Author recommends window size=10 for skipgram, 5 for CBOW word2vec models; this likely also applies to doc2vec.")
	print("According to wikipedia (unattributed!), 'Typically, the dimensionality of the vectors is set to be between 100 and 1,000'.")


	# __init__(self, documents=None, dm_mean=None, dm=1, dbow_words=0, dm_concat=0, dm_tag_count=1, docvecs=None, docvecs_mapfile=None, comment=None, trim_rule=None, callbacks=(), **kwargs)
	model = gensim.models.Doc2Vec(stream, windowSize=10, vector_size=vecSize, epochs=numIterations, min_count=minTermFrequency)
	print("Training completed")

	return 0

if __name__ == "__main__":
	main()

