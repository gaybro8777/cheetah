<div align="center" style="-moz-user-select: none; user-select: none; pointer-events: none; cursor: default; text-decoration: none; color: black;">
<img src="./misc/img/cheetah_invert.jpeg" />
<img src="./misc/img/cheetah_logo_invert.jpeg" />
</div>
&nbsp;

Tired of unrelenting fake news?

Skeptical of misinformation claims made by tinpot 'experts' [actively engaging in it themselves](https://www.nytimes.com/2018/12/19/us/alabama-senate-roy-jones-russia.html)?

Worried about the encroachment on public information by a handful of regionally and politically isolated tech monopolies?

Have no fear, Cheetah is here!

Cheetah is a machine-learning repository containing counter-misinformation methods and results for reproduction.
Techniques graduate here from other data-extraction and algorithmic projects. While this repro
contains algorithms and code, its intent is not as a library but to provide a self-contained repro environment for research and dissemination.
The purpose of this project is to inform and educate the public about the new public nuisance of misinformation, using open-source methods to quantify it.
Because the reality is that reverse-engineering misinformation actors (algorithms, search engines, sites, even entire platforms) is actually very easy,
using off-the-shelf NLP and machine learning.

Run the code and see for yourself. A work-in-progress paper is provided [here](https://www.nytimes.com/2018/12/19/us/alabama-senate-roy-jones-russia.html).
Most of this is living code/documentation, since I'm very much a disciple of a "code, not papers" ethic, given the sluggish, elitism of the latter.

## Running Cheetah

Cheetah is simple to run. Cd to src/ and run main.py with python:

* cd src/
* python3 main.py

The main menu will present various options.
The first task is to download the FastText english term-vector model from Facebook research to the 
models/english/ directory. I provided a tool to do this, or you may manually download the '.text' vector model via the website:
* https://fasttext.cc/docs/en/crawl-vectors.html
* --> english -> '.text' -> downloaded file is named "cc.en.300.vec.gz"
* **NOTE: do not download the .bin model**, get the much smaller ".text" model.
* Unzip the model and place it at models/english/cc.en.300.vec.gz

Once downloaded, select 'cheetah repro' from the main menu options and let it complete. The 
calculations take a few minutes to complete on a modest machine.

## Requirements

* Python 3.5+

Non-standard packages:
* matplotlib
* numpy
* gensim
* unidecode

To install these packages, use:
* pip install -r requirements.txt

Python dependencies are what they are, so grapple with your environment as needed to get these installed consistently.

I apologize, because the goal is to make Cheetah as self-contained as possible, but there may be other required
python packages I missed. If you see exceptions having to do with missing packages, just install
them individually with pip3 and retry:

	pip3 install --user [package name]

## TODO
* Dockerizing Cheetah is in progress.
* Pyodide demonstration


