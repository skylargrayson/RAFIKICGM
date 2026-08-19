import numpy as np
from astropy.convolution import Gaussian2DKernel 
from astropy.convolution import convolve_fft
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u
import math
from scipy.ndimage.interpolation import geometric_transform
from scipy.stats import bootstrap
from scipy.stats import bootstrap
import h5py
from .catalog import load_catalog
from .data_access import download_data
from .utils import redshift_resampling

def determining_frb_size(box_size, z, comov, angular_res):
    '''
    Tells you how many pixels you want in your image for a given angular resolution

    :param box_size: Size of the box in units of Mpccm/h 
    :type box_size: float
    :param z: redshift of your snapshot
    :type z: float
    :param comov: Comoving distance in kpc. Suggested to use Ned Wright's cosmology calculator to determine
    :type comov: float
    :param angular_res: The angular size of each pixel you want in your frb in units of arcseconds
    :type angular_res: float
    :return: How many pixels you want to make your frb to achieve the desired angular resolution
    :rtype: int
    '''

    physical_size = box_size/(1+z)/0.68 #Assuming h = 0.68
    #convert resolution to radians and multiply by comoving distance/(1+z) to get physical size of pixel
    pixel = comov*angular_res*(4.84814*10**(-6))/(1+z) 
    frb = physical_size*1000/pixel
    return math.ceil(frb)


def cut_stamps(config, index_sample): #DONE NOT TESTED
    '''
    Cut out stamps of Compton-y map around every galaxy in the sample. Return nested array of the stamps 

    :param config: input yaml file
    :type config: yaml  
    :param index_sample: array of galaxy indices in the RAFIKI-CGM catalog file that will be used for our mock galaxy sample
    :type index_sample: np.ndarray
    :return: stamps-nested array of 2D stamps centered around each galaxy of interest
    :rtype: np.ndarray
    '''

    #Load relevant info from config
    sim_name = config['package_data']['sim']
    redshift = str(config['package_data']['redshift'])
    pixel_scale = config['sz']['pixel_size_arcsec'] #gives us the physical scale of each pixel in the FRB 
    stamp_width = config['sz']['stamp_width']*60/pixel_scale #gives us stamp width in pixel units
    if sim_name=='EAGLE':
        #Load RAFIKI-CGM galaxy catalog
        ids,stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,redshift)
    else:
        stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,redshift)
        ids=None
    #Map to redshift labels
    red_shift = {'0.1':'0_1', '0.5':'0_5', '1':'1', '1.0':'1','2':'2','2.0':'2','1.':'1','2.':'2'} #To account for possible names
    if redshift not in red_shift:
        raise ValueError(f"⚠️ Redshift '{redshift}' not recognized. Valid options are: 0.1, 0.5, 1, 2")

    
    xfile = download_data(config,f"{sim_name}/snap_z{red_shift[redshift]}/tSZ/{sim_name}_{red_shift[redshift]}_x_szy.npy")
    yfile = download_data(config,f"{sim_name}/snap_z{red_shift[redshift]}/tSZ/{sim_name}_{red_shift[redshift]}_y_szy.npy")
    zfile = download_data(config,f"{sim_name}/snap_z{red_shift[redshift]}/tSZ/{sim_name}_{red_shift[redshift]}_z_szy.npy")

    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    comov = cosmo.comoving_distance(float(redshift)).to(u.kpc).value 
    frb=determining_frb_size(50, float(redshift), comov, pixel_scale) #Number of pixels in your fixed resolution buffer, suggested to correspond to resolution at least twice that of your observational comparison

    sz_dat_x = np.load(xfile)
    stamps_x = cropping_sz_x(sz_dat_x, frb_locs[0], frb_locs[1], frb_locs[2], index_sample, stamp_width, frb) 
    sz_dat_y = np.load(yfile)
    stamps_y = cropping_sz_x(sz_dat_y, frb_locs[0], frb_locs[1], frb_locs[2], index_sample, stamp_width, frb) 
    sz_dat_z = np.load(zfile)
    stamps_z = cropping_sz_z(sz_dat_z, frb_locs[0], frb_locs[1], frb_locs[2], index_sample, stamp_width, frb) 

    return stamps_x+stamps_y+stamps_z


