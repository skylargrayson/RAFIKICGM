Installation
============


RAFIKI-CGM can be found at this github page,

Or downloaded using the command line with:

.. code-block:: console

	$ git clone 

Dependencies
------------
RAFIKI-CGM is a python-based code requiring the following packages:

- `yt <https://yt-project.org/>`_ (version 4.1.3 or higher)
- `NumPy <https://numpy.org/>`_
- `SciPy <https://scipy.org/>`_
- `Astropy <https://www.astropy.org/>`_ 
- `h5py <https://www.h5py.org/>`_
- `matplotlib <https://matplotlib.org/>`_ 
- `cython <https://cython.org/>`_ 
- `psutil <https://pypi.org/project/psutil/>`_ 
- `joblib <https://joblib.readthedocs.io/en/stable/>`_ 
- `caesar <https://caesar.readthedocs.io/en/latest/getting_started.html#>`_ 
- `pyXSIM <https://hea-www.cfa.harvard.edu/~jzuhone/pyxsim/index.html>`_ 
- `SOXS <https://hea-www.cfa.harvard.edu/soxs/>`_


We recommend installing ``yt`` via Anaconda:

.. code-block:: console

	$ conda install -c conda-forge yt


If you are only interested in generating tSZ data products you do not need ``pyXSIM`` or ``SOXS`` (although you will need to comment out their import statement in the pipeline scripts). 



