import pandas as pd
import h5py 
import numpy as np
import matplotlib.pyplot as plt



def load_catalog(config,redshift): 
    ''' 
    Loads the catalog of mock galaxy properties for comparison

    :param config: input yaml files
    :type config: yaml 
    :return: stell-Array of galaxy stellar masses (solar units)
    :return: halo-Array of galaxy halo masses (solar units)
    :return: rad-Array of galaxy virial radii (kpc)
    :return: age-Array of galaxy ages (Gyr)
    :return: sfr-Array of galaxy star formation rates (solar units/yr)
    :return: ssfr-Array of galaxy specific star formation rates (Gyr^-1)
    :return: frb_locs-Array of galaxy locations in tSZ FRB map (pixel units)
    :return: central-Boolean flag if galaxies are central in their halo 
    :rtype: np.ndarray   
    '''

    path_to_package_data = config['package_data']['path']
    sim_name = config['package_data']['sim']
    red_shift = {'0.1':'0_1', '0_1':'0_1', '0.5':'0_5', '0_5':'0_5','1':'1', '1.0':'1','2':'2','2.0':'2','1.':'1','2.':'2'} #To account for possible names
    if redshift not in red_shift:
        raise ValueError(f"Redshift '{redshift}' not recognized. Valid options are: 0.1, 0.5, 1, 2")

    path = path_to_package_data+sim_name+'/snap_z'+red_shift[redshift]+'/galaxy_catalog.hdf5'

    if sim_name =='EAGLE':
        with h5py.File(path, 'r') as f:
            ids = f['galaxy_properties/ids'][:]    
            stell = f['galaxy_properties/stellar_mass'][:]
            dm_mass      = f['galaxy_properties/dm_mass'][:]
            m200c        = f['galaxy_properties/m200c'][:]
            r200c        = f['galaxy_properties/r200c'][:]
            halo       = f['galaxy_properties/m500c'][:]
            rad        = f['galaxy_properties/r500c'][:]
            age          = f['galaxy_properties/age'][:]
            sfr          = f['galaxy_properties/sfr'][:]
            central = f['galaxy_properties/central'][:]

            xs = f['frb_locations/x'][:]
            ys = f['frb_locations/y'][:]
            zs = f['frb_locations/z'][:]


        ssfr = 1e9 * sfr / stell
        frb_locs = [xs,ys,zs]

        return np.array(ids), np.array(stell), np.array(halo), np.array(rad), np.array(age), np.array(sfr), np.array(ssfr),np.array(frb_locs),np.array(central)
    else:
        with h5py.File(path, 'r') as f:

            stell = f['galaxy_properties/stellar_mass'][:]
            dm_mass      = f['galaxy_properties/dm_mass'][:]
            m200c        = f['galaxy_properties/m200c'][:]
            r200c        = f['galaxy_properties/r200c'][:]
            halo       = f['galaxy_properties/m500c'][:]
            rad        = f['galaxy_properties/r500c'][:]
            age          = f['galaxy_properties/age'][:]
            sfr          = f['galaxy_properties/sfr'][:]
            central = f['galaxy_properties/central'][:]

            xs = f['frb_locations/x'][:]
            ys = f['frb_locations/y'][:]
            zs = f['frb_locations/z'][:]


        ssfr = 1e9 * sfr / stell
        frb_locs = [xs,ys,zs]

        return np.array(stell), np.array(halo), np.array(rad), np.array(age), np.array(sfr), np.array(ssfr),np.array(frb_locs),np.array(central)


