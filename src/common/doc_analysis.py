#just for exploratory testing
import sklearn.linear_model
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.decomposition import PCA
from sklearn import manifold
from sklearn import preprocessing
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

from mpl_toolkits.mplot3d import Axes3D
from time import time

"""
This script is under construction, directly copied over from VecSent.
This is mostly for visualization and data exploration.

Experimental script testing various regressors on the task of predicting social media content share counts from document vectors.
This is all based on the model:
	1) Convert documents set D to a set of vectors, V
	2) Regress on V against share counts
So static document analysis: build the document model, then regress, separately. Not very robust.
A real method would optimize the document vectors as it regressed, like an RNN to model the documents, terminating in a share target.

Note that all methods are dependent on the quality of the doc2vec representation of content, so things like doc2vec vec-size are
a parameter.
"""

def tsne(X, numComponents):
	"""
	@numComponents: the number of components
	@X: 
	"""
	t0 = time()
	print("Running t-sne...")
	tsne = manifold.TSNE(n_components=numComponents, init='pca', random_state=0)
	#X = X[0:min(6000,X.shape[0]),:]
	#X = X[0:min(6000,X.shape[0]),:]
	Y = tsne.fit_transform(X)
	t1 = time()
	print("t-SNE: %.2g sec" % (t1 - t0))
	fig = plt.figure(figsize=(15, 10))
	#ax = fig.add_subplot(2, 5, 10)
	plt.scatter(Y[:, 0], Y[:, 1], c="b", cmap=plt.cm.Spectral)
	plt.title("t-SNE (%.2g sec)" % (t1 - t0))
	#ax.xaxis.set_major_formatter(NullFormatter())
	#ax.yaxis.set_major_formatter(NullFormatter())
	plt.axis('tight')
	plt.show()

	return tsne, Y

def pca_analysis(X, numComponents=16, colors=None, startAxis=0):
	"""
	@X:
	@numComponents: number of components to plot
	"""
	#run PCA on the data, just for exploration
	#startAxis: The first principal component from which to plot the next three dimensions
	pca = PCA(n_components=numComponents)
	pca.fit(X)
	limit = 3000
	print("Components' explained variance ratios:\n\t {}".format(pca.explained_variance_ratio_))
	print("Singular values:\n\t{}".format(pca.singular_values_))
	#plot the first three components
	Z = pca.transform(X)
	x1 = Z[0:min(limit,Z.shape[0]), 0+startAxis]
	x2 = Z[0:min(limit,Z.shape[0]), 1+startAxis]
	x3 = Z[0:min(limit,Z.shape[0]), 2+startAxis]
	colors = colors[0:min(limit, len(colors))]
	fig = plt.figure(1, figsize=(20,10))
	ax = Axes3D(fig)
	ax.scatter(x1, x2, x3, c=colors)
	plt.show()

	return pca, Z

def evaluateModel(model, X, y):
	"""
	Plots actual y value on x axis, and predicted value on y-axis. Thus accurate predictions will
	cluster around the line y=x, giving a visualization of model behavior. Don't expect nice clustering
	for share data, since sharing is so non-linear and chaotic; if there is any central tendency at all,
	that may be 'success'.
	@model: 
	@X: 
	@y: the targets (share counts)
	"""
	limit = 2500
	pred_y = model.predict(X)

	#sample only a subset of points to plot
	s_pred_y = pred_y[0:min(limit,pred_y.shape[0])]
	s_y = y[0:min(limit, y.shape[0])]
	fig, ax = plt.subplots()
	ax.scatter(s_y, s_pred_y, edgecolors=(0, 0, 0))
	ax.plot([s_y.min(), s_y.max()], [s_y.min(), s_y.max()], 'k--', lw=4)
	ax.set_xlabel('Actual')
	ax.set_ylabel('Predicted')
	plt.show()

def plot2d(x, y):
	#sample points
	limit = 3000
	s_x = x[0:min(limit,x.shape[0])]
	s_y = y[0:min(limit,y.shape[0])]

	fig, ax = plt.subplots()
	ax.scatter(s_x, s_y, edgecolors=(0, 0, 0))
	ax.plot([x.min(), x.max()], [0, y.max()], 'k--', lw=4)
	#ax.set_xlabel('Actual')
	#ax.set_ylabel('Predicted')
	plt.show()

def plot3d(x,y,z):
	limit = 2000
	s_x = x[0:min(limit,x.shape[0])]
	s_y = y[0:min(limit,y.shape[0])]
	s_z = z[0:min(limit,z.shape[0])]

	fig = plt.figure(1, figsize=(20,10))
	ax = Axes3D(fig)
	ax.scatter(s_x, s_y, s_z)
	plt.show()