def cropping_sz_x(sz_dat, xs, ys, zs, sample, width, frb):
    ''' 
    Generates a nested 2D array of SZ data in the regions around our sampled galaxies using a data box projected in the x-direction
        
    :param sz_dat: 2D array of projected Compton-y map
    :type sz_dat: list[float]
    :param xs: x-coordinates of locations of galaxies in your box, adjusted to match the pixel frb
    :type xs: list[float]
    :param ys: y-coordinates of locations of galaxies in your box, adjusted to match the pixel frb
    :type ys: list[float]
    :param zs: z-coordinates of locations of galaxies in your box, adjuste to match the pixel frb
    :type zs: list[float]
    :param sample: list of index locations of the galaxies we want to sample (output of ``sorting``)
    :type sample: list[int]
    :param width: the pixel size we want to crop around the galaxies
    :type width: int
    :param frb: pixel size of the SZ data used
    :type frb: int
    :return: lists-Nested array of SZ data for the regions around our sample gaalxies
    :rtype: list[float]
        
    '''

    lists = []
    q = 0
    for i in sample:
        indices_z = range(int(zs[i])-int(width/2),int(zs[i])+int(width/2))
        indices_y = range(int(ys[i])-int(width/2),int(ys[i])+int(width/2))
        #print(indices_z)
        #print(indices_y)
        if width/2<zs[i] < frb-(width/2) and width/2<ys[i] < frb-(width/2): 
            lists.append([])
            lists[q].append(sz_dat[int(zs[i]-width/2):int(zs[i]+width/2),int(ys[i]-width/2):int(ys[i]+width/2)])
            q+=1
        else: #Wrapping data around periodic box if needed
            lists.append([])
            z = sz_dat.take(indices_z, axis = 0, mode='wrap').take(indices_y, axis = 1, mode='wrap')
            lists[q].append(z)
            q+=1
    return lists

def cropping_sz_y(sz_dat, xs, ys, zs,sample, width, frb):
    ''' 
    Generates a nested 2D array of SZ data in the regions around our sampled galaxies using a data box projected in the y-direction
        
    :param sz_dat: 2D array of projected Compton-y map
    :type sz_dat: list[float]
    :param xs: x-coordinates of locations of galaxies in your box, adjusted to match the pixel frb
    :type xs: list[float]
    :param ys: y-coordinates of locations of galaxies in your box, adjusted to match the pixel frb
    :type ys: list[float]
    :param zs: z-coordinates of locations of galaxies in your box, adjuste to match the pixel frb
    :type zs: list[float]
    :param sample: list of index locations of the galaxies we want to sample (output of ``sorting``)
    :type sample: list[int]
    :param width: the pixel size we want to crop around the galaxies
    :type width: int
    :param frb: pixel size of the SZ data used
    :type frb: int
    :return: lists-Nested array of SZ data for the regions around our sample gaalxies
    :rtype: list[float]
        
    '''
    lists = []
    q = 0
    for i in sample:
        indices_z = range(int(zs[i])-int(width/2),int(zs[i])+int(width/2))
        indices_x = range(int(xs[i])-int(width/2),int(xs[i])+int(width/2))

        if width/2<zs[i] < frb-(width/2) and width/2<xs[i] < frb-(width/2): 

            lists.append([])
            lists[q].append(sz_dat[int(xs[i]-width/2):int(xs[i]+width/2),int(zs[i]-width/2):int(zs[i]+width/2)])
            q+=1
        else: #Wrapping data around periodic box if needed
            lists.append([])
            z = sz_dat.take(indices_x, axis = 0, mode='wrap').take(indices_z, axis = 1, mode='wrap')
            lists[q].append(z)
            q+=1
    return lists

