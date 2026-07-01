import numpy as np
import h5py
import yt
from .catalog import load_catalog
import pandas as pd


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


def load_xray_particle_data(filename):
    with h5py.File(filename) as f:

        gas = f["data"]

        data = {
            ("gas","particle_position_x"):
                (gas["particle_position_x"][:],
                gas["particle_position_x"].attrs["units"]),

            ("gas","particle_position_y"):
                (gas["particle_position_y"][:],
                gas["particle_position_y"].attrs["units"]),

            ("gas","particle_position_z"):
                (gas["particle_position_z"][:],
                gas["particle_position_z"].attrs["units"]),

            ("gas","particle_velocity_x"):
                (gas["velocity_x"][:],
                gas["velocity_x"].attrs["units"]),

            ("gas","particle_velocity_y"):
                (gas["velocity_y"][:],
                gas["velocity_y"].attrs["units"]),

            ("gas","particle_velocity_z"):
                (gas["velocity_z"][:],
                gas["velocity_z"].attrs["units"]),

            ("gas","particle_mass"):
                (gas["mass"][:],
                gas["mass"].attrs["units"]),

            ("gas","density"):
                (gas["density"][:],
                gas["density"].attrs["units"]),

            ("gas","temperature"):
                (gas["temperature"][:],
                gas["temperature"].attrs["units"]),

            ("gas","metallicity"):
                (gas["metallicity"][:],
                gas["metallicity"].attrs["units"]),

            ("gas","smoothing_length"):
                (gas["smoothing_length"][:],
                gas["smoothing_length"].attrs["units"]),
                
            ("gas","emission_measure"):
                (gas["emission_measure"][:],
                gas["emission_measure"].attrs["units"]),
        }

    bbox = np.array([
        [data[("gas","particle_position_x")][0].min(),
        data[("gas","particle_position_x")][0].max()],
        [data[("gas","particle_position_y")][0].min(),
        data[("gas","particle_position_y")][0].max()],
        [data[("gas","particle_position_z")][0].min(),
        data[("gas","particle_position_z")][0].max()],
    ])

    loaded_data= yt.load_particles(data, bbox=bbox)
    return loaded_data


def redshift_resampling(config,index_sample):
    mode = str(config['xray']['redshift_sampling']['mode'])     #Determine mode
    if mode=='fixed':   
        #Use the snapshot redshift for every galaxy
        z_fixed = float(config['xray']['redshift_sampling']['fixed_z']) 
        return np.full(len(index_sample), z_fixed)
    

    sim_name = config['package_data']['sim']
    z= float(config['xray']['redshift'])  
    if sim_name=='EAGLE':
        #Load RAFIKI-CGM galaxy catalog
        ids,stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,z)     
    else:
        stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,z)
        ids=None


    if mode=='redshift':
        obs_catalog = config['xray']['redshift_sampling']['observational_catalog']#path to comparison galaxy sample catalog
        obs_data    = np.array(pd.read_csv(obs_catalog, header=None))
        z_column = config['xray']['redshift_sampling']['z_column']#column of redshift in galaxy sample catalog
        mass_column = config['xray']['redshift_sampling']['mass_column']#column of redshift in galaxy sample catalog
        obs_z    = obs_data[:, z_column] 
        return np.random.choice(obs_z,size=len(index_sample), replace=True)



    if mode=='mass_redshift':

        obs_catalog = config['xray']['redshift_sampling']['observational_catalog']#path to comparison galaxy sample catalog
        obs_data    = np.array(pd.read_csv(obs_catalog, header=None))
        z_column = config['xray']['redshift_sampling']['z_column']#column of redshift in galaxy sample catalog
        mass_column = config['xray']['redshift_sampling']['mass_column']#column of redshift in galaxy sample catalog
        obs_z    = obs_data[:, z_column] 
        obs_mass = obs_data[:, mass_column]

        galaxy_stellar=stell

        bins = np.array(config['xray']['redshift_sampling']['mass_bins'])
        z_bins = [[] for _ in range(len(bins) - 1)]

        #separate galaxies into mass bins, find their redshifts
        for mass, z in zip(obs_mass, obs_z):
            idx = np.digitize(mass, bins) - 1
            if 0 <= idx < len(z_bins):
                z_bins[idx].append(z)

        #randomly select redshifts based on simulated sample masses
        sim_redshifts = []
        for i in index_sample:
            sim_mass = np.log10(galaxy_stellar[i])

            idx = np.digitize(sim_mass, bins) - 1

            if 0 <= idx < len(z_bins) and len(z_bins[idx]) > 0:
                sim_redshifts.append(np.random.choice(z_bins[idx]))
            else:
                sim_redshifts.append(1)
                
        return(sim_redshifts)