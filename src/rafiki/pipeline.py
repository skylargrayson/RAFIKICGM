import os
import astropy.units as u
from astropy.cosmology import FlatLambdaCDM
from .catalog import  select_by_ranges, select_by_matching
from .sz import cut_stamps, make_radial_profiles, make_moment_profiles, thermal_energy, make_stacked_images
from .xray import xray_instrument_simulation
from .utils import redshift_resampling


def select_galaxies(config):
    '''
    Selects an analog galaxy sample and assigns redshifts to each galaxy

    :param config: input yaml file
    :type config: yaml  
    :return: gal_sample_indices-Array of selected galaxy catalog indices
    :return: galaxy_redshifts-Array of redshifts for mock observation for each galaxy in the catalog
    :rtype: np.ndarray   
    '''

    #Download galaxy catalogs and select sample
    redshift = str(config['package_data']['redshift'])
    if config['selection']['method']=='ranges':
        gal_sample_indices = select_by_ranges(config,redshift)
    elif config['selection']['method']=='matching':
        gal_sample_indices = select_by_matching(config,redshift)
    else:
        raise ValueError(f"Unknown selection method '{config['selection']['method']}'. Choose 'ranges' or 'matching'.")
    print('Number of selected analog galaxies:', len(gal_sample_indices)*3)

    #Assign redshifts to each galaxy in the sample 
    galaxy_redshifts = redshift_resampling(config,gal_sample_indices) 

    return gal_sample_indices, galaxy_redshifts


def run_sz(config, gal_sample_indices, galaxy_redshifts):
    ''' 
    Generates SZ data products
        
    :param config: input yaml file
    :type config: yaml     
    '''


    out_dir = config['output']['directory']
    label   = config['output']['label']
    save_to = str(out_dir) + str(label)
    output_file = save_to + '_szdat.hdf5'
    redshift = str(config['package_data']['redshift'])
    if os.path.exists(output_file):
        response = input(f"File {output_file} already exists — overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborting. Change output.label or output.directory in your config to save to a new file.")
            return
        else:
            print(f"Overwriting {output_file}")

    compton_y_stamps = cut_stamps(config, gal_sample_indices)
    #Calculate beam size in pixel units
    pixel_scale = config['sz']['pixel_size_arcsec'] #gives us the physical scale of each pixel in the FRB
    beam_scale = config['sz']['gaussian_std'] #units of arcmin
    out_dir = config['output']['directory']
    label = config['output']['label']
    save_to = str(out_dir)+str(label)
    if config['analysis']['sz_radial_profiles']:
        print('Beginnning radial profile analysis...')
        make_radial_profiles(compton_y_stamps, beam_scale*60,save_to, config,gal_sample_indices, galaxy_redshifts) #Will save files as output.directory.label_szdat.hdf5
        print('Completed radial profile analysis.')

    if config['analysis']['sz_moment_profiles']:
        print('Beginnning moment profile analysis...')
        make_moment_profiles(compton_y_stamps, beam_scale*60, save_to, config,gal_sample_indices, galaxy_redshifts) #Will save files as output.directory.label_szdat.hdf5
        print('Completed moment profile analysis.')
        
    if config['analysis']['thermal_energy']:
        print('Beginnning thermal energy analysis...')
        ap_arcsec = config['sz']['thermal_energy']['aperture']*60
        thermal_energy(compton_y_stamps, beam_scale*60, save_to, ap_arcsec, config, gal_sample_indices, galaxy_redshifts) #Will save files as output.directory.label_szdat.hdf5
        print('Completed thermal energy analysis.')
    if config['analysis']['sz_stacked_image'] and not config['analysis']['sz_radial_profiles']: #image making is included in radial profile pipeline
        print('Beginnning making SZ image...')
        make_stacked_images(compton_y_stamps, beam_scale*60,save_to, config,gal_sample_indices, galaxy_redshifts) #Will save files as output.directory.label_szdat.hdf5
        print('Completed SZ image.')

    print('Finished')

def run_xray(config, gal_sample_indices, galaxy_redshifts):
    ''' 
    Generates X-ray data products
        
    :param config: input yaml file
    :type config: yaml     
    '''
    out_dir = config['output']['directory']
    label   = config['output']['label']
    xray_z = str(config['package_data']['redshift'])
    save_to = str(out_dir) + str(label)
    output_file = save_to + '_xraydat.hdf5'

    if os.path.exists(output_file):
        response = input(f"File {output_file} already exists — overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborting. Change output.label or output.directory in your config to save to a new file.")
            return
        else:
            print(f"Overwriting {output_file}")
    xray_instrument_simulation(config,gal_sample_indices, galaxy_redshifts, save_to) #Generate instrument simulated files 



    