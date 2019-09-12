import sys
if sys.version_info.major < 3:
	print("ERROR use python3 instead of python 2.7")
	exit()

import json
from datetime import datetime
import dateutil.parser
import re

"""
Primitive storage object for holding headlines.
"""

class Headline():
	sourceUrlRegex = re.compile("/web/\d{14}")

	def __init__(self):
		self.Description = ""
		self.Headline = ""
		self.DT = ""
		self.Rank = -1
		self.URI = ""
		self.Thumbnail = ""
		self.Banner = ""
		self.Authors = ""
		self.IconType = ""
		self.Duration = ""
		self.Id = -1
		self.Layout = ""
		self.ArchiveSource = ""
		self.FullText = "" #likely only used a temporary storage location when fetching full article texts from a separate data source
		self.IsoWeek = -1 #see python datetime.isocalender(); per-week queries seem highly likely, so I decided to add this to Headline
		self.Attrib = dict() #catch all container for variable attributes from some snapshots (eg, the category of the headline, like 'sports', 'politics', or any other attributes)

	def GetFullText(self):
		return " ".join([self.Description,self.Headline,self.FullText])

	"""
	Initializes a presumably empty Headline object from a facebook /post object. This is not
	the same as an object returned by /ids queries.

	NOTE: THIS FUNCTION EXPECTS DB WAS CREATED USING json.dumps: Use only json.dumps and json.loads to serial/deserialize data from db!
	Also not that db connection @text_factory is set to unicode. By design, the facebook post db is now up to date per using only unicode!

	@fbObject: A dict as below

	{u'name': u"Why a high school that's just 5\\u0025 black is raising the Black Lives Matter flag", u'shares': u"{'count': 137}", u'caption': u'cnn.com', u'link': u'http:\\/\\/cnn.it\\/2GHlFYc', u'created_t
	ime': u'2018-02-02T18:45:10+0000', u'message': u"Of the 350 students at this high school, only 18 of them are black. But it's because of -- and not in spite of -- that fact that the school has raised the 
	Black Lives Matter flag.", u'id': u'5550296508_10157903708001509', u'description': u' '}
	"""
	def BuildFromFacebookPostSqlRecord(self, rec, description):

		#deserialize the complete fbObject from the sql record's 'data' column
		fbObject = dict()
		for i in range(len(rec)):
			if description[i][0] == "data":
				#print(str(type(rec[i]))+"    "+rec[i])
				fbObject = json.loads(rec[i]) #TODO: encode("ascii","ignore") breaks unicode, eg, for foreign languages. This is a serious TODO.

		#print(str(fbObject))

		message = fbObject.get("message",None)
		if message is not None:
			self.Description = message

		desc = fbObject.get("description",None)
		if desc is not None:   #both message and description often contain synopsis info
			if len(desc) > 8 and self.Description != desc: #detects if description is same as @message, from above
				#check if Description is prefix of (or equal to) desc; an annoyance, but necessary for data integrity, since message or description may simply be a truncated version of the other
				if self.Description in desc:
					self.Description = desc #message is a prefix of @description, so overwrite previous description (eg from @message) with longer synopsis
				elif desc not in self.Description: #append @description, but only after verifying it is not a perfix of @message
					self.Description = self.Description + " " + desc
				else:
					self.Description += desc

		headline = fbObject.get("name",None)
		if headline is not None:
			self.Headline = headline
		else:
			#print("ERROR no headline found, defaulting to message, for fbObject: "+fbObject["id"]+"\n"+str(fbObject))
			self.Headline = self.Description

		dtString = fbObject.get("created_time", None)
		if dtString is not None:
			self.DT = datetime.strptime(dtString,"%Y-%m-%dT%H:%M:%S+0000")
			self.IsoWeek = self.DT.isocalendar()[1]
		else:
			print("ERROR no created_time for fbObject: "+str(fbObject["id"]))
			self.DT = datetime.now()

		#used as backup link/url
		fbId = fbObject.get("id", None) #cannot store @id in post in Headline.Id, because Headline.Id is int; fb-post id's are strings: '55555555_1111111'
		if fbId is not None:
			self.Attrib["fb_id"] = fbId

		url = fbObject.get("link", None)
		if url is not None:
			self.URI = url
		#try to extract a uri from the message/description, where some news orgs stuff it
		elif "http" in self.Description:
			link = self.Description.split("http")[1].split(" ")[0].rstrip(".")
			self.URI = link
		elif "@" in self.Description: #in many cases, the link in the message is an email address: mail@npr.org. This is a very imprecise method for getting it
			addr = self.Description.split("@")[0].split(" ")[-1]
			domain = self.Description.split("@")[1].split(" ")[0]
			self.URI = addr+"@"+domain
		else:
			#It is fine for posts to not have links, for instance 6758258138_10155483495633139
			#"Susan Hutchison, chair of the Washington State Republican Party, will be on The Record today. What questions do you want us to ask her?"
			#which is just a comments post with no related article.
			print("WARNING no url/link found for facebook object: "+fbObject["id"]+"\n"+str(fbObject))
			self.URI = "https://www.facebook.com/"+str(self.Id)

		self.Attrib["share_count"] = 0
		shareData = fbObject.get("shares",None)
		if shareData is not None:
			self.Attrib["shares"] = shareData #get the shares dictionary
			self.Attrib["share_count"] = int(self.Attrib["shares"]["count"])
		else: #there is often no shares dict in the fbObject, such as if the item is very new and hasn't been shared; hence this sets default values to 0
			self.Attrib["shares"] = {"count": 0}

		return self

	"""
	Initializes a presumably empty Headline object from a stinger object, containing the minimum keys title, description, datetime, url.

	"""
	def BuildFromStingerSqlRecord(self, rec, description):
		i = 0

		#if type(record) != list:
		#	rec = list(record)
			
		print("record: "+str(rec))
		while i < len(rec):
			if "title" == description[i][0]:
				self.Headline = rec[i]
			elif "id_key" == description[i][0]:
				self.Id = int(rec[i])
			elif "description" in description[i][0]:
				self.Description = rec[i].lower()
			elif "datetime" in description[i][0]:
				dateStr = rec[i]
				self.DT = dateutil.parser.parse(dateStr)
				#self.DT = datetime.strptime(dateStr, "%a %b %d %H:%M:%S %Z %Y")  #formatting: "Sun Oct 23 01:46:21 UTC 2016"
				self.IsoWeek = self.DT.isocalendar()[1]
			elif "url" in description[i][0]:
				self.URI = rec[i]
			#not required, but common extra columns
			elif "rank" in description[i][0]:
				self.Rank = int(rec[i].strip())
			elif "authors" in description[i][0]:
				self.Authors = rec[i]
			elif "source" in description[i][0]:
				self.Attrib["source"] = rec[i]
			else:
				print("WARN in BuildFromStingerSqlRecord(): field >"+description[i][0]+"< not found! Adding to Attrib") 
				self.Attrib[description[i][0]] = rec[i]
			i += 1

		return self

	def Print(self):
		self.PrintTerse()
		print("Description: "+self.Description)
		print("Iso week: %d" % self.IsoWeek)
		print("Rank: %d" % self.Rank)
		print("Id: %d"% self.Id)
		print("Authors: %s" %self.Authors)
		print("ArchiveSource: %s" % self.ArchiveSource)
	
	def PrintTerse(self):
		print("%s::%s::%s" % (self.Headline,self.URI,str(self.DT)))
	
	"""
	Gets the value for a given field via the field string.
	
	TODO: This if-else is awful. Use a dictionary instead.
	"""
	def GetValue(self, field):
		value = ""
		field = field.lower()
		
		if field == "description":
			value = self.Description
		elif field == "headline":
			value = self.Headline
		elif field == "dt":
			value = self.DT
		elif field == "week":
			value = self.IsoWeek
		elif field == "isoweek":
			value = self.IsoWeek
		elif field == "rank":
			value = self.Rank
		elif field == "uri":
			value = self.URI
		elif field == "thumbnail":
			value = self.Thumbnail
		elif field == "banner":
			value = self.Banner
		elif field == "icontype":
			value = self.IconType
		elif field == "duration":
			value = self.Duration
		elif field == "id":
			value = self.Id
		elif field == "layout":
			value = self.Layout
		elif field == "authors" or field == "author":
			value = self.Authors
		elif field == "archivesource":
			value = self.ArchiveSource
		else:
			print("ERROR field "+field+" not found")
			
		return value
			
	"""
		Given string formatted exactly as "Sun Oct 23 01:46:21 UTC 2016", returns iso-calendar week number.
	"""
	def GetIsoWeek(self,utcString):
		day = int(utcString[8:10])
		year = int(utcString[24:28])
		month = utcString[4:7].lower()
		if month == "jan":
			month = 1
		elif month == "feb":
			month = 2
		elif month == "mar":
			month = 3
		elif month == "apr":
			month = 4
		elif month == "may":
			month = 5
		elif month == "jun":
			month = 6
		elif month == "jul":
			month = 7
		elif month == "aug":
			month = 8
		elif month == "sep":
			month = 9
		elif month == "oct":
			month = 10
		elif month == "nov":
			month = 11
		elif month == "dec":
			month = 12
		else:
			month = -1
			print("ERROR month not found in Headline.GetIsoWeek: "+month)
			exit()
		
		weekNum = datetime.date(year, month, day).isocalendar()[1]
		return weekNum

	#Restrict hit detection to headlines; this is important for disambiguating headlines uniquely on a topic (and not on
	#other topics), since the larger text of an article will usually include multiple topics. IOW, this identifies
	#content uniquely identifying a particular topic, even though it could include ther topics in its body.
	def HasTopicalHeadlineHit(self, topics):
		for topic in topics:
			if topic.lower() in self.Headline:
				return True
		return False

	def HasTopicHit(self, topics):
		"""
			Returns whether or not headline headline or description contains any topic words in @topics, case-insensitively
			throughout the entire body of information. This is probably too broad to use for topical cross filtering,
			since the full body of a headline will usually convey information about multiple topics/participants.
			@topics: A list of topic terms.
		"""
		return self.CountTopicHits(topics) > 0
		
	#Note this counts the frequency of the hits, not just number of hits; so if a term occurs twice, 2 will be included in the sum
	def CountTopicHits(self, topics):
		txt = self.GetFullText().lower()
		return sum([txt.count(topic.lower()) for topic in topics])
	
	"""
	Used to remove terms, for various filtering.

	Note that this removes any occurrence of @term in @terms, such that longer term 
	references will be left as potential fragments: "Trump's day at the office..."
	will be converted to "'s at the office..." for @terms=["Trump"].

	Also note the case-sensitivity; this method is case-sensitive.
	"""
	def StripTerms(self, terms):
		for term in terms:
			self.Headline = self.Headline.replace(term,"")
			self.Description = self.Description.replace(term,"")
			self.FullText = self.FullText.replace(term,"")

	#Used to replace term
	def ReplaceTerm(self, target, replacement):
		self.Headline = self.Headline.replace(target, replacement)
		self.Description = self.Description.replace(target, replacement)
		self.FullText = self.FullText.replace(target, replacement)
		return self

	"""
	@dateLow/high: Datetime.date objects with which to compare, inclusively.
	"""
	def IsInDateRange(self, lowDate, highDate):
		return self.DT.date() >= lowDate and self.DT.date() <= highDate

	"""
	Inverse of ToDict(), given a python dictionary, maps its keys  to corresponding headline data members.
	"""	
	def FromDict(self,d):
		success = len(d.keys()) > 4
		for key in d.keys():
			if key == "description":
				self.Description = d[key]
			elif key == "headline":
				self.Headline = d[key]
			elif key == "datetime": #datetime must be formatted as "%Y-%m-%d %H:%M:%S", like isoformat() result but without microseconds
				try:
					self.DT = datetime.strptime(d[key], "%Y-%m-%d %H:%M:%S")
					self.IsoWeek = self.DT.isocalendar()[1]
				except:
					success = False
					print("ERROR could not parse datetime str into Headline.DT: "+d[key])
					self.DT = d[key]
			elif key == "rank":
				self.Rank = int(d[key])
			elif key == "uri":
				self.URI = d[key]
			elif key == "thumbnail" or key == "imageuri":
				self.Thumbnail = d[key]
			elif key == "banner":
				self.Banner = d[key]
			elif key == "authors":
				try:
					self.Authors = d[key]
				except:
					success = False
					traceback.print_exc()
					print("ERROR failed to deserialize Headline authors: "+str(d[key]))
					self.Authors = d[key]
			elif key == "duration":
				self.Duration = d[key]
			elif key == "id":
				self.Id = int(d[key])
			elif key == "layout":
				self.Layout = d[key]
			elif key == "fullText":
				self.FullText = d[key]
			elif key == "isoWeek":
				self.IsoWeek = int(d[key])
			elif key == "attrib":
				try:
					self.Attrib = d[key]
				except:
					success = False
					traceback.print_exc()
					print("ERROR could not deserialize Headline attrib dict: "+str(d[key]))
					self.Attrib = dict()
			elif key == "archiveSource":
				self.ArchiveSource = d[key]
			else:
				print("ERROR key not found in Headline.FromDict(): "+key)

		return success

	def ToDict(self,filterSource=True):
		keyVals = dict()

		keyVals["description"] = self.Description
		keyVals["headline"] = self.Headline
		#the conversion of DT to string is required for serialization
		keyVals["datetime"] = self.DT.strftime("%Y-%m-%d %H:%M:%S") #same as dt.isoformat(), but without microseconds or 'T'
		keyVals["rank"] = self.Rank
		keyVals["banner"] = self.Banner
		keyVals["authors"] = self.Authors
		keyVals["duration"] = self.Duration
		keyVals["id"] = self.Id
		keyVals["layout"] = self.Layout
		keyVals["fullText"] = self.FullText
		keyVals["isoWeek"] = self.IsoWeek
		keyVals["attrib"] = self.Attrib

		if filterSource: #strip or omit source info
			keyVals["uri"] = self._getSourceUrl(self.URI)  #source info should be filtered on ingress/read, not here, this is just a second egress protection
			keyVals["thumbnail"] = self._getSourceUrl(self.Thumbnail)			
		else:
			keyVals["uri"] = self.URI
			keyVals["thumbnail"] = self.Thumbnail
			keyVals["archiveSource"] = self.ArchiveSource

		return keyVals

	def _getSourceUrl(self, url):
		#print(str(type(url)))
		match = self.sourceUrlRegex.search(url)
		if match is not None:
			return url[match.end()+1:] # [1:] to slice the leading '/'
		return url

	"""
	Converts Headline to a string representation as a python dict of key value pairs.
	@filterSource: If true, information that indicates data sources will be stripped.
	"""
	def ToString(self, filterSource=True):
		return json.dumps(self.ToDict(filterSource), sort_keys=True, ensure_ascii=False)

	"""
	Populates the object from a sql-lite record, as would be returned by a db SELECT.

	@record: ordered column values of the record
	@description: the *ordered* column names corresponding in order with @record.

	the cursor.description object, which is a tuple of tuples, formatted like:
		(('Id', None, None, None, None, None, None), ('layout', None, None, None, None, None, None), ('description', 
	Where the first item of each tuple is a the column name for that column index.

	Full description (subject to change) 
		(('Id', None, None, None, None, None, None), ('layout', None, None, None, None, None, None), 
		('description', None, None, None, None, None, None), ('headline', None, None, None, None, None, None),
		('uri', None, None, None, None, None, None), ('rank', None, None, None, None, None, None), 
		('duration', None, None, None, None, None, None), ('thumbnail', None, None, None, None, None, None), 
		('archiveSource', None, None, None, None, None, None), ('iconType', None, None, None, None, None, None))
	"""
	def BuildFromSqlRecord(self, record, description, filterSource=True):
		i = 0
		#print("rec: "+str(record))
		#print("type: "+str(type(record)))
		if type(record) != list:
			rec = list(record)
			
		#print("record: "+str(rec))
		while i < len(rec):
			if "Id" == description[i][0]:
				self.Id = rec[i]
			elif "authors" in description[i][0]:
				self.Authors = rec[i]
			elif "layout" in description[i][0]:
				self.Layout = rec[i]
			elif "description" in description[i][0]:
				self.Description = rec[i].lower()
			elif "headline" in description[i][0]:
				self.Headline = rec[i].lower()
			elif "link" in description[i][0]:  #'link' IS NOT TO BE USED ANYWHERE, nor is expected. This is solely a bandaid because some snapshots incorrectly stored 'link' instead of 'uri'.
				self.URI = rec[i]
			elif "uri" in description[i][0]:
				self.URI = rec[i]
			elif "rank" in description[i][0]:
				self.Rank = int(rec[i])
			elif "duration" in description[i][0]:
				self.Duration = rec[i] 
			elif "thumbnail" in description[i][0] or "imageuri" in description[i][0]:
				self.Thumbnail = rec[i] 
			elif "iconType" in description[i][0]:
				self.IconType = ""
				if rec[i] != None:
					self.IconType = rec[i]
			elif "isprimary" in description[i][0].lower():
				self.Attrib["isPrimary"] = rec[i].lower()
				#print("IsPrimary: {}".format(rec[i].lower()))
			elif "archiveSource" in description[i][0]:
				self.ArchiveSource = rec[i] 
				dateStr = self.ArchiveSource.replace("_", " ")
				#print("ARCHIVE SOURCE: "+dateStr)
				self.DT = datetime.strptime(dateStr, "%a %b %d %H:%M:%S %Z %Y")  #formatting: "Sun Oct 23 01:46:21 UTC 2016"
				self.IsoWeek = self.DT.isocalendar()[1]
			else:
				#print("WARN in BuildFromSqlRecord(): field >"+description[i][0]+"< not found! Adding to Attrib") 
				self.Attrib[description[i][0]] = rec[i]
			i += 1

		if filterSource:
			self.ArchiveSource = self._getSourceUrl(self.ArchiveSource)
			self.URI = self._getSourceUrl(self.URI)
			self.Thumbnail = self._getSourceUrl(self.Thumbnail)

	#A temporary hack to test/explore the harvard dataset
	def BuildFromHarvardRecord(self, headline, dt, shareCount=0):
		self.DT = dt
		self.IsoWeek = self.DT.isocalendar()[1]
		self.Headline = headline
		self.Attrib["share_count"] = shareCount
		return self
		

