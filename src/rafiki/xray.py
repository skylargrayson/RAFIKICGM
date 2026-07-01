import numpy as np
from astropy.io import fits
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u
from random import randint
from scipy.stats import bootstrap
from scipy.stats import bootstrap
import h5py
import pyxsim
import soxs
import os
import glob
from importlib.resources import files
from .catalog import load_catalog
from .instruments import make_erosita
from .utils import load_xray_particle_data, redshift_resampling
import traceback
from pathlib import Path
def xray_instrument_simulation(config,index_sample, label):
    '''
    Run through the X-ray pipeline. Creates mock observations, generates radial profiles of surface brigtness and stacks. Also generates stacked images if analysis.xray_stacked_image: true
    Does not return anything, just saves data to file

    :param config: input yaml file
    :type config: yaml  
    :param index_sample: array of galaxy indices in the RAFIKI-CGM catalog file that will be used for our mock galaxy sample
    :type index_sample: np.ndarray
    :param label: File name and path to save outputs
    :type label: str
    '''

    instrument = str(config['xray']['soxs_instrument'])
    exp_time = float(config['xray']['exposure_time_ks'])
    output_dir = str(config['output']['directory'])
    output_label = str(config['output']['label'])
    data_path = str(config['package_data']['path'])
    sim = str(config['package_data']['sim'])
    xray_data_saved = data_path + sim + '/snap_z0_1/X-ray/particles/'
    make_image = config['analysis']['xray_stacked_image']

    axes = ["x", "y", "z"]
    emin=float(config['xray']['emin']) 
    emax=float(config['xray']['emax']) 
    area=float(config['xray']['collecting_area']) 
    r_bins = np.array(config['xray']['radial_bins'])#creating the radial bins that will be used-this is from Zhang 2024c
    snap_redshift = float(config['xray']['redshift'])  
   
    if instrument.startswith("erosita"):
        instrument_dir = Path(__file__).parent / "data" / "erosita"
        soxs.set_soxs_config("soxs_data_dir", str(instrument_dir))
        make_erosita()
        detectors= [f"erosita{i}" for i in range(1, 8)]
        arf_dat=fits.open(instrument_dir / "onaxis_tm0_arf_filter_2023-01-17.fits")
    else:
        detectors = [instrument]
        arf_dat=fits.open(soxs.instrument_registry[instrument]["arf"])

    ad=arf_dat[1].data
    arf_e=np.array(ad['ENERG_LO']) #energy in kev
    arf= ad['SPECRESP'] #effective area in cm^2
    texp=float(config['xray']['exposure_time_ks'])*1000

    all_profs = []
    all_images =[]

    failed_runs = []
    if sim == 'EAGLE':
        ids,stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config, str(snap_redshift))
        index_to_id = {i: id_ for i, id_ in enumerate(ids)}

    source_model = pyxsim.CIESourceModel("apec", emin, emax, 1000, Zmet =('gas', 'metallicity'), temperature_field = ('gas', 'temperature'),emission_measure_field=('gas','emission_measure'))

    redshifts = redshift_resampling(config,index_sample) 


    for i in index_sample:
        gal_number = str(i)
        if sim=='EAGLE':
            gal_id = str(index_to_id[i])
            particles = load_xray_particle_data(xray_data_saved+f"galaxy_{gal_id}.h5")
        else:
            particles = load_xray_particle_data(xray_data_saved+f"galaxy_{gal_number}.h5")
        z=redshifts[i]
        #Make photon and event lists
        xray_fields = source_model.make_source_fields(particles, emin,emax)
        ad = particles.all_data()       
        n_photons, n_cells = pyxsim.make_photons( output_dir+output_label+f"_photons_{gal_number}", ad, z, area,exp_time*1.5*1000, source_model) #for generating photons, use longer exposure time than instrument simulation

        for axis in axes:
            n_events = pyxsim.project_photons( output_dir+output_label+f"_photons_{gal_number}",  output_dir+output_label+f"_events_{gal_number}", axis, (0.0, 0.0))
        os.remove(output_dir+output_label+f"_photons_{gal_number}.h5") #Don't need photon lists after this point 
        for axis in axes:
            all_comb = []
            image_comb = []
            for detector in detectors:
                inst = soxs.instrument_registry[detector]
                cosmo = FlatLambdaCDM(H0=67.74 * u.km / u.s / u.Mpc, Tcmb0=2.725 * u.K, Om0=0.3089)

                d_A = cosmo.angular_diameter_distance(z).to(u.kpc).value 
                pixel_scale_arcsec = inst["fov"] * 60.0 / inst["num_pixels"]
                theta_rad = (pixel_scale_arcsec * u.arcsec).to(u.rad).value
                dl = cosmo.luminosity_distance(z).to(u.cm).value
                pixel_size_kpc = d_A * theta_rad

                try:

                    outfile = os.path.join(
                        output_dir,
                        f"{output_label}_gal_sample_{axis}_{gal_number}_{detector}.fits"
                    )
                    event_file =  output_dir+output_label+f"_events_{gal_number}.h5"
                    soxs.instrument_simulator(                      #Makes mock images
                            event_file,
                            outfile,
                            (exp_time, "ks"),
                            detector,
                            [0, 0],
                            overwrite=True,
                            ptsrc_bkgnd=config['xray']['ptsrc_bkgnd'],
                            instr_bkgnd=config['xray']['instr_bkgnd'],
                            foreground=config['xray']['foreground']
                        )
                    f = fits.open(outfile)
                    d = f[1].data
                    e_obs = convert_to_erg(np.array(d['ENERGY'])/1000,z, dl, emin, emax, arf, arf_e, texp)
                    num_pixels = inst["num_pixels"]
                    width = num_pixels 
                    r = np.sqrt((d['X'] - width)**2 + (d['Y'] - width)**2) * pixel_size_kpc
                    radial = bin_energies(r, e_obs, r_bins)
                    all_comb.append(radial)
                    f.close()

                    if make_image:
                        soxs.write_image(outfile,  output_dir+output_label+f"_gal_image_sample_{axis}_{gal_number}_{detector}.fits", emin=emin, emax=emax, overwrite=True) 
                        image_file = output_dir+output_label+f"_gal_image_sample_{axis}_{gal_number}_{detector}.fits"
                        fi = fits.open(image_file)
                        di=fi[0].data
                        image_comb.append(di)
                    else:
                        image_comb.append(np.full((num_pixels, num_pixels), np.nan))
                except Exception as e:
                    num_pixels = inst["num_pixels"]            
                    print(f"⚠️ Skipping galaxy {i}, axis {axis}, instrument {detector}: {e}")
                    failed_runs.append((i, axis, detector))

                    # Append zeros so shapes stay consistent
                    all_comb.append(np.full(len(r_bins)-1, np.nan))
                    image_comb.append(np.full((num_pixels, num_pixels), np.nan))

                    continue
                
            y_images=np.nansum(np.array(image_comb), axis=0)
            all_images.append(y_images)
    
            summed_instruments = np.nansum(np.array(all_comb), axis=0)
            all_profs.append(summed_instruments)

            for fname in glob.glob(output_dir + output_label + "*.fits"):
                os.remove(fname)
            for fname in glob.glob(output_dir + output_label + "*.h5"):
                os.remove(fname)

    print('Number of galaxies with no detections', len(failed_runs))
    counts = np.nanmean( np.array(all_images), axis=0)   

    y = list(zip(*all_profs))

    y_a = []
    err_a = []

    for i in y:
        i = np.array(i)
        valid = ~np.isnan(i)

        if np.sum(valid) == 0:
            y_a.append(np.nan)
            err_a.append(np.nan)
            continue

        y_a.append(np.nanmean(i))

        bootstrap_ci = bootstrap(
            (i[valid],),
            np.mean,
            confidence_level=0.95,
            random_state=1,
            method='percentile'
        )
        err_a.append(bootstrap_ci.standard_error)
    failed_arr = np.array([str(x) for x in failed_runs], dtype='S')
    with h5py.File(label+'_xraydat.hdf5', 'a') as f: 
        if 'metadata' in f:
            del f['metadata']
        
        meta = f.create_group('metadata') 
        meta.attrs['simulation'] = str(sim)
        meta.attrs['snapshot redshift']  = str(snap_redshift)
        meta.attrs['instrument'] = str(instrument)
        meta.create_dataset('galaxy_indices', data=np.array(index_sample))  
        meta.create_dataset('galaxy_redshifts', data=np.array(redshifts))  
        meta.create_dataset('failed_galaxies', data=np.array(failed_arr))
        if 'radial_profile' in f:
                del f['radial_profile']
        rad = f.create_group('radial_profile')
        rad.create_dataset('radius', data=np.array(r_bins))
        rad['radius'].attrs['units'] = 'kpc'
        rad.create_dataset('Sx', data=np.array(y_a))
        rad['Sx'].attrs['units'] = ''
        rad.create_dataset('error', data=np.array(err_a))
        rad['error'].attrs['units'] = ''

        if make_image:
            stacked_image = f.create_group('image')
            stacked_image.create_dataset('image_dat', data=np.array(counts))




