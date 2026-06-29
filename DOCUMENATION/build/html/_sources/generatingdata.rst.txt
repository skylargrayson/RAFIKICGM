Generating Your Own Maps
========================

RAFIKI-CGM automatically includes the necessary data products for 9 RAFIKI simulations, SIMBA, EAGLE, and EAGLE-AGNdT9. However, the package
does include pipelines needed for generating your own data products from other simulations. In its current form, these are limited to SIMBA and EAGLE runs.


tSZ 
---
You can use RAFIKI-CGM to create a map of the Compton-y parameter projected along a snapshot box. This converts the particle data to a two-dimensional pixelated map of the Compton-y parameter, defined as :math:`y = \sigma_T \int dl \ n_e \frac{k(T_e-T_{CMB})}{m_e c^2}` 
This is done via the generating_sz_data function and a full routine can be found in making_sz_maps.py. Here we briefly explain the inputs


.. code-block:: python

	filename = 'snap_m50n512_105.hdf5'
	output_name = 'SIMBA_z1' 
	z = 0.9927 
	theta = 3


- **filename** - Path and name of snapshot for analysis. Must be .hdf5 format
- **output_name** - Name of the .npy file containing the projected Compton-y map. The full script will project along the x, y, and z directions, and save files as output_name+'_x/y/z_szy.npy'
- **z** - redshift corresponding to the snapshot. Deriving the Compton-y parameter from pressure fields as done here is redshift dependent.
- **theta** - Angular resolution you want your map to have in units of arcseconds. Default and the value used to generate the RAFIKI-CGM package maps is 3". 


X-ray
-----







