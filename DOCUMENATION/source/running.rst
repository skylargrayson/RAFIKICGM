Running RAFIKI-CGM
==================

RAFIKI-CGM is running from the command line using a YAML configuration file. This controls all elements of the pipeline including the type of analysis, the simulations you want to use,
and specific settings regarding instrument simulation, galaxy samples, and where outputs are ssaved. You can run the full pipeline using:

.. code-block:: bash
	
	python run_pipeline.py --config config.yaml


Configuration File
------------------

A full example configuration file is shown below, as well as detailed documentation on each section. 

.. code-block:: yaml

	# =============================================================================
	# RAFIKI-CGM Configuration File
	# =============================================================================

	# -----------------------------------------------------------------------------
	#Simulation Selection
	# -----------------------------------------------------------------------------
	package_data:
		path: '/Volumes/easystore/RAFIKI_CGM_mock_library/'
		sim: RAFIKI_I                  #Options: SIMBA, EAGLE, RAFIKI_A-I 

	# -----------------------------------------------------------------------------
	#Analysis Selection
	# -----------------------------------------------------------------------------
	# Set to true to enable each data product
	analysis:
		sz_radial_profiles: false          #Stacked Compton-y radial profile
		sz_moment_profiles: false          #Stacked m=1/m=0 and m=2/m=0 moment profiles
		thermal_energy: false           #Thermal energy scaling relations
		sz_stacked_image: true          #Stacked map of Compton-y parameter
		xray_profiles: true             #Stacked X-ray surface brightnes profiles
		xray_stacked_image: true        #Stacked image of X-ray photon counts


	# -----------------------------------------------------------------------------
	# Galaxy Selection Settings
	# -----------------------------------------------------------------------------
	selection:
		method: matching                #Options: ranges | matching
		#Applied in both methods as an initial cut:
		property_ranges:             
			centrals_only: true           #Restrict to central galaxies only
			stellar_mass_min: 8e10        # Solar Masses (null=no cut)
			stellar_mass_max: null     
			halo_mass_min: null           # Solar Massess
			halo_mass_max: 1e14        
			ssfr_min: null                # Gyr^-1
			ssfr_max: null    
		#Used only in method: matching         
		catalog:
			path: keep_CEN.csv            #Comparison catalog
			match_property: stellar_mass  #Options: stellar_mass | halo_mass    
			column: 1                     #Column index of match_property in catalog
			bins: [10.5,10.6,10.7,10.8,10.9,11,
				11.1,11.2,11.3,11.4,11.5,11.6]  #log10 solar masses
			n_sample: 150                 #Number of galaxies in resampled selection 

	# -----------------------------------------------------------------------------
	# Thermal Sunyaev Zel'dovich settings
	# -----------------------------------------------------------------------------
	sz:
		redshift: 1				   #0.1, 0.5, 1, or 2
		pixel_size_arcsec: 3       #Angular size of map pixel (arcsec, default=3)
		stamp_width: 15            #Cutout size around each galaxy (arcmin)
		gaussian_std: 2            #Gaussian beam standard deviation (arcmin)
		thermal_energy:            
			aperture: 1              #Radius for thermal energy calculation
			stellar_mass_bins: [10.7, 10.9, 11.1, 11.3, 11.5, 11.7, 14.0]                # log10 solar masses
			halo_mass_bins: [12, 12.2, 12.4, 12.6, 12.8, 13, 13.2, 13.4, 13.6, 13.8, 16] # log10 solar masses

	# -----------------------------------------------------------------------------
	# X-ray settings 
	# -----------------------------------------------------------------------------
	xray:
		redshift: 0.1               #Snapshot redshift (currently only 0.1 supported)
		soxs_instrument: erosita    #Options: erosita | <any SOXS instrument label>
		exposure_time_ks: 1000      #Exposure time (ks)
		emin: 0.5                   #Minimum energy (keV)
		emax: 2                     #Maximum energy (keV)
		radial_bins: [0, 10, 30, 50, 75, 100, 200, 
						300,400, 500, 600, 700, 800, 
						900, 1000, 1100, 1200, 1300, 1400, 1500] #Radial bin edges (kpc)
		#Background components for instrument simulation
		ptsrc_bkgnd: false        #Point source background
		instr_bkgnd: false        #Instrumental background
		foreground: false         #Astrophysical foregrounds  


	# -----------------------------------------------------------------------------
	# Output
	# -----------------------------------------------------------------------------
	output:
		directory: /path/to/outputs/ #Directory for all output files   =
		label: rafiki_I             #Output file preflix 
									#Files saved as <label>_szdat.hdf5 and/or <label>_xraydat.hdf5 


Simulation Selection
^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

	package_data:
		path: /Volumes/easystore/RAFIKI_CGM_mock_library/
		sim: RAFIKI_A

This section points to where the maps and galaxy catalogs are saved and allows you to select the simulation you would like to analyze