def cropping_sz_z(sz_dat, xs, ys, zs, sample, width, frb):
    ''' 
    Generates a nested 2D array of SZ data in the regions around our sampled galaxies using a data box projected in the z-direction
        
    :param sz_dat: 2D array of projected Compton-y map
    :type sz_dat: list[float]
    :param xs: x-coordinates of locations of galaxies in your box, adjusted to match the pixel frb
    :type xs: list[float]
    :param ys: y-coordinates of locations of galaxies in your box, adjusted to match the pixel frb
    :type ys: list[float]
    :param zs: z-coordinates of locations of galaxies in your box, adjuste to match the pixel frb
    :type zs: list[float]
    :param sample: list of index locations of the galaxies we want to sample (output of ``sorting``)
    :type sample: list[int]
    :param width: the pixel size we want to crop around the galaxies
    :type width: int
    :param frb: pixel size of the SZ data used
    :type frb: int
    :return: lists-Nested array of SZ data for the regions around our sample gaalxies
    :rtype: list[float]
        
    '''
    lists = []
    q = 0
    for i in sample:
        indices_y = range(int(ys[i])-int(width/2),int(ys[i])+int(width/2))
        indices_x = range(int(xs[i])-int(width/2),int(xs[i])+int(width/2))

        if width/2<ys[i] < frb-(width/2) and width/2<xs[i] < frb-(width/2): 

            lists.append([])
            lists[q].append(sz_dat[int(ys[i]-width/2):int(ys[i]+width/2),int(xs[i]-width/2):int(xs[i]+width/2)])
            q+=1
        else: #Wrapping data around periodic box if needed
            lists.append([])
            z = sz_dat.take(indices_y, axis = 0, mode='wrap').take(indices_x, axis = 1, mode='wrap')
            lists[q].append(z)
            q+=1
    return lists

def azimuthalAverage(image, pixel_scale, bins, center=None):
    """
    Calculates the azimuthally averaged radial profile. Taken from with some alterations https://github.com/mkolopanis/python/blob/master/radialProfile.py
        
    :param image: 2D array of projected Compton-y map around our galaxy of interest
    :type image: list[float]
    :param center: The [x,y] pixel coordinates used as the center. Default is None, which useds the center of the image
    :type center: list[float] or None
    :return: radial_prof-Radial profile of the azimuthally averaged signal
    :rtype: list[float]
    
    """
    # Calculate the indices from the image

    y, x = np.indices(np.shape(image))

    if not center:
        center = np.array([(x.max()-x.min())/2.0+1, (x.max()-x.min())/2.0+1]) #+1 added because rounding down below
    
    
    r = pixel_scale*np.hypot(x - center[0], y - center[1]) #np.hypot gives the hypotenuse of a triangle with the given legs
    
    # Get sorted radii
    ind = np.argsort(r.flat)  

    r_sorted = r.flat[ind]  #Sorted list of the radii of the pixels, converted to integers below
    i_sorted = image.flat[ind]  #Sorting the image pixels by the radii
     
    which_bin = np.digitize(r_sorted,bins)
    radial_prof=[]
    for i in range(1,len(bins)):
        mask=which_bin==i

        if np.any(mask):
            vals=i_sorted[mask]
            radial_prof.append(np.mean(vals))
        else:
            radial_prof.append(np.nan)

    return radial_prof


def make_stacked_images(stamps, kernel, label,config, index_sample, galaxy_redshifts):
    make_image = config['analysis']['sz_stacked_image']
    pixel_scale = config['sz']['pixel_size_arcsec']* u.arcsec #gives us the physical scale of each pixel in the FRB
    snapshot_redshift = float(config['package_data']['redshift'])

    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    D_map = cosmo.angular_diameter_distance(snapshot_redshift)
    pixel_size_kpc = (pixel_scale.to(u.rad).value * D_map).to(u.kpc).value

    n_gal=len(galaxy_redshifts)

    convolved_stamps= [] 
    for j in range(len(stamps)): 
        galaxy_redshift = galaxy_redshifts[j%n_gal]
        D_A = cosmo.angular_diameter_distance(galaxy_redshift).to(u.kpc).value
        pixel_scale_arcsec = (pixel_size_kpc / D_A * u.rad).to(u.arcsec).value
        kernel_pixels = kernel/ pixel_scale_arcsec
        gauss_kernel = Gaussian2DKernel(kernel_pixels) 
        i = stamps[j]
        dd =convolve_fft(i[0], gauss_kernel)     
        convolved_stamps.append(dd)
    image_dat = np.mean( np.array(convolved_stamps), axis=0)   
    sim_name = str(config['package_data']['sim'])
    redshift = config['package_data']['redshift']
    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.create_dataset('galaxy_indices', data=np.array(index_sample))
            meta.create_dataset('galaxy_redshifts', data=np.array(galaxy_redshifts))  

        if 'image' in f:
            del f['image']
        stacked_image = f.create_group('image')
        stacked_image.create_dataset('image_dat', data=np.array(image_dat))

