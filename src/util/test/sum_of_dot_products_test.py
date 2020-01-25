"""
Had to convince myself a sum of sum of dot products factors like I said it did...

For two lists of vectors X and Y, the sum of their cosine similarities is a double summation:

	for x in X:
		for y in Y:
			total += x dot y / ( |x| |y| )

If you do sum re-arranging/factoring, you can show that this simplifies to the much faster:

	for x in X:
		y' = sum([ (y / |y| for y in Y ])
		total += (x / |x|) dot y'

This script verifies this empirically, but is also for observing any numerical rounding
of either implementation.

The implication is that cheetah calculations can be made much faster for two reasons:
1) The sums factor, like above
2) More importantly, based on (1) the entire summation over sentiment/signal terms can
be removed and pre-computed! Holee-toledoh
"""

import numpy as np


def cossim(x,y):
	return x.dot(y) / (np.linalg.norm(x) * np.linalg.norm(y))

def cossim_double_sum(x_seq, y_seq):
	"""
	Implementation of the canonical definition of cossim for two sets of vectors.
	@x_seq, y_seq: Each a list of vectors in R^k
	"""
	return sum( [cossim(x,y) for x in x_seq for y in y_seq] )

def factored_double_sum(x_seq, y_seq):
	"""
	Implementation of the simplified/optimized version of cossim for two sets of vectors.
	@x_seq, y_seq: Each a list of vectors in R^k
	"""
	total = 0.0
	for x in x_seq:
		y_prime = np.sum([y / np.linalg.norm(y) for y in y_seq], axis=0)
		total += (x / np.linalg.norm(x)).dot(y_prime)
	return total

def rand_vec_seq(dim, nvecs):
	return [np.random.rand(dim)*10 for i in range(nvecs)]

def test():
	nvecs = 200
	ntests = 10
	dim = 400

	for i in range(ntests):
		x_seq = rand_vec_seq(dim, nvecs)
		y_seq = rand_vec_seq(dim, nvecs)
		cs1 = cossim_double_sum(x_seq, y_seq)
		cs2 = factored_double_sum(x_seq, y_seq)
		print("{} =?= {}".format(cs1, cs2)) 

test()















