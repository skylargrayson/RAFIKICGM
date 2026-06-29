Running and Plotting Thermal Sunyaev Zel'dovich Data
======================================================

This cookbok walks through a basic end-to-end run of RAFIKI-CGM's tSZ functionality. 

Setting up the Config File
---------------------------

Copy the example config file into your directory.

    cp config_example.yaml config.yaml

Set the path to where the RAFIKI-CGM data is saved and select the simulation

.. code-block:: yaml

    package_data:
      path: /path/to/your/data/
      sim: RAFIKI_A

Choose all four tSZ analyses:

.. code-block:: yaml

    analysis:
        sz_radial_profiles: true        
        sz_moment_profiles: true     
        thermal_energy: true         
        sz_stacked_image: true        
        xray_profiles: false         
        xray_stacked_image: false  
        
Select your galaxy sample using property ranges. In this example we select massive galaxies with a stellar mass greater than 1e11, and no limits on halo mass or star formation rate.

.. code-block:: yaml

	selection:
		method: ranges              
		property_ranges:
            centrals_only: false             
			stellar_mass_min: 1e11  
			stellar_mass_max: null     
			halo_mass_min: null       
			halo_mass_max: null      
			ssfr_min: null            
			ssfr_max: null            

Select your SZ analysis parameters. In this situation we are using the z=1 snapshot, with a beam standard deviation of 2 arcminutes. For thermal energy calculations we are summing within
one arcminute and stacking galaxies with the halo and stellar mass bins shown below. 

.. code-block:: yaml

	sz:
		redshift: 1
		pixel_size_arcsec: 3     
		stamp_width: 15           
		gaussian_std: 2            
		thermal_energy:            
			aperture: 1             
			stellar_mass_bins: [10.7, 10.9, 11.1, 11.3, 11.5, 11.7, 14.0]  
			halo_mass_bins: [12, 12.2, 12.4, 12.6, 12.8, 13, 13.2, 13.4, 13.6, 13.8, 16]

Point to where you want the data to save

.. code-block:: yaml

	# Output
	output:
		directory: ./results/      
		label: rafiki_A_example       

Running the Pipeline
--------------------

Run the pipeline from the command line

.. code-block:: bash
	
	python run_pipeline.py --config config.yaml

You should see output like:

.. code-block:: none

    Number of selected analog galaxies: 333
    Beginnning radial profile analysis...
    Completed radial profile analysis.
    Beginnning moment profile analysis...
    Completed moment profile analysis.
    Beginning thermal energy analysis...
    Completed thermal energy analysis.
    Beginnning generating stacked image...
    Completed stacked image.
    Finished.

Remember that the number of selected galaxies is equal to three times the actual number in the simulation box as it accounts for the three different projections.

.. _plotting:

Loading and Plotting Your Results
----------------------------------

Once the pipeline has finished running you can load the output files and plot the radial profiles, moment radial profiles, thermal energy scaling relations, and the stacked Comtpon-y map as below

.. code-block:: python

    import numpy as np
    from matplotlib import pyplot as plt    
    import h5py

    data_file = 'results/rafiki_A_example_szdat.hdf5' #path to saved stacked radial data-should be the only thing you need to change

    #-------------RADIAL PROFILES-------------#
    with h5py.File(data_file, 'r') as f:
        x_a = f['radial_profile/radius'][:]
        y_a = f['radial_profile/compton-y'][:]
        err_a = f['radial_profile/error'][:]

    plt.plot(x_a,y_a)
    plt.errorbar(x_a,y_a, yerr=err_a)
    plt.xlabel('Radius (arcmin)')
    plt.ylabel('Compton-y')
    plt.yscale('log')
    plt.show()

.. figure:: ../_static/images/radialprof.png
   :width: 70%
   :align: center


.. code-block:: python

    #-------------MOMENT PROFILES-------------#
    with h5py.File(data_file, 'r') as f:
        x_a = f['moment_profiles/radius'][:]
        y_a = f['moment_profiles/moment_1'][:]
        err_a = f['moment_profiles/m1_error'][:]
        y_b = f['moment_profiles/moment_2'][:]
        err_b = f['moment_profiles/m2_error'][:]

    plt.scatter(x_a, y_a,s=30,color = 'red',label = 'm=1')
    plt.errorbar(x_a, y_a[0:300],yerr = err_a,color = 'red',fmt ='none')
    plt.scatter(x_a, y_b[0:300],s=30,color = 'orange',label = 'm=2')
    plt.errorbar(x_a, y_b[0:300],yerr = err_b,color = 'orange',fmt ='none')
    plt.legend()
    plt.xlim(0,10)
    plt.xlabel('Radius (arcmin)')
    plt.ylabel('$\Sigma(m)/\Sigma(m=0$)')
    plt.show()

.. figure:: ../_static/images/momentprof.png
   :width: 70%
   :align: center

.. code-block:: python

    #-------------STELLAR MASS-THERMAL ENERGY-------------#
    with h5py.File(data_file, 'r') as f:
        x_a = f['thermal_energy/stellar_mass'][:]
        y_a = f['thermal_energy/thermal_stellar'][:]
        err_a = f['thermal_energy/thermal_stellar_error'][:]


    plt.scatter(x_a ,y_a, c = 'black')
    plt.errorbar(x_a,y_a, yerr=err_a, fmt='none', color = 'black')
    plt.yscale('log')
    plt.xscale('log')
    plt.xlabel('Stellar Mass ($M_\odot$)')
    plt.ylabel('Thermal Energy ($10^{60}$ erg)')
    plt.show()

.. figure:: ../_static/images/thermstell.png
   :width: 70%
   :align: center

.. code-block:: python

    #-------------HALO MASS-THERMAL ENERGY-------------#
    with h5py.File(data_file, 'r') as f:
        x_a = f['thermal_energy/halo_mass'][:]
        y_a = f['thermal_energy/thermal_halo'][:]
        err_a = f['thermal_energy/thermal_halo_error'][:]


    plt.scatter(x_a ,y_a, c = 'black')
    plt.errorbar(x_a,y_a, yerr=err_a, fmt='none', color = 'black')
    plt.yscale('log')
    plt.xscale('log')
    plt.xlabel('Halo Mass ($M_\odot$)')
    plt.ylabel('Thermal Energy ($10^{60}$ erg)')
    plt.show()

.. figure:: ../_static/images/thermhalo.png
   :width: 70%
   :align: center

.. code-block:: python

    #-------------STACKED IMAGE-------------#
    import matplotlib.colors as colors
    from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

    with h5py.File(data_file, 'r') as f:
        y_a = f['image/image_dat'][:]

    fig, ax = plt.subplots()

    plt.imshow(y_a, norm=colors.LogNorm(vmin=np.min(y_a), vmax=np.max(y_a)))
    plt.colorbar(label='Compton-y')
    ax.set_xticks([]) 
    ax.set_yticks([]) 
    ax.set_xlabel("")  
    ax.set_ylabel("")

    #Calculated pixel scale using default 1 pixel = 3 arcsec
    scalebar = AnchoredSizeBar(ax.transData,
                            60, '3 arcmin', 'upper left', 
                            pad=0.1,
                            color='black',
                            frameon=True,
                            size_vertical=3)

    ax.add_artist(scalebar)
    plt.show()

.. figure:: ../_static/images/szstack.png
   :width: 70%
   :align: center