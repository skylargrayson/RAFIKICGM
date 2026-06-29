.. RAFIKI documentation master file, created by
   sphinx-quickstart on Tue Jul 11 10:36:06 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to RAFIKI-CGM's documentation!
======================================

RAFIKI-CGM is an open-source python package developed to analyze simulated microwave and X-ray data. In its current form, it consists of a database with maps from 11 simulations
and the ability to generate stacked data products for easy comparison against observations. 

.. note:: 
	This project is under active development. There may still be bugs and limited functionality.

Features
--------
        - Generate thermal Sunyaev-Zeldovich data products including:
                
                - Radial profiles of the Compton-y parameter
                - Radial profiles of the moments of symmetry for the Compton-y parameter maps (extracting information about anisotropies in the data)
                - Stacks of thermal energy around galaxies as a function of stellar and halo mass. 
        
        - Generate soft X-ray emission data products including:

                - Radial profiles of stacked X-ray surface brightness
                - Radial profiles of the moments of symmetry for the surface brightness maps

        - Immense user flexibility in galaxy sample, including matching distributions from input catalog, setting limits by galaxy property, and selecting data from a range of redshift snapshots


Support
-------
If you have questions, contact Skylar Grayson sigrayso@asu.edu



Table of Contents
==================
.. toctree::
   usage
   overview/index
   running
   outputs
   cookbook/index
   generatingdata
   reference

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
