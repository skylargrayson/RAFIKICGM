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
    path_to_package_data = config['package_data']['path']
    sim_name = config['package_data']['sim']
    redshift = str(config['sz']['redshift'])
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
        raise ValueError(f"Redshift '{redshift}' not recognized. Valid options are: 0.1, 0.5, 1, 2")

    sz_dat_path = path_to_package_data+sim_name+'/snap_z'+red_shift[redshift]+'/tSZ/'+sim_name+'_'+red_shift[redshift]
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    comov = cosmo.comoving_distance(float(redshift)).to(u.kpc).value 
    frb=determining_frb_size(50, float(redshift), comov, pixel_scale) #Number of pixels in your fixed resolution buffer, suggested to correspond to resolution at least twice that of your observational comparison


    sz_dat_x = np.load(sz_dat_path+'_x_szy.npy')
    stamps_x = cropping_sz_x(sz_dat_x, frb_locs[0], frb_locs[1], frb_locs[2], index_sample, stamp_width, frb) 
    sz_dat_y = np.load(sz_dat_path+'_y_szy.npy')
    stamps_y = cropping_sz_x(sz_dat_y, frb_locs[0], frb_locs[1], frb_locs[2], index_sample, stamp_width, frb) 
    sz_dat_z = np.load(sz_dat_path+'_z_szy.npy')
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

def azimuthalAverage(image, center=None):
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
    
    
    r = np.hypot(x - center[0], y - center[1]) #np.hypot gives the hypotenuse of a triangle with the given legs
    
    # Get sorted radii
    ind = np.argsort(r.flat)  

    r_sorted = r.flat[ind]  #Sorted list of the radii of the pixels, converted to integers below
    i_sorted = image.flat[ind]  #Sorting the image pixels by the radii
     
    # Get the integer part of the radii (bin size = 1)
    r_int = r_sorted.astype(int)

    # Find all pixels that fall within each radial bin.
    deltar = r_int[1:] - r_int[:-1]# Assumes all radii represented
    rind3 = np.where(deltar)[0] # location of changed radius
    rind = np.insert(rind3, 0, 0)
    nr = rind[1:] - rind[:-1] # number of radius bin
    
    
    # Cumulative sum to figure out sums for each radius bin
    csim = np.cumsum(i_sorted, dtype=float)
    tbin = csim[rind[1:]] - csim[rind[:-1]]
    
    radial_prof = tbin / nr
    
    #Below is my addition for calculating error, breaks up pixels into separate sub-arrays by radius range, averages. 
    split = [i_sorted[rind[r]:rind[r+1]] for r in range(len(rind)-1)]
 
    errors = [np.std(split[i])/np.sqrt(len(split[i]))for i in range(len(split))]
    return radial_prof


def make_stacked_sz_image(stamps,kernel,label, config,index_sample):
    '''
    Convolves data and generates a 2D map of the stacked compton-y parameter for galaxies in the sample
        
    :param stamps: A nested array of the SZ data around galaxies. Output of ``cropping_sz`` function
    :type stamps: list[float]
    :param kernel: The standard deviation of the Gaussian kernel in units of pixels
    :type kernel: float
    :param label: File name and path to save outputs
    :type label: str
    :param config: input yaml files
    :type config: yaml   
    :return: Saves an hdf5 file containing containing stacked radial profile and meta data about the sample
    '''
    sim_name = str(config['package_data']['sim'])
    redshift = config['sz']['redshift']
    gauss_kernel = Gaussian2DKernel(kernel) 
    convolved_stamps = []
    for i in stamps: 
        convolved_stamps.append(convolve_fft(i[0], gauss_kernel))
    stacked = np.mean( np.array(convolved_stamps), axis=0)   

    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.attrs['galaxy_indices']=np.array(index_sample)
        if 'image' in f:
            del f['image']
        rad = f.create_group('image')
        rad.create_dataset('image_dat', data=np.array(stacked))



def make_radial_profiles(stamps, kernel, label,config, index_sample):
    '''
    Convolves data and generates radial profiles for all galaxies in your sample
        
    :param stamps: A nested array of the SZ data around galaxies. Output of ``cropping_sz`` function
    :type stamps: list[float]
    :param kernel: The standard deviation of the Gaussian kernel in units of pixels
    :type kernel: float
    :param label: File name and path to save outputs
    :type label: str
    :param config: input yaml files
    :type config: yaml   
    :return: Saves an hdf5 file containing containing stacked radial profile and meta data about the sample
    '''
   

    #Convolve and generate radial profile
    gauss_kernel = Gaussian2DKernel(kernel) 
    radial_sample = []
    for i in stamps: 
        dd =convolve_fft(i[0], gauss_kernel)     
        aa=azimuthalAverage(dd, center = None)     
        radial_sample.append(aa)
    flip = list(zip(*radial_sample))
    #Stack and bootstrap errors
    y_a = []
    err_a = []
    for i in flip:
        y_a.append(np.mean(i))
        ii = (i,)
        bootstrap_ci = bootstrap(ii, np.mean, confidence_level=0.95,
                                random_state=1, method='percentile')
        err_a.append(bootstrap_ci.standard_error)
       
    pixel_scale = float(config['sz']['pixel_size_arcsec'])
    x_a = [(i*pixel_scale)/60 for i in range(len(y_a))] #convert radial profiles from pixel units to arcminutes
    #Open metadata from config file
    sim_name = str(config['package_data']['sim'])
    redshift = config['sz']['redshift']

    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.attrs['galaxy_indices']=np.array(index_sample)

        if 'radial_profile' in f:
            del f['radial_profile']
        rad = f.create_group('radial_profile')
        rad.create_dataset('radius', data=np.array(x_a))
        rad['radius'].attrs['units'] = 'Arcminutes'
        rad.create_dataset('compton-y', data=np.array(y_a))
        rad['compton-y'].attrs['units'] = ''
        rad.create_dataset('error', data=np.array(err_a))
        rad['error'].attrs['units'] = ''

    return 