def CAP_filtering(image, pixel_scale, cap_radii ):
    y, x = np.indices(image.shape)

    center = np.array([
            (x.max() - x.min()) / 2.0 + 1,
            (y.max() - y.min()) / 2.0 + 1 ])
    r = pixel_scale * np.hypot(
        x - center[0],
        y - center[1])

    if np.max(r)>(np.sqrt(2)*np.max(cap_radii)):
        raise ValueError("⚠️ Maximum CAP radii set too high. r*$\sqrt{2}$ must be less than the stamp size.")
    cap = []

    for rad in cap_radii:
        inner = r < rad
        outer =  ((r >= rad) & (r < np.sqrt(2) * rad))
        cap_value = (np.nansum(image[inner])- np.nansum(image[outer]) )
        cap.append(cap_value)

    return(cap)


def make_radial_profiles(stamps, kernel, label,config, index_sample, galaxy_redshifts):
    '''
    Convolves data and generates radial profiles for all galaxies in your sample
        
    :param stamps: A nested array of the SZ data around galaxies. Output of ``cropping_sz`` function
    :type stamps: list[float]
    :param kernel: The standard deviation of the Gaussian kernel in units of arcseconds
    :type kernel: float
    :param label: File name and path to save outputs
    :type label: str
    :param config: input yaml files
    :type config: yaml   
    :return: Saves an hdf5 file containing containing stacked radial profile and meta data about the sample
    '''
    
    #Convert scales for redshifts for each individual galaxy
    make_image = config['analysis']['sz_stacked_image']
    pixel_scale = config['sz']['pixel_size_arcsec']* u.arcsec #gives us the physical scale of each pixel in the FRB
    snapshot_redshift = float(config['package_data']['redshift'])
    radial_bins = np.array(config['sz']['radial_bins'])
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    D_map = cosmo.angular_diameter_distance(snapshot_redshift)
    pixel_size_kpc = (pixel_scale.to(u.rad).value * D_map).to(u.kpc).value

    n_gal=len(galaxy_redshifts)

    #Convolve and generate radial profile
    radial_sample = []
    convolved_stamps= [] 
    for j in range(len(stamps)): 
        galaxy_redshift = galaxy_redshifts[j%n_gal]
        D_A = cosmo.angular_diameter_distance(galaxy_redshift).to(u.kpc).value
        pixel_scale_arcsec = (pixel_size_kpc / D_A * u.rad).to(u.arcsec).value
        kernel_pixels = kernel/ pixel_scale_arcsec
        gauss_kernel = Gaussian2DKernel(kernel_pixels) 
        i = stamps[j]
        dd =convolve_fft(i[0], gauss_kernel)     
        convolved_stamps.append(dd)
        aa=azimuthalAverage(dd, pixel_size_kpc, radial_bins, center = None)  
        radial_sample.append(aa)

    #perform CAP filtering and stack: 
    cap_radii = np.array(config['sz']['CAP_filtering_radii'])
    cap_profiles = []
    
    for stamp in convolved_stamps:
        rad = CAP_filtering(stamp, pixel_size_kpc, cap_radii)
        cap_profiles.append(rad)

    flip_cap = list(zip(*cap_profiles))    
    y_cap = []
    y_cap_err = []
    for i in flip_cap:
        y_cap.append(np.nanmean(i))
        ii = (i,)
        bootstrap_ci = bootstrap(ii, np.nanmean, confidence_level=0.95,
                                random_state=1, method='percentile')
        y_cap_err.append(bootstrap_ci.standard_error)

    flip = list(zip(*radial_sample))
    #Stack and bootstrap errors
    y_a = []
    err_a = []
    for i in flip:
        y_a.append(np.nanmean(i))
        ii = (i,)
        bootstrap_ci = bootstrap(ii, np.nanmean, confidence_level=0.95,
                                random_state=1, method='percentile')
        err_a.append(bootstrap_ci.standard_error)
    
    x_a =  0.5 * (radial_bins[:-1] + radial_bins[1:])
    #Open metadata from config file
    sim_name = str(config['package_data']['sim'])
    redshift = config['package_data']['redshift']
    image_dat = np.mean( np.array(convolved_stamps), axis=0)   
    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['snapshot_redshift']  = str(redshift)
            meta.create_dataset('galaxy_indices', data=np.array(index_sample))
            meta.create_dataset('galaxy_redshifts', data=np.array(galaxy_redshifts))  

        if 'radial_profile' in f:
            del f['radial_profile']
        rad = f.create_group('radial_profile')
        rad.create_dataset('radius', data=np.array(x_a))
        rad['radius'].attrs['units'] = 'kpc'
        rad.create_dataset('compton-y', data=np.array(y_a))
        rad['compton-y'].attrs['units'] = ''
        rad.create_dataset('error', data=np.array(err_a))
        rad['error'].attrs['units'] = ''
        rad.create_dataset('cap_radius', data=np.array(cap_radii))
        rad['cap_radius'].attrs['units'] = 'kpc'
        rad.create_dataset('cap_profile', data=np.array(y_cap))
        rad['cap_profile'].attrs['units'] = ''
        rad.create_dataset('cap_error', data=np.array(y_cap_err))
        rad['cap_error'].attrs['units'] = ''


        if make_image:
            if 'image' in f:
                del f['image']
            stacked_image = f.create_group('image')
            stacked_image.create_dataset('image_dat', data=np.array(image_dat))
    return 



