import yt
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import gridspec
import numpy as np
import caesar
import pandas as pd
import csv
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename
from astropy.convolution import Gaussian2DKernel, interpolate_replace_nans
from astropy.convolution import convolve, convolve_fft
import scipy.ndimage
from random import randint
import math
from scipy.ndimage.interpolation import geometric_transform
#from Galaxy_data import *
from scipy.stats import bootstrap


def gen_random_indices(index_set, gen_size):
    """
    Generates a list of indicies by random sampling with replacement
        
    :param index_set: List of values to sample from
    :type index_set: list[float]
    :param gen_size: Length of final resampled list you want
    :type gen_size: int
    :return: a list of length gen_size randomly chosen from index_set
    """
    return np.random.choice(index_set, size=gen_size, replace=True)

def single_catalog_bootstrap(data, boot_size, loop_size):
    """
    Calculates the means of a list of catalogs, useful when determining things like correlation matrices

    :param data: List of pandas tables
    :type data: list[float]
    :param boot_size: Sample size
    :type boot_size: int
    :param loop_size: How many times to do the bootstrapping
    :type boot_size: int
    """
    if type(data)!=list:
        print("Data must be provided as a list... exiting...")
        return None
    dlen = len(data)
    dlen2 = len(data[0])    
    print(dlen, len(data[0]))
    
    result = []
    for l in range(loop_size):
        indices = gen_random_indices(np.arange(dlen2), boot_size)
        result.append([np.mean(np.take(data[d], indices)) for d in range(dlen)])
    result = np.array(result)
    return result