def select_by_ranges(config,z): 
    '''
    Loads the parameters for generating a mock galaxy sample catalog, used only if selection.method is set to range

    :param config: input yaml files
    :type config: yaml    
    :return: index_sample-array of galaxy indices in the RAFIKI-CGM catalog file that will be used for our mock galaxy sample
    :rtype: np.ndarray
    '''
    sim_name = config['package_data']['sim']

    if sim_name=='EAGLE':
        #Load RAFIKI-CGM galaxy catalog
        ids,stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,z)
        
        
    else:
        stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,z)
        ids=None

    sel = config['selection']['property_ranges']
    #Load ranges from config and validate min/max pairs make sense
    property_map = {
        'stellar_mass': stell,
        'halo_mass':    halo,
        'ssfr':         ssfr
    }
    
    for prop in property_map:
        min_val = sel.get(f'{prop}_min')
        max_val = sel.get(f'{prop}_max')
        if min_val is not None and max_val is not None:
            if float(max_val) <= float(min_val):
                raise ValueError(
                    f"Invalid range for {prop}: "
                    f"{prop}_max ({max_val}) must be greater than "
                    f"{prop}_min ({min_val})"
                )

    #Apply selection
    mask = np.ones(len(stell), dtype=bool) #Create a mask for galaxies that we will keep, starting with all selected
    
    if sel.get('centrals_only')== True:
        if sim_name=='EAGLE':
             mask &= centrals == 0.0
        else:
            mask &= centrals.astype(bool)
    if sel.get('stellar_mass_min') is not None:
        mask &= stell >= float(sel['stellar_mass_min'])
    if sel.get('stellar_mass_max') is not None:
        mask &= stell <= float(sel['stellar_mass_max'])
    if sel.get('halo_mass_min') is not None:
        mask &= halo >= float(sel['halo_mass_min'])
    if sel.get('halo_mass_max') is not None:
        mask &= halo <= float(sel['halo_mass_max'])
    if sel.get('ssfr_min') is not None:
        mask &= ssfr >= float(sel['ssfr_min'])
    if sel.get('ssfr_max') is not None:
        mask &= ssfr <= float(sel['ssfr_max'])

    index_sample = np.where(mask)[0]

    if len(index_sample) == 0:
        raise ValueError(
            "No galaxies passed the selection cuts. Check your min/max values in the config file."
        )
    if sim_name=='EAGLE':
        return index_sample #For EAGLE analysis want to verify galaxy ids as data saved differently than other sims
    else:         
        return index_sample


def select_by_matching(config,z):
    '''
    Load the galaxy sample catalog from the observations, used only if selection.method is set to matching

    :param config: input yaml file
    :type config: yaml    
    :return: Indices for galaxy sample selected to match the observed distribution
    :rtype: np.ndarray   
    '''
    sim_name = config['package_data']['sim']
    
    obs_catalog = config['selection']['catalog']['path'] #path to comparison galaxy sample catalog
    match_by = str(config['selection']['catalog']['match_property']) #property you want to match
    prop_column = config['selection']['catalog']['column'] #column of above property in galaxy sample catalog
    obs_data    = np.array(pd.read_csv(obs_catalog, header=None))
    obs_prop    = obs_data[:, prop_column] 

    if sim_name=='EAGLE':
        #Load RAFIKI-CGM galaxy catalog
        ids,stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,z)
        
        
    else:
        stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,z)
        ids=None

    sel = config['selection']['property_ranges']
     #Load ranges from config and validate min/max pairs make sense
    property_map = {
        'stellar_mass': stell,
        'halo_mass':    halo
    }

    if match_by not in property_map:
        raise ValueError(f"match_property '{match_by}' not recognized." 
                         f"Choose one of {list(property_map.keys())}")
    
    
    sim_indices = select_by_ranges(config,z)

    



    sim_prop = np.log10(np.array(property_map[match_by][sim_indices])) #load simulation galaxy sample properties with intial cuts, put in log space

    min_bin = max(np.min(obs_prop), np.min(sim_prop))
    max_bin = min(np.max(obs_prop), np.max(sim_prop))

    valid = (obs_prop >= min_bin) & (obs_prop <= max_bin) #Restrict binning weights to where the ranges overlap
    obs_prop = obs_prop[valid]

    if len(sim_prop) == 0:
        raise ValueError("No simulation galaxies passed the pre-matching cuts.")
     
    # --- Build histograms ---
    bins = config['selection']['catalog']['bins']  # list of bin edges in log space

    obs_hist, bin_edges     = np.histogram(obs_prop, bins=bins)
    obs_hist_norm           = obs_hist / np.sum(obs_hist)

    bin_indices             = np.clip(np.digitize(sim_prop, bin_edges) - 1, 0, len(obs_hist) - 1)
    sim_bin_counts          = np.bincount(bin_indices, minlength=len(obs_hist))
    sim_bin_probs           = sim_bin_counts / (np.sum(sim_bin_counts) + 1e-9) # Avoid division by zero

    # --- Compute selection weights ---
    # Weight each galaxy by how underrepresented its bin is in the simulation relative to the observed distribution
    selection_probs         = obs_hist_norm / (sim_bin_probs + 1e-9) # Avoid division by zero
    selection_probs        /= np.sum(selection_probs)
    source_weights          = selection_probs[bin_indices]
    source_weights         /= np.sum(source_weights)

    if np.sum(source_weights) == 0:
        raise ValueError(
            "No simulation galaxies overlap with the observed distribution. Check that your bins and match_property are correct, and that property_ranges cuts are not too aggressive."
        )

    # --- Resample ---
    n_sample = int(config['selection']['catalog']['n_sample'])
    resampled_indices = np.random.choice(len(sim_prop), size=n_sample, replace=True, p=source_weights)


    return sim_indices[resampled_indices] 