``package_data.path`` 
	*str* - Path to the directory where RAFIKI-CGM maps and catalogs are saved. (CLOUD ACCESS INFO EVENTUALLY?) 

``package_data.sim``
	*str* - Name of the simulation you want to use to generate the mock data. Either ``SIMBA``, ``EAGLE``, or ``RAFIKI_A-I``. See :ref:`sim_options` to understand the differences

Analysis Selection
^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

	analysis:
		sz_radial_profiles: false          #Stacked Compton-y radial profile
		sz_moment_profiles: false          #Stacked m=1/m=0 and m=2/m=0 moment profiles
		thermal_energy: false           #Thermal energy scaling relations
		sz_stacked_image: true          #Stacked map of Compton-y parameter
		xray_profiles: true             #Stacked X-ray surface brightnes profiles
		xray_stacked_image: true        #Stacked image of X-ray photon counts

This section is where you select which analyses you would like to do. There are three options related to the thermal Sunyaev-Zeldovich effect and two for X-ray emission.

``analysis.sz_radial_profiles``
	*bool* - Generate a stacked radial profile of the Compton-y parameter

``analysis.sz_moment_profiles``
	*bool* - Generate stacked radial profiels for the moments of symmetry, output as the ratios of m1/m0 and m2/m0

``analysis.thermal_energy``
	*bool* - Calculate the thermal energy value within a circular region in your galaxy stack. Splits the sample into bins of stellar and halo mass that are specified in the config.sz.thermal_energy

``analysis.sz_stacked_image``
	*bool* - Save 2D array of stacked map of Compton-y parameter around galaxies

Galaxy Selection
^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

	selection:
	method: matching              #either "ranges": specify limits on galaxy properties or "matching": match user input galaxy catalog
	property_ranges:             #Use these to set limits if method set to ranges
		centrals_only: true        #Only select galaxies central in their halos
		stellar_mass_min: 1.0e11   # Solar Masses
		stellar_mass_max: null     
		halo_mass_min: null        # Solar Masses
		halo_mass_max: null        
		ssfr_min: null             # Gyr^-1
		ssfr_max: null             
	catalog:
		path: keep_CEN.csv #File path for observational galaxy catalog
		match_property: stellar_mass              #Galaxy property you are trying to match-if mass make sure in log units
		column: 1                                 #Column index (i.e. 0 is the first column) of the property above in the observational catalog file
		bins: [10.5,10.6,10.7,10.8,10.9,11,11.1,11.2,11.3,11.4,11.5,11.6] #Stellar mass bins for the histogram of galaxy sample selection
		n_sample: 100    

Here you identify how you want to generate the mock galaxy catalog and input the relevant parameters. There are two ways of doing this, set by selection.method

``selection.method``
	*str* - Identify how you wish to choose the galaxy sample. There are two options: ranges or matching. The first allows you to place limits on galaxy properties (stellar mass, halo mass,
	and ssfr) to cut out your galaxy sample. The second allows you to input a catalog and select analog galaxies for your sample. If you select matching, it will still apply any cuts listed
	under selection.property_ranges, so be sure those are set to null if you do not want any further cuts. (See :ref:`selection-methods`  for detailed documentation). Each method has a range of associated
	parameters.

``selection.property_ranges.centrals_only``
	*bool* - Select whether you want to only sample galaxies that are central in their halos.
	Set to ``false`` if you want to include all galaxies (both satellites and centrals)

``selection.property_ranges.stellar_mass_min``
	*float* - Minimum stellar mass cut in solar masses
	Set to ``null`` to apply no lower limit

``selection.property_ranges.stellar_mass_max``
	*float* - Maximum stellar mass cut in solar masses
	Set to ``null`` to apply no upper limit

``selection.property_ranges.halo_mass_min``
	*float* - Minimum halo mass cut in solar masses
	Set to ``null`` to apply no lower limit

``selection.property_ranges.halo_mass_max``
	*float* - Maximum halo mass cut in solar masses
	Set to ``null`` to apply no upper limit

.. note:: 
	While tSZ analysis can be used for any galaxy in the box, X-ray :ref: `event_files` have only been generated for the 500 most massive galaxies in each simulation output. This corresponds 
	to a minimum stellar mass of ~4.3x10^10, please be conscious of this when choosing ranges. 

``selection.property_ranges.ssfr_min``
	*float* - Minimum specific star formation rate cut in Gyr^-1
	Set to ``null`` to apply no lower limit

``selection.property_ranges.ssfr_max``
	*float* - Maximum specific star formation rate cut in Gyr^-1
	Set to ``null`` to apply no upper limit

``selection.catalog.path``
	*str* - Path and file name for catalog containing the comparison galaxy sample information

``selection.catalog.match_property``
	*str*  - The galaxy sample property you want to match in the catalog. 
	Either ``stellar_mass`` or ``halo_mass``