"""FUNCTIONS FOR FINDING MOMENTS """

def topolar(img, order=1):
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

    rads = max_radius * np.linspace(0,1,img.shape[0])
    angs = np.linspace(0, 2*np.pi, img.shape[1])

    return polar, (rads, angs)

def make_moment_profiles(stamps, kernel, label, config, index_sample):
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
    data0 = []
    data1 = []
    data2 = []
    n=0
    gauss_kernel = Gaussian2DKernel(kernel) 
    for i in stamps: 
        d =convolve_fft(i[0], gauss_kernel)  
      
        pol, (rads,angs) = topolar(d)
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
        
        
        amplitude0 = [np.sqrt(reals0[h]**2+imaginaries0[h]**2) for h in range(len(reals0))]
        amplitude1 = [np.sqrt(reals1[h]**2+imaginaries1[h]**2) for h in range(len(reals1))]
        amplitude2 = [np.sqrt(reals2[h]**2+imaginaries2[h]**2) for h in range(len(reals2))]
        data0.append(amplitude0)
        data1.append(amplitude1)
        data2.append(amplitude2)
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


    pixel_scale = float(config['sz']['pixel_size_arcsec'])
    x_a = [(i*pixel_scale)/60 for i in range(len(y_a))] #convert radial profiles from pixel units to arcminutes
    #Open metadata from config file
    sim_name = str(config['package_data']['sim'])
    redshift = config['sz']['redshift']

    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.attrs['galaxy_indices']=np.array(index_sample)
        if 'moment_profiles' in f:
            del f['moment_profiles']
        rad = f.create_group('moment_profiles')
        rad.create_dataset('radius', data=np.array(x_a))
        rad['radius'].attrs['units'] = 'Arcminutes'
        rad.create_dataset('moment_1', data=np.array(m_a))
        rad['moment_1'].attrs['units'] = ''
        rad.create_dataset('m1_error', data=np.array(err_a))
        rad['m1_error'].attrs['units'] = ''
        rad.create_dataset('moment_2', data=np.array(m_b))
        rad['moment_2'].attrs['units'] = ''
        rad.create_dataset('m2_error', data=np.array(err_b))
        rad['m2_error'].attrs['units'] = ''



"""THERMAL ENERGY"""

def thermal_energy(stamps, kernel, label, aperture, comov, z, theta, gal_sample_indices, config):
    """
    Calculates the thermal energy in a given aperature from maps of SZ-y data
        
    :param stamps: A nested array of the SZ data around galaxies.
    :type stamps: list[float]
    :param kernel: The standard deviation of the Gaussian kernel in units of pixels
    :type kernel: float
    :param label: File name and path to save outputs
    :type label: str
    :param aperture: pixel size of the radius of the aperture within which you want to caculate thermal energy
    :type aperture: float
    :param comov: comoving distance in Gpc
    :type comov: float
    :param z: Redshift of snapshot
    :type z: float
    :param theta: pixel size in arcseconds
    :type theta: float
    :param gal_sample_indices: indices of the galaxies in the catalog used to creat the stamps
    :type gal_sample_indices: list[float]
    :param config: input yaml files
    :type config: yaml  
    :return: Saves an hdf5 file containing thermal energy as a function of stellar and halo mass and meta data about the sample (if not already included from radial analysis)

    """

    gauss_kernel = Gaussian2DKernel(kernel) 
    energies = []
    for i in stamps:
        image= convolve_fft(i[0], gauss_kernel)
        y, x = np.indices(image.shape)
        
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
            if i<= aperture:
                new_r_int.append(i)

        l = len(new_r_int)
        i_sorted_new = i_sorted[0:l]
        total = np.sum(i_sorted_new)
        energies.append(total)
    
    therm = []
    for i in energies:
        therm.append(2.9 * (comov/(1+z))**2 * (i*(theta/60)**2)/(10**(-6)))
    redshift = str(config['sz']['redshift'])
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
    redshift = config['sz']['redshift']
    
    with h5py.File(label+'_szdat.hdf5', 'a') as f: 
        if 'metadata' not in f:
            meta = f.create_group('metadata') 
            meta.attrs['simulation'] = sim_name
            meta.attrs['redshift']  = str(redshift)
            meta.attrs['galaxy_indices']=np.array(gal_sample_indices)
            therm_cuts = f.create_group('metadata/therm_cuts')
            therm_cuts.attrs['radius']=aperture
        if 'metadata/therm_cuts' not in f:
            therm_cuts = f.create_group('metadata/therm_cuts')
            therm_cuts.attrs['radius']=aperture
        if 'thermal_energy' in f:
            del f['thermal_energy']
        rad = f.create_group('thermal_energy')
        rad.create_dataset('stellar_mass', data=np.array(thresholds_stellar[1:-1]))
        rad['stellar_mass'].attrs['units'] = 'Solar'
        rad.create_dataset('halo_mass', data=np.array(thresholds_halo[1:-1]))
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