"""FUNCTIONS FOR FINDING MOMENTS """

def topolar(img, pixel_size_kpc, order=1):
    """
    Transforms an image into polar coordinates
        
    :param img: 2D data of the image wanting to transform
    :type img: list[float]
    :param order: The spline interpolation order, default 1
    :type order: int
    :return: Polar-Nested array of image by polar coordinates, (rads, angs)- Values of the radii and angles corresponding to the data in polar
    :rtype: list[float]
    """
    # max_radius is the length of the diagonal 
    # from a corner to the mid-point of img.
    max_radius = 0.5*np.linalg.norm( img.shape )

    def transform(coords):
        # Put coord[1] in the interval, [-pi, pi]
        theta = 2*np.pi*coords[1] / (img.shape[1] - 1.)

        # Then map it to the interval [0, max_radius].
        #radius = float(img.shape[0]-coords[0]) / img.shape[0] * max_radius
        radius = max_radius * coords[0] / img.shape[0]

        i = 0.5*img.shape[0] - radius*np.sin(theta)
        j = radius*np.cos(theta) + 0.5*img.shape[1]
        return i,j

    polar = geometric_transform(img, transform, order=order)

    rads = max_radius * np.linspace(0,1,img.shape[0])*pixel_size_kpc
    angs = np.linspace(0, 2*np.pi, img.shape[1])

    return polar, (rads, angs)

