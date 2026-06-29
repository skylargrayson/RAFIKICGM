'''
This script generates a projected map of the Compton-y signal for use in tSZ analysis. 
Inputs are set in lines 17-22 and explained more in detail in the documentation.
'''

import yt
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import gridspec
import numpy as np
import csv
import math
import pandas as pd



'''
You shouldn't need to adjust below this line
-------------------------------------------------------------
'''


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

def determining_caesar_conversion(box_size, frb):
    '''
    Calculates the factor needed to convert between the scales of the CAESAR output and the frb we generate

    :param box_size: Size of the box in units of Mpccm/h 
    :type box_size: float
    :param frb: Pixel size of your map
    :type frb: int
    :return: Value to divide out of CAESAR coordinates to match your frb
    :rtype: int
    '''

    kpc_size = box_size*1000/0.68
    return kpc_size/frb



def generating_sz_data(filename, projection_direction, output_name, frb, redshift):
    '''
    Cuts ISM and current wind particles, makes a new field of gas pressure, projects this field in the specified direction, and saves a file containing the projected map of the tSZ signal

    :param filename: path to snapshot
    :type filename: str
    :param projection_direction: 'x', 'y', or 'z', the direction you want to project your data in
    :type projection_direction: str
    :param output_name: name of the .npy file that will store the projected SZ data
    :type output_name: str
    :param frb: number of pixels in your fixed resolution buffer. Suggested to correspond to twice the resolution of your observational comp
    :type frb: int
    :param redshift: redshift of the snapshot
    :type redshift: int
    :return: None. Saves a file with the name given in the inputs containing the projected SZ data
    
    '''



    obj = yt.load(filename)
    #Creating derived field of gas pressure
    def _pressure(field, data):
        return (
            data["PartType0", "density"]
            * data["PartType0", "Temperature"]
        )

    obj.add_field(
        name=("PartType0", "pressure"),
        function=_pressure,
        sampling_type="local",
        units="K*code_mass/code_length**3",
    )

    #Cutting ISM and wind particles
    def cuts(pfilter, data):
        filter = np.logical_and(data[(pfilter.filtered_type, "H_nuclei_density")]  < 0.1, 
                                data[(pfilter.filtered_type, "DelayTime")]  <= 0 )
        return filter
    yt.add_particle_filter(
        "szcuts", function=cuts, filtered_type="PartType0",requires=("H_nuclei_density","DelayTime"))
    obj.add_particle_filter("szcuts")

    #Generating projection plot, can change direction of projection in second input
    prj = yt.ProjectionPlot(obj, projection_direction, ('szcuts', 'pressure'))

    #Generating an frb to set pixel size of your map. Resolution currently set to be 1/2 the smallest beam width
    prj.set_buff_size((frb,frb)) 
    data = prj.frb[('szcuts', 'pressure')]

    sz_dat3a = np.array(data)*1.11*10**(-32)*(1+redshift)**3 
    sz_dat = np.array(sz_dat3a)
    #Saves 2D array of projected SZ-y data as a .npy file
    with open(output_name, 'wb') as f:
        np.save(f, np.array(sz_dat))

    

def generating_sz_data_eagle(filename, projection_direction, output_name, frb, redshift):
    '''
    Cuts ISM and current wind particles, makes a new field of gas pressure, projects this field in the specified direction, and saves a file containing the projected map of the tSZ signal

    :param filename: path to snapshot
    :type filename: str
    :param projection_direction: 'x', 'y', or 'z', the direction you want to project your data in
    :type projection_direction: str
    :param output_name: name of the .npy file that will store the projected SZ data
    :type output_name: str
    :param frb: number of pixels in your fixed resolution buffer. Suggested to correspond to twice the resolution of your observational comp
    :type frb: int
    :param redshift: redshift of the snapshot
    :type redshift: int
    :return: None. Saves a file with the name given in the inputs containing the projected SZ data
    
    '''
    obj = yt.load(filename)
    #Creating derived field of gas pressure
    def _pressure(field, data):
        return (
            data["PartType0", "density"]
            * data["PartType0", "Temperature"]
        )

    obj.add_field(
        name=("PartType0", "pressure"),
        function=_pressure,
        sampling_type="local",
        units="K*code_mass/code_length**3",
    )

    # Cutting ISM particles (low-density gas)
    def cuts(pfilter, data):
        return data[(pfilter.filtered_type, "density")]*(2e43/(.68)/(3.18e24/(.68))**3*(1+redshift)**3*(6.023e23)*.76) < (.10)  #conversions

    yt.add_particle_filter(
        "szcuts", function=cuts, filtered_type="PartType0", requires=("density",)
    )
    obj.add_particle_filter("szcuts")

    #Generating projection plot, can change direction of projection in second input
    prj = yt.ProjectionPlot(obj, projection_direction, ('szcuts', 'pressure'))

    #Generating an frb to set pixel size of your map. Resolution currently set to be 1/2 the smallest beam width
    prj.set_buff_size((frb,frb)) 
    data = prj.frb[('szcuts', 'pressure')]

    sz_dat3a = np.array(data)*1.83*10**(-41)*(1+redshift)**3 
    sz_dat = np.array(sz_dat3a)
    #Saves 2D array of projected SZ-y data as a .npy file
    with open(output_name, 'wb') as f:
        np.save(f, np.array(sz_dat))