``selection.catalog.bins``
	*array* - Bin edges for histogram that will be used to match sample distributions. 
	Units of log solar masses

``selection.catalog.n_sample``
	*float* - Number of galaxies in resampled selection 


SZ Analysis Parameters
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

	sz:
		redshift: 1				   #0.1, 0.5, 1, or 2
		pixel_size_arcsec: 3       #default 3 for pre-generated maps
		stamp_width: 15            #width of square to cut around galaxies in arcminutes. Default 15
		gaussian_std: 2            #standard deviation of the Gaussian beam in units of arcminutes. Default 2
		thermal_energy:            
			aperture: 1              #radius of spherical aperture for calculating thermal energy in units of arcminutes. Default 1
			stellar_mass_bins: [10.7, 10.9, 11.1, 11.3, 11.5, 11.7, 14.0]   # log10 solar masses
			halo_mass_bins: [12, 12.2, 12.4, 12.6, 12.8, 13, 13.2, 13.4, 13.6, 13.8, 16] # log10 solar masses


Here you input the parameters that are relevant for conducting the SZ analysis

``sz.redshift``
	*float* - Redshift of the snapshot you wish to analyse. Options are 0.1, 0.5, 1, and 2.

``sz.pixel_size_arcsec``
	*float* - Pixel scale of the Compton-y map. If using built-in RAFIKI-CGM maps the default is 3 arcseconds and this will never need to be changed. 

``sz.stamp_width``
	*float* - Width of the square region you want to cut around galaxies to generate stacked data in units of arcminutes. Default is 15.

``sz.gaussian_std``
	*float* - Standard deviation of the Gaussian beam you want to convolve your data with to align with observational data in units of arcminutes. 
	For ACT use: XX. 
	For SPT use: XX.
	For TolTEC use: XX.

``sz.thermal_energy.aperture``
	*float* - Radius of the circular aperture used to calculate thermal energy in units of arcminutes.

``sz.thermal_energy.stellar_mass_bins``
	*list of floats* - Bin edges for stacking by stellar mass in thermal energy calculations. Units of log solar masses

``sz.thermal_energy.halo_mass_bins``
	*list of floats* - Bin edges for stacking by halo mass in thermal energy calculations. Units of log solar masses



.. code-block:: yaml

	xray:
		redshift: 0.1               #Snapshot redshift (currently only 0.1 supported)
		soxs_instrument: erosita    #Options: erosita | <any SOXS instrument label>
		exposure_time_ks: 1000      #Exposure time (ks)
		emin: 0.5                   #Minimum energy (keV)
		emax: 2                     #Maximum energy (keV)
		radial_bins: [0, 10, 30, 50, 75, 100, 200, 
						300,400, 500, 600, 700, 800, 
						900, 1000, 1100, 1200, 1300, 1400, 1500] #Radial bin edges (kpc)
		#Background components for instrument simulation
		ptsrc_bkgnd: false        #Point source background
		instr_bkgnd: false        #Instrumental background
		foreground: false         #Astrophysical foregrounds  


``xray.redshift``
	*float* - Redshift of the snapshot you wish to analyse. Currently only supported for z=0.1.

``xray.sox_instrument``
	*str* - Name of the instrument wanted for mock data. 
	Can use any SOXS supported instrument or ``erosita`` for the eROSITA-SRG instrument

``xray.exposure_time_ks``
	*float* - Exposure time for the mock observation in units of kiloseconds. Must be less than 2000 

``xray.emin``
	*float* - Minimum photon energy wanted to model in units of keV

``xray.emax``
	*float* - Maximum photon energy wanted to model in units of keV

``xray.radial_bins``
	*array* - Radial bin edges for generating surface brightness profile in units of kpc

``xray.ptsrc_bkgnd``
	*bool* - Include X-ray point source background in SOXS modelling

``xray.instr_bkgnd``
	*bool* - Include instrument background in SOXS modelling

``xray.foreground``
	*bool* - Include astrophysical foregrounds in SOXS modelling




Outputs
^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

	# Output
	output:
		directory: /path/to/outputs/      #directory where output files will be saved
		label: rafiki_A_z1          #label for the output files, will be saved as <label>_szdat.hdf5 and/or <label>_xraydat.hdf5 


Here you set the output directory and how you would like the data to be labeled. For more detail on the format of the output files see :ref:`output_structure`

``output.directory`` 
	*str* - Path to the directory where you would like to save files. Be sure the directory exits, use absolute path

``output.label``
	*str* - Label used for the output files. If conducting tSZ analysis the file will be saved as <label>_szdat.hdf5 and for x-ray data will be <label>_xraydat.hdf5 


Visualizing Data
----------------

See :ref:`plotting` for examples on how to read in the output files and visualize the results. 



Tips and Common Issues
----------------------

**The pipeline runs but output files are empty**
    Make sure ``output.label`` and ``output.directory`` are set correctly in your config and that the output directory exists before running. 