def make_moment_profiles(stamps, kernel, label, config, index_sample, galaxy_redshifts):
    '''
     Generates radial profiles of transformed maps for m=0, 1, and 2
        
    :param stamps: A nested array of the SZ data around galaxies. Output of ``cropping_sz`` function
    :type stamps: list[float]
    :param kernel: The standard deviation of the Gaussian kernel in units of pixels
    :type kernel: float
    :param label: File name and path to save outputs
    :type label: str
    :param config: input yaml files
    :type config: yaml  
    :return: Saves an hdf5 file containing containing stacked ratios of m1/m0 and m2/m0 and meta data about the sample (if not already included from radial analysis)
    '''

    pixel_scale = config['sz']['pixel_size_arcsec']* u.arcsec #gives us the physical scale of each pixel in the FRB
    snapshot_redshift = float(config['package_data']['redshift'])
    radial_bins = np.array(config['sz']['radial_bins'])
    x_a =  0.5 * (radial_bins[:-1] + radial_bins[1:])
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    D_map = cosmo.angular_diameter_distance(snapshot_redshift)
    pixel_size_kpc = (pixel_scale.to(u.rad).value * D_map).to(u.kpc).value
    n_gal = len(galaxy_redshifts)
    data0 = []
    data1 = []
    data2 = []
    n=0
    for j in range(len(stamps)): 

        galaxy_redshift = galaxy_redshifts[j%n_gal]
        D_A = cosmo.angular_diameter_distance(galaxy_redshift).to(u.kpc).value
        pixel_scale_arcsec = (pixel_size_kpc / D_A * u.rad).to(u.arcsec).value
        kernel_pixels = kernel/ pixel_scale_arcsec
        gauss_kernel = Gaussian2DKernel(kernel_pixels) 
        i = stamps[j]
        d =convolve_fft(i[0], gauss_kernel)   
        pol, (rads,angs) = topolar(d, pixel_size_kpc)
        reals0 = []
        imaginaries0 = []
        reals1 = []
        imaginaries1 = []
        reals2 = []
        imaginaries2 = []
        for k in list(pol):
            
            real0 = [k[j]*math.cos(0*angs[j]) for j in range(len(k))]
            imag0 = [k[j]*math.sin(0*angs[j]) for j in range(len(k))]
            reals0.append(np.sum(real0)/(len(real0)))
            imaginaries0.append(np.sum(imag0)/(len(imag0)))
            real1 = [k[j]*math.cos(1*angs[j]) for j in range(len(k))]
            imag1 = [k[j]*math.sin(1*angs[j]) for j in range(len(k))]
            reals1.append(np.sum(real1)/(len(real1)))
            imaginaries1.append(np.sum(imag1)/(len(imag1)))
            real2 = [k[j]*math.cos(2*angs[j]) for j in range(len(k))]
            imag2 = [k[j]*math.sin(2*angs[j]) for j in range(len(k))]
            reals2.append(np.sum(real2)/(len(real2)))
            imaginaries2.append(np.sum(imag2)/(len(imag2)))
        
        
        amplitude0 = np.hypot(reals0, imaginaries0)
        amplitude1 = np.hypot(reals1, imaginaries1)
        amplitude2 = np.hypot(reals2, imaginaries2)

        amp0_binned = []
        amp1_binned = []
        amp2_binned = []

        for i in range(len(radial_bins)-1):

            mask = (rads >= radial_bins[i]) & (rads < radial_bins[i+1])

            if np.any(mask):
                amp0_binned.append(np.nanmean(amplitude0[mask]))
                amp1_binned.append(np.nanmean(amplitude1[mask]))
                amp2_binned.append(np.nanmean(amplitude2[mask]))
            else:
                amp0_binned.append(np.nan)
                amp1_binned.append(np.nan)
                amp2_binned.append(np.nan)


        data0.append(amp0_binned)
        data1.append(amp1_binned)
        data2.append(amp2_binned)
        #data.append(profile)
        n+=1
    data_a = list(zip(*data0))
    data_b = list(zip(*data1))
    data_c = list(zip(*data2))

    #creating moment ratios
    m_a = [np.mean(data_b[i])/np.mean(data_a[i]) for i in range(len(data_b))]
    m_b = [np.mean(data_c[i])/np.mean(data_a[i]) for i in range(len(data_c))]

    #Generating error bars
    y_a = []
    for j in range(len(data0[1])):
        y_a.append([])
        for i in range(4000):
            indices = np.random.choice(len(data_a[0]), len(data_a[0]), replace=True)
            new_b = [data_b[j][k] for k in indices]
            new_a = [data_a[j][k] for k in indices]
            y_a[j].append(np.mean(new_b)/np.mean(new_a))

    err_a = []
    for i in range(len(y_a)):
        err_a.append(np.std(y_a[i]))

    y_b = []

    for j in range(len(data0[1])):
        y_b.append([])
        #print(j)
        for i in range(4000):
            indices = np.random.choice(len(data_a[0]), len(data_a[0]), replace=True)
            new_c = [data_c[j][k] for k in indices]
            new_a = [data_a[j][k] for k in indices]
            y_b[j].append(np.mean(new_c)/np.mean(new_a))
    err_b = []
    for i in range(len(y_b)):
        err_b.append(np.std(y_b[i]))


    sim_name = str(config['package_data']['sim'])
    redshift = config['package_data']['redshift']

    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.create_dataset('galaxy_indices', data=np.array(index_sample))
            meta.create_dataset('galaxy_redshifts', data=np.array(galaxy_redshifts))  
        if 'moment_profiles' in f:
            del f['moment_profiles']
        rad = f.create_group('moment_profiles')
        rad.create_dataset('radius', data=np.array(x_a))
        rad['radius'].attrs['units'] = 'kpc'
        rad.create_dataset('moment_1', data=np.array(m_a))
        rad['moment_1'].attrs['units'] = ''
        rad.create_dataset('m1_error', data=np.array(err_a))
        rad['m1_error'].attrs['units'] = ''
        rad.create_dataset('moment_2', data=np.array(m_b))
        rad['moment_2'].attrs['units'] = ''
        rad.create_dataset('m2_error', data=np.array(err_b))
        rad['m2_error'].attrs['units'] = ''