def doc_analysis():
	pcaComponents = 50
	minShareThreshold = 500 #omit rows with share counts less than this
	maxShareThreshold = 20000

	modelPath = "model_temp.csv"
	for arg in sys.argv:
		if "-modelPath=" in arg:
			modelPath = arg.split("=")[1]

	data = pd.read_csv(modelPath, header=None)
	print("Shuffling data... this must be done to verify inputs are unordered before separating test/train sets")
	data = shuffle(data)
	print("columns: {} unfiltered shape: {}".format(data.columns, data.shape))
	ncols = len(data.columns)
	data = data[data[ncols-4] > minShareThreshold]  #filter data by share threshold
	data = data[data[ncols-4] < maxShareThreshold]
	print("Examples after share filtering: {}".format(data.shape))
	#filter by partisan content, indicated by 'b' or 'r' in last column
	#print("{}".format(data[ncols-1]))
	print("Filtering by color...")
	data = data[data[ncols-1].str.contains(".*r|b|p|m.*")]

	colors = data.iloc[:,ncols-1].values
	#print("Colors: {}".format(colors))
	X = data.iloc[:,0:-4].values
	xdim = X.shape[1]
	pcaComponents = min(xdim, pcaComponents)

	print("n: {} xdim: {}".format(X.shape[0], X.shape[1]))
	y = data.iloc[:,-4].values
	print("X: {}  y: {}".format(X.shape, y.shape))

	if "--standardize" in sys.argv: #normalize input space to zero mean and unit variance
		print("Standardizing input space...")
		X = preprocessing.scale(X)
		y = preprocessing.scale(y)

	if "--logSpace" in sys.argv:
		y = np.log(y+1)  #plus 1, to prevent log(0)

	testSize = 0.1
	#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=testSize, random_state=0, shuffle=False) #useful, but sklearn does not specify how to get non-randomized splits; that is, split the data in contiguous order-preserving chunks
	trainSize = int((1.0 - testSize) * X.shape[0])
	X_train = X[0:trainSize,:]
	y_train = y[0:trainSize]
	X_test = X[trainSize:,:]
	y_test = y[trainSize:]
	color_train = colors[0:trainSize]
	color_test = colors[trainSize:]

	model = sklearn.linear_model.LinearRegression(normalize=False)
	print("Fitting model...")
	model.fit(X_train, y_train)
	score = model.score(X_train, y_train)
	print("Linear R^2 TRAIN SCORE: {}".format(score))
	evaluateModel(model, X_train, y_train)
	score = model.score(X_test, y_test)
	print("Linear R^2 TEST SCORE: {}".format(score))
	evaluateModel(model, X_test, y_test)


	#cv_mse = cross_val_score(estimator = regressor, X = x_train, y = y_train, cv = 10, scoring='neg_mean_squared_error')
	#cv_mse.mean()

	pca, Z_train = pca_analysis(X_train, pcaComponents, color_train, startAxis=0)
	#tsne(Z[:,0:min(5,pcaComponents)], 2)
	nComponents = min(pcaComponents,xdim)
	model.fit(Z_train[:,0:nComponents], y_train)
	score = model.score(Z_train[:,0:nComponents], y_train)
	print("PCA Linear R^2 TRAIN SCORE {} pca components: {}".format(score, nComponents))
	evaluateModel(model, Z_train[:,0:nComponents], y_train)
	#plot the actual share counts and only the first pca component
	plot2d(Z_train[:,0], y_train)
	plot3d(Z_train[:,0], Z_train[:,1], y_train)

	#exit()
	#mlp regression
	print("Training multilayer neural net...")
	nn = MLPRegressor(activation="tanh", solver="adam", hidden_layer_sizes=(1000), max_iter=20000) #solver = {adam, lbfgs, sgd}
	nn.fit(X_train, y_train)
	score = nn.score(X_train, y_train)
	print("Neural net R^2 training score: {}".format(score))
	evaluateModel(nn, X_train, y_train)
	score = nn.score(X_test, y_test)
	print("Neural net R^2 test score: {}".format(score))
	evaluateModel(nn, X_test, y_test)



	"""
	#run a neural net, just to see if a generic non-linear regression can top linear regression
	hiddenSize = int(xdim/10)
	mlr = MLPRegressor(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(xdim, hiddenSize), random_state=1)
	mlr.fit(X,y)
	"""


	"""
	#See: http://scikit-learn.org/stable/auto_examples/linear_model/plot_ols.html
	print("Mean squared error: %.2f"
		  % mean_squared_error(diabetes_y_test, diabetes_y_pred))
	# Explained variance score: 1 is perfect prediction
	print('Variance score: %.2f' % r2_score(diabetes_y_test, diabetes_y_pred))
	"""




