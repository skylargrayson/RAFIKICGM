import yt
import pyxsim
import soxs
import caesar
import numpy as np
from yt.utilities.cosmology import Cosmology

from concurrent.futures import ProcessPoolExecutor

#CLEAN SCRIPT
soxs.set_soxs_config("frgnd_spec_model", "halosat")
cosmo = Cosmology(hubble_constant=0.6774, omega_matter=0.3089, omega_lambda=0.6911)
#Load in relevant files
ds = yt.load('/Volumes/easystore/allphys/snap_m50n512_145.hdf5')
gals = caesar.load('/Volumes/easystore/allphys/m50n512_145.hdf5')


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

ds.add_field(
        name=("gascuts", "emission_measure"),
        function=_emission_measure,
        sampling_type="local",
        units="cm**(-3)",
    )

#Extract galaxy quantities
galaxies_pos = [i.pos for i in gals.galaxies]
galaxy_stellar = [float(i.masses['stellar'].d) for i in gals.galaxies]
halo = [float(i.halo.masses['dm'].d) for i in gals.galaxies]
rad = [float(i.halo.virial_quantities['r200c'].d) for i in gals.galaxies]
ages = [float(i.ages['mass_weighted'].d) for  i in gals.galaxies]
sfr = [float(i.sfr.d )for  i in gals.galaxies]



radius=1500

def process_galaxy(i):
    ad = ds.sphere(galaxies_pos[i], (radius, "kpc"))

    fields = [
        ("gascuts", "particle_position_x"),
        ("gascuts", "particle_position_y"),
        ("gascuts", "particle_position_z"),
        ("gascuts", "velocity_x"),
        ("gascuts", "velocity_y"),
        ("gascuts", "velocity_z"),
        ("gascuts", "density"),
        ("gascuts", "emission_measure"),
        ("gascuts", "temperature"),
        ("gascuts", "metallicity"),
        ("gascuts", "mass"),
        ("gascuts", "smoothing_length"),
    ]

    data = {field: ad[field] for field in fields}
    yt.save_as_dataset(
            ad.ds,
            f"/Volumes/easystore/RAFIKI_CGM_mock_library/SIMBA/snap_z0_1/X-ray/particles/galaxy_{i}.h5",
            data=data
        )


index_sample_a = [i for i in range(501)]
if __name__ == '__main__':
    with ProcessPoolExecutor(8) as executor:
        executor.map(process_galaxy, index_sample_a)