"""THERMAL ENERGY"""

def thermal_energy(stamps, kernel, label, aperture, config, gal_sample_indices, galaxy_redshifts):
    """
    Calculates the thermal energy in a given aperture from maps of SZ-y data
        
    :param stamps: A nested array of the SZ data around galaxies.
    :type stamps: list[float]
    :param kernel: The standard deviation of the Gaussian kernel in units of arcseconds
    :type kernel: float
    :param label: File name and path to save outputs
    :type label: str
    :param aperture: pixel size of the radius of the aperture within which you want to caculate thermal energy
    :type aperture: float
    :param gal_sample_indices: indices of the galaxies in the catalog used to creat the stamps
    :type gal_sample_indices: list[float]
    :param config: input yaml files
    :type config: yaml  
    :return: Saves an hdf5 file containing thermal energy as a function of stellar and halo mass and meta data about the sample (if not already included from radial analysis)

    """
    pixel_scale = config['sz']['pixel_size_arcsec']* u.arcsec #gives us the physical scale of each pixel in the FRB
    snapshot_redshift = float(config['package_data']['redshift'])
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    D_map = cosmo.angular_diameter_distance(snapshot_redshift)
    pixel_size_kpc = (pixel_scale.to(u.rad).value * D_map).to(u.kpc).value
    n_gal=len(galaxy_redshifts)
    therm=[]
    for j in range(len(stamps)): 
        galaxy_redshift = galaxy_redshifts[j%n_gal]
        D_A = cosmo.angular_diameter_distance(galaxy_redshift).to(u.kpc).value
        pixel_scale_arcsec = (pixel_size_kpc / D_A * u.rad).to(u.arcsec).value
        kernel_pixels = kernel/ pixel_scale_arcsec
        gauss_kernel = Gaussian2DKernel(kernel_pixels) 
        i = stamps[j]
        image =convolve_fft(i[0], gauss_kernel)    
        y, x = np.indices(image.shape)

        aperture_pixels = aperture/pixel_scale_arcsec
        center = np.array([(x.max()-x.min())/2.0+1, (x.max()-x.min())/2.0+1]) #+1 added because rounding down below
        r = np.hypot(x - center[0], y - center[1]) #np.hypot gives the hypotenuse of a triangle with the given legs
        # Get sorted radii
        ind = np.argsort(r.flat)  
        r_sorted = r.flat[ind]  #Sorted list of the radii of the pixels, converted to integers below
        i_sorted = image.flat[ind]  #Sorting the image pixels by the radii 
        # Get the integer part of the radii (bin size = 1)
        r_int = r_sorted.astype(int)

        new_r_int=[]
        for i in r_int:
            if i<= aperture_pixels:
                new_r_int.append(i)

        l = len(new_r_int)
        i_sorted_new = i_sorted[0:l]
        total = np.sum(i_sorted_new)
        comov = cosmo.comoving_distance(float(galaxy_redshift)).to(u.Gpc).value 
        therm.append(2.9 * (comov/(1+galaxy_redshift))**2 * (total*(pixel_scale_arcsec/60)**2)/(10**(-6)))
    

    redshift = str(config['package_data']['redshift'])
    sim_name = config['package_data']['sim']
    if sim_name=='EAGLE':
        #Load RAFIKI-CGM galaxy catalog
        ids,stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,redshift)
    else:
        stell, halo, rad, age, sfr, ssfr,frb_locs,centrals=load_catalog(config,redshift)
        ids=None
    stellarm = np.tile(np.array(stell)[gal_sample_indices], 3)
    halom = np.tile(np.array(halo)[gal_sample_indices], 3)
    stellar_bins = np.array(config['sz']['thermal_energy']['stellar_mass_bins'])
    halo_bins = np.array(config['sz']['thermal_energy']['halo_mass_bins'])
    thresholds_stellar = [10 ** x for x in stellar_bins] #Convert to solar units
    thresholds_halo = [10 ** x for x in halo_bins] #Convert to solar units

    combined_data = [stellarm, halom, therm]

    y,err,y2,err2 = make_thermal_energy_plot(combined_data, thresholds_stellar, thresholds_halo)

    sim_name = str(config['package_data']['sim'])
    redshift = config['package_data']['redshift']
    thresholds_stellar=np.array(thresholds_stellar)
    thresholds_halo=np.array(thresholds_halo)
    x_stellar =  0.5 * (thresholds_stellar[:-1] + thresholds_stellar[1:])
    x_halo=  0.5 * (thresholds_halo[:-1] + thresholds_halo[1:])
    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.create_dataset('galaxy_indices', data=np.array(gal_sample_indices))
            meta.create_dataset('galaxy_redshifts', data=np.array(galaxy_redshifts))  
        if 'metadata/therm_cuts' not in f:
            therm_cuts = f.create_group('metadata/therm_cuts')
            therm_cuts.attrs['radius']=aperture
        if 'thermal_energy' in f:
            del f['thermal_energy']
        rad = f.create_group('thermal_energy')
        rad.create_dataset('stellar_mass', data=np.array(x_stellar))
        rad['stellar_mass'].attrs['units'] = 'Solar'
        rad.create_dataset('halo_mass', data=np.array(x_halo))
        rad['halo_mass'].attrs['units'] = 'Solar'
        rad.create_dataset('thermal_stellar', data=np.array(y))
        rad['thermal_stellar'].attrs['units'] = '10^60 ergs'
        rad.create_dataset('thermal_stellar_error', data=np.array(err))
        rad['thermal_stellar_error'].attrs['units'] = '10^60 ergs'
        rad.create_dataset('thermal_halo', data=np.array(y2))
        rad['thermal_halo'].attrs['units'] = '10^60 ergs'
        rad.create_dataset('thermal_halo_error', data=np.array(err2))
        rad['thermal_halo_error'].attrs['units'] = '10^60 ergs'
      

