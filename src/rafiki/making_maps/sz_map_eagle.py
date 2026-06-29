import pandas as pd
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u
from mapmaking_functions import *

filename = '/Volumes/easystore/EAGLE/RefL0050N0752/snapshot_027_z000p101/snap_027_z000p101.0.hdf5'
name = '/Volumes/easystore/RAFIKI_CGM_mock_library/EAGLE/snap_z0_1/tSZ/EAGLE_0_1'
z = 0.1 #redshift of your snapshot


#Calculate comoving distance in kpc-use basic cosmology
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
comov = cosmo.comoving_distance(z).to(u.kpc).value 
#Calculate number of pixels in your fixed resolution buffer such that each pixel is theta arcseconds across
theta = 3 #arcseconds
frb=determining_frb_size(50, z, comov, theta) 
print('frb size',frb)

#Generate maps, save 
projection_direction = 'x' #x, y, or z
output_name = name+'_x_szy.npy' #Name must end in '_x[y,z]_szy.npy' 
generating_sz_data_eagle(filename, projection_direction, output_name, frb, z)

projection_direction = 'y' #x, y, or z
output_name = name+'_y_szy.npy' #Name must end in '_x[y,z]_szy.npy' 
generating_sz_data_eagle(filename, projection_direction, output_name, frb, z)

projection_direction = 'z' #x, y, or z
output_name = name+'_z_szy.npy' #Name must end in '_x[y,z]_szy.npy' 
generating_sz_data_eagle(filename, projection_direction, output_name, frb, z)