import os
import astropy.units as u
from astropy.cosmology import FlatLambdaCDM
from .catalog import  select_by_ranges, select_by_matching
from .sz import cut_stamps, make_radial_profiles, make_moment_profiles, thermal_energy,make_stacked_sz_image
from .xray import xray_instrument_simulation



def run_sz(config):
    ''' 
    Generates SZ data products
        
    :param config: input yaml file
    :type config: yaml     
    '''


    out_dir = config['output']['directory']
    label   = config['output']['label']
    save_to = str(out_dir) + str(label)
    output_file = save_to + '_szdat.hdf5'
    redshift = str(config['sz']['redshift'])
    if os.path.exists(output_file):
        response = input(f"File {output_file} already exists — overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborting. Change output.label or output.directory in your config to save to a new file.")
            return
        else:
            print(f"Overwriting {output_file}")
    if config['selection']['method']=='ranges':
        gal_sample_indices = select_by_ranges(config,redshift)
    elif config['selection']['method']=='matching':
        gal_sample_indices = select_by_matching(config,redshift)
    else:
        raise ValueError(f"Unknown selection method '{config['selection']['method']}'. Choose 'ranges' or 'matching'.")
    print('Number of selected analog galaxies:', len(gal_sample_indices)*3)

    compton_y_stamps = cut_stamps(config, gal_sample_indices)
    #Calculate beam size in pixel units
    pixel_scale = config['sz']['pixel_size_arcsec'] #gives us the physical scale of each pixel in the FRB
    beam_scale = config['sz']['gaussian_std'] #units of arcmin
    beam_scale_pixels = beam_scale*60/pixel_scale
    out_dir = config['output']['directory']
    label = config['output']['label']
    save_to = str(out_dir)+str(label)
    if config['analysis']['sz_radial_profiles']:
        print('Beginnning radial profile analysis...')
        make_radial_profiles(compton_y_stamps, beam_scale_pixels,save_to, config,gal_sample_indices) #Will save files as output.directory.label_szdat.hdf5
        print('Completed radial profile analysis.')

    if config['analysis']['sz_moment_profiles']:
        print('Beginnning moment profile analysis...')
        make_moment_profiles(compton_y_stamps, beam_scale_pixels, save_to, config,gal_sample_indices) #Will save files as output.directory.label_szdat.hdf5
        print('Completed moment profile analysis.')
    if config['analysis']['thermal_energy']:
        print('Beginnning thermal energy analysis...')
        ap_arcmin = config['sz']['thermal_energy']['aperture']
        ap_pixels = ap_arcmin*60/pixel_scale
        redshift = config['sz']['redshift']
        cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
        comov = cosmo.comoving_distance(float(redshift)).to(u.Gpc).value 
        thermal_energy(compton_y_stamps, beam_scale_pixels, save_to, ap_pixels, comov, redshift, pixel_scale, gal_sample_indices, config) #Will save files as output.directory.label_szdat.hdf5
        print('Completed thermal energy analysis.')
    if config['analysis']['sz_stacked_image']:
        print('Beginnning generating stacked image...')
        make_stacked_sz_image(compton_y_stamps, beam_scale_pixels, save_to, config,gal_sample_indices)
        print('Completed stacked image.')
    print('Finished')

def run_xray(config):
    ''' 
    Generates X-ray data products
        
    :param config: input yaml file
    :type config: yaml     
    '''
    out_dir = config['output']['directory']
    label   = config['output']['label']
    xray_z = str(config['xray']['redshift'])
    save_to = str(out_dir) + str(label)
    output_file = save_to + '_xraydat.hdf5'

    if os.path.exists(output_file):
        response = input(f"File {output_file} already exists — overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborting. Change output.label or output.directory in your config to save to a new file.")
            return
        else:
            print(f"Overwriting {output_file}")
    
    if config['selection']['method']=='ranges':
        gal_sample_indices = select_by_ranges(config,xray_z)
    elif config['selection']['method']=='matching':
        gal_sample_indices = select_by_matching(config,xray_z)
    else:
        raise ValueError(f"Unknown selection method '{config['selection']['method']}'. Choose 'ranges' or 'matching'.")
    print('Number of selected analog galaxies:', len(gal_sample_indices)*3)
    print('Beginning instrument simulation')
    xray_instrument_simulation(config,gal_sample_indices, save_to) #Generate instrument simulated files 
    
    
    
    #print('Beginning generating profiles')
    #make_xray_profiles(config, gal_sample_indices, save_to)

    #if config['analysis']['xray_stacked_image']==True:
        #print('Beginning image stacking')
        #make_xray_image(config, gal_sample_indices,save_to)

    