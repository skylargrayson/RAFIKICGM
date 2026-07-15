Quickstart
==========

This page walks you from installation to your first mock observations using RAFIKI-CGM. 

Install
-------
 
.. code-block:: bash
 
   pip install rafikicgm
 
Or, to install the latest development version from source:
 
.. code-block:: bash
 
   git clone https://github.com/skylargrayson/RAFIKICGM.git
   cd RAFIKICGM
   pip install -e .
 
RAFIKI-CGM is a python-based code requiring the following packages, which should be automatically installed by pip. 

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



Basic Configuration
-------------------

RAFIKI-CGM is ran from a YAML config file. 
A complete, working config is given in the examples directory of the github and in :doc:`running`, where every key is also described in detail.


Run the Pipeline
----------------

RAFIKI-CGM can be run from the command line:

.. code-block:: bash

    rafikicgm run quickstart_config.yaml


Check the Output
----------------

A successful run will produce 

* ``./outputs/quickstart_szdat.h5`` -- the simulated SZ data 
* ``./outsputs/quickstart_xraydat.h5`` -- the simulated X-ray data

You can examine the structure of these output files in more detail in :doc:`outputs`. 

Next Steps
----------

* Learn more in :doc:`overview`
* Walk through a full example in :doc:`cookbook`
* See every config option in :doc:`running`