def replace(arr):
    #Replaces zero values
    for i in range(len(arr)):
        for j in range(len(arr)):
            if arr[i][j]==0:   
                arr[i][j] = 10**(-3)
    return arr

def convert_to_erg(e_obs, redshift,dl,emin,emax,arf, arf_e, texp):
	#input array of observed energies in kev
	new_energies = []
	
	for i in range(len(e_obs)):
		if emin<e_obs[i]<emax:
			arf_val = arf[np.argmin(np.absolute(np.array(arf_e)-e_obs[i]))]
			e_rf = e_obs[i]*(1+redshift)
			new_energies.append((4*np.pi*dl**2)*1.602177*10**(-9)*e_rf/(texp*arf_val))
		else:
			new_energies.append(0)
	return new_energies

def bin_energies(rad,energies,r_bins):
    #rad is radius of each pixel in kpc
    #energies is energy of each pixel in erg
	bins = np.digitize(rad,r_bins, right=True)
	binned_e = []
	for i in range(1,len(r_bins)):
		indices=np.where(bins==i)
		vals = np.array(energies)[indices]
		bin_area = [np.pi*(r_bins[i]**2-r_bins[i-1]**2)]
		binned_e.append(np.sum(vals)/bin_area)
	return np.array(binned_e).flatten()