def make_thermal_energy_plot(data, thresholds_stellar, thresholds_halo):
    '''
    Generates data and error on thermal energy values for stacked galaxies

    :param data: Nested list containing stellar masses of galaxies, halo masses of galaxies, and thermal energy around each galaxy
    :type data: list[float]
    :param thresholds_stellar: Bin limits for stacking by stellar mass
    :type thresholds_stellar: list[float]
    :param thresholds_halo: Bin limits for stacking by halo mass
    :type thresholds_halo: list[float]
    :return: y-Thermal energy of stacked galaxies in each stellar mass bin, err-Error on thermal energy of stacked galaxies in each stellar mass bin, y2$
    :rtype: list[float]

    '''
    bins = [[] for _ in range(len(thresholds_stellar) - 1)]
    therms = [[] for _ in range(len(thresholds_stellar) - 1)]


    for i, s in enumerate(data[0]):
        for j, threshold in enumerate(thresholds_stellar[:-1]):
          
            if threshold < s < thresholds_stellar[j + 1]:
                bins[j].append(i)
                therms[j].append(data[2][i])
                break

    bins2 = [[] for _ in range(len(thresholds_halo) - 1)]
    therms2 = [[] for _ in range(len(thresholds_halo) - 1)]

    for i, s in enumerate(data[1]):
        for j, threshold in enumerate(thresholds_halo[:-1]):
            if threshold < s < thresholds_halo[j + 1]:
                bins2[j].append(i)
                therms2[j].append(data[2][i])
                break
    # Combine results for therm and mass
    comb = therms
    comb_mass = [data[0][b] for b in bins]
    comb2 = therms2
    comb_mass2 = [data[1][b] for b in bins2]


    y = []
    err = []
    for j in range(len(thresholds_stellar)-1):
        i = comb[j]
        if len(i) != 0:
            y.append(np.mean(i))
            ii = (i,)
            bootstrap_ci = bootstrap(ii, np.mean, confidence_level=0.95,
                         random_state=1, method='percentile')
            err.append(bootstrap_ci.standard_error)
        else:
            y.append(0.0)
            err.append(0.0)

    y2 = []
    err2 = []
    for j in range(len(thresholds_halo)-1):
        i = comb2[j]
        if len(i) != 0:
            y2.append(np.mean(i))
            ii = (i,)
            bootstrap_ci = bootstrap(ii, np.mean, confidence_level=0.95,
                         random_state=1, method='percentile')
            err2.append(bootstrap_ci.standard_error)
        else:
            y2.append(0.0)
            err2.append(0.0)

    return(y,err,y2,err2)


#Bootstrapping tools

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


