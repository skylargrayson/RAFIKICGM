Dev: Generating Your Own Maps
=============================

.. note:: 
	This page is out of date and will be updated shortly. 

RAFIKI-CGM automatically includes the necessary data products for 9 RAFIKI simulations, SIMBA, and EAGLE. Here, we provide information on how to generate these data products for other simulation snapshots
if you are interested in expanding the range of snapshot redshifts or using your own code. Currently, the scripts shared here are only designed to work with SIMBA-like and EAGLE-like snapshots. 

The developer/making_maps folder in the RAFIKI-CGM github contains example scripts that can be used to generate the data products following the methodology described below.

tSZ 
---
You can use RAFIKI-CGM to create a map of the Compton-y parameter projected along a snapshot box. This converts the particle data to a two-dimensional pixelated map of the Compton-y parameter, defined as :math:`y = \sigma_T \int dl \ n_e \frac{k(T_e-T_{CMB})}{m_e c^2}` 
This is done via the generating_sz_data and generating_sz_data_eagle functions and a full routine can be found in making_sz_maps.py. 

The Compton-y parameter is calculated following 
:math:`y = \sigma_T \int dl n_e \frac{k (T_e-T_{CMB})}{m_e c^2}`

The integration along the line of sight is performed using yt's ProjectionPlot function of the pressure field, with a specific Fixed Resolution Buffer set by default to generate a pixel scale of 3 arcseconds.

The scripts provided also remove ISM particles, defined by a density threshold of :math:`n_H>0.1 cm^{-3}` as those are artificially pressurized in SPH codes, and in the SIMBA script also removes active wind particles as 
those are decoupled from the hydrodynamics. The simulation box is projected along the x, y, and z axes to generate three Compton-y maps per snapshot. 



X-ray
-----
The X-ray pre-made data takes the form of particle datasets around the 500 most massive galaxy in the box. A full example routine can be found in making_particlesets_simba.py and making_particlesets_eagle.py

This process uses yt to cut a sphere 1500 kpc in radius around each galaxy and save only the datasets relevent for generating mock X-ray data: positions, velocities, density, emission measure, temperature, metallicity, mass, and smoothing length.
For every galaxy, an individual hdf5 dataset is saved. 


Galaxy Catalogs
---------------

RAFIKI-CGM provides pre-made galaxy sample catalogs. You will need to generate your own catalog with the same format for use in the RAFIKI-CGM pipeline if you wish to add additional simulations/snapshots. 

The Jupyter notebook make_galaxy_catalog.ipynb walks through this process for both SIMBA and EAGLE. 






