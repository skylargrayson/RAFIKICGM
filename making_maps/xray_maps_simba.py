import yt
import pyxsim
import soxs
import caesar
import numpy as np
from yt.utilities.cosmology import Cosmology
import os
import csv
from concurrent.futures import ProcessPoolExecutor

soxs.set_soxs_config("frgnd_spec_model", "halosat")


cosmo = Cosmology(hubble_constant=0.6774, omega_matter=0.3089, omega_lambda=0.6911)
#Load in relevant files
ds = yt.load('/Volumes/easystore/allphys/snap_m50n512_145.hdf5')
gals = caesar.load('/Volumes/easystore/allphys/m50n512_145.hdf5')

output_directory = "/Volumes/easystore/RAFIKI_CGM_mock_library/SIMBA/snap_z0_1/X-ray/pyxsim/"


redshift = 0.1

exp=2000 #in ks


#Cutting ISM and wind particles
def _delay(field, data):
    return ( data["PartType0", "DelayTime"]
    )

yt.add_field(
    ("gas", "DelayTime"),
    function=_delay,
    sampling_type="local",
    units="auto",
    dimensions=1,
)

def cuts(pfilter, data):
    filter = np.logical_and(data[(pfilter.filtered_type, "H_nuclei_density")]  < 0.1, 
                                data[(pfilter.filtered_type, "DelayTime")]  <= 0 )
    return filter
yt.add_particle_filter(
    "cuts", function=cuts, filtered_type="PartType0",requires=["H_nuclei_density", "DelayTime"])

def gascuts(pfilter, data):
    filter = np.logical_and(data[(pfilter.filtered_type, "H_nuclei_density")]  < 0.1, 
                                data[(pfilter.filtered_type, "DelayTime")]  <= 0 )
    return filter
yt.add_particle_filter(
    "gascuts", function=gascuts, filtered_type="gas",requires=["H_nuclei_density", "DelayTime"])
ds.add_particle_filter("cuts")
ds.add_particle_filter("gascuts")

def _emission_measure(field, data):
    dV = data[ftype, "mass"] / data[ftype, "density"]
    nenhdV = data[ftype, "H_nuclei_density"] * dV
    nenhdV *= data[ftype, "El_number_density"]
    return nenhdV

#Extract galaxy quantities
galaxies_pos = [i.pos for i in gals.galaxies]
galaxy_stellar = [float(i.masses['stellar'].d) for i in gals.galaxies]
halo = [float(i.halo.masses['dm'].d) for i in gals.galaxies]
rad = [float(i.halo.virial_quantities['r200c'].d) for i in gals.galaxies]
ages = [float(i.ages['mass_weighted'].d) for  i in gals.galaxies]
sfr = [float(i.sfr.d )for  i in gals.galaxies]

#Various parameters to set

exp_time = (exp, "ks") 
area = (2100.0, "cm**2")  # collecting area
#radius = 200 #radius in kpc you want around each galaxy

#Make X-ray source model (thermal CIE) and xray fields
source_model = pyxsim.CIESourceModel("apec", 0.5, 2.0, 1000, Zmet =('cuts', 'metallicity'), temperature_field = ('gascuts', 'temperature'),emission_measure_field=('gascuts','emission_measure'))
xray_fields = source_model.make_source_fields(ds, 0.5, 2.0)


def process_galaxy(i):
    #where i is the index of the galaxy we want to sample
    radius=1500
    ad = ds.sphere(galaxies_pos[i], (radius, "kpc"))
    with open(output_directory+'galaxy_sample_properties.csv','a', newline = '') as f: 
        w = csv.writer(f)
        c = w.writerow([galaxy_stellar[i],halo[i],rad[i],ages[i],sfr[i]])
    n_photons, n_cells = pyxsim.make_photons(output_directory+"gal_sample_"+str(i)+"_photons", ad, redshift, area,exp*1000, source_model)
    print('Finished making photons',i)
    #Generating events projected along the x direction 
    n_events = pyxsim.project_photons(output_directory+"gal_sample_"+str(i)+"_photons", output_directory+"gal_sample_"+str(i)+"_x_events", 'x', (0.0, 0.0)) #Last line is ra and dec
    print('Finished making events x',i)
    n_events = pyxsim.project_photons(output_directory+"gal_sample_"+str(i)+"_photons", output_directory+"gal_sample_"+str(i)+"_y_events", 'y', (0.0, 0.0))
    print('Finished making events y',i)
    n_events = pyxsim.project_photons(output_directory+"gal_sample_"+str(i)+"_photons", output_directory+"gal_sample_"+str(i)+"_z_events", 'z', (0.0, 0.0))
    print('Finished making events z',i)

    os.remove(output_directory+"gal_sample_"+str(i)+"_photons.h5")

index_sample_a = [i for i in range(501)]
if __name__ == '__main__':
    with ProcessPoolExecutor(8) as executor:
        executor.map(process_galaxy, index_sample_a)

