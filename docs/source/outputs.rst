Outputs
**************

Data outputs are saved in hdf5 files with locations and names set in the output section of the configuration file. 
The cookbook provides scripts for loading and plotting the data. It is reccomended that you use `h5py <https://www.h5py.org/>`_ to open the files but any hdf5 reader will work. 
The structure of the files are outlined below. 

.. _output_structure:

SZ Data Products
---------------------------------------------------
Saved to  ``<directory/label>_szdat.hdf5``

**File structure:**

.. code-block:: none

    <label>_szdat.hdf5
    ├── metadata/
    │   ├── simulation               (name of simulation used to generate data)
    │   ├── redshift                 (redshift of snapshot used to generate data)
    │   └── galaxy indices           (indices of the galaxy sample)  
    │   
    ├── radial_profile/              (if analysis.radial_profiles: true)
    │   ├── radius                   (center of radial bins in arcminutes)
    │   ├── compton-y                (stacked Compton-y value at each radius)
    │   └── error                    (error on Compton-y at each radius)
    │
    ├── moment_profiles/             (if analysis.moment_profiles: true)
    │   ├── radius                   (center of radial bins in arcminutes)
    │   ├── moment_1                 (stacked m=1/m=0 ratio)
    │   ├── m1_error                 (error on stacked m=1/m=0 ratio)
    │   ├── moment_2                 (stacked m=2/m=0 ratio)
    │   └── m2_error                 (error on stacked m=2/m=0 ratio)
    │
    ├── thermal_energy/              (if analysis.thermal: true)
    │   ├── stellar_mass             (center of stellar mass bins in solar masses)
    │   ├── thermal_stellar          (stacked thermal energy by stellar mass bin)
    │   ├── thermal_stellar_error    (error on stacked thermal energy)
    │   ├── halo_mass                (center of halo mass bins in solar masses)
    │   ├── thermal_halo             (stacked thermal energy by halo mass bin)
    │   └── thermal_halo_error       (error on stacked thermal energy)
    │
    └── image/                       (if analysis.sz_stacked_image: true)
        └── image_dat                (2D array of stacked Compton-y map)

X-ray Data Products
---------------------------------------------------
Saved to  ``<directory/label>_xraydat.hdf5``

**File structure:**

.. code-block:: none

    <label>_xraydat.hdf5
    ├── metadata/
    │   ├── simulation               (name of simulation used to generate data)
    │   ├── redshift                 (redshift of snapshot used to generate data)
    │   ├── instrument               (SOXS instrument used for mock data)
    │   └── galaxy indices           (indices of the galaxy sample)  
    │   
    ├── radial_profile/              (if analysis.radial_profiles: true)
    │   ├── radius                   (center of radial bins in kpc)
    │   ├── Sx                       (stacked X-ray surface brightness at each radius)
    │   └── error                    (error on Sx at each radius)
    │
    └── image/                       (if analysis.xray_stacked_image: true)
        └── image_dat                (2D array of stacked image, units of counts)




