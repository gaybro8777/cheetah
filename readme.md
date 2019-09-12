The steps to run the Cheetah repro are as follows, and are provided by the tool. But please read 
the full readme.
# Download the english '.text' term vector model from facebook research (4.5GB, which may take up to an hour on slow connections)
# Run main.py under python3 and select 'cheetah repro' in the main menu. Output results will be displayed and also stored in the results/ directory

Requirements:
* Python 3.5+
* tabs >> spaces

Non-standard Packages:
* matplotlib
* numpy
* gensim
* unidecode (is this non-standard?)

I apologize because I want this to be as self-contained as possible, but there may be other required
python packages I am missing. If you see exceptions having to do with missing packages, just install
them individually with pip3 and retry:
	pip3 install --user [package name]

Cheetah is simple to run. Cd into src/ and run main.py with python3:
	cd src/
	python3 main.py

The main menu will present various options.
The first task is to download the FastText english term-vector model from Facebook research to the 
models/english/ directory. I provided a tool to do this, but you can also just manually download 
the '.text' vector model via the website:
* https://fasttext.cc/docs/en/crawl-vectors.html
* -> english -> '.text' -> downloaded file is named "cc.en.300.vec.gz"
* Don't download the .bin model! Get the .text model
* Unzip the model and place it at models/english/cc.en.300.vec.gz

Once downloaded, just select 'cheetah repro' from the main menu options and let it complete. The 
calculations take a few minutes to complete on a modest machine.


