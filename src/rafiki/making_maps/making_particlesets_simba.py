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
ds = yt.load('/Volumes/easystore/2025_Pleiades_Runs/z_01/snap_m50n512_1_0125_025.hdf5')
gals = caesar.load('/Volumes/easystore/2025_Pleiades_Runs/z_01/m50n512_1_0125_025.hdf5')


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
    #ACCOUNT FOR PERIODIC BOUNDARIES-ADJUST COORDINATES
    sphere_center = ds.arr(galaxies_pos[i],"code_length")
    x = ad[("gascuts", "particle_position_x")].to("cm")
    y = ad[("gascuts", "particle_position_y")].to("cm")
    z = ad[("gascuts", "particle_position_z")].to("cm")

    center_cm = sphere_center.to("cm")
    L = ds.domain_width.to("cm")

    dx = x - center_cm[0]
    dy = y - center_cm[1]
    dz = z - center_cm[2]

    dx[dx >  L[0]/2] -= L[0]
    dx[dx < -L[0]/2] += L[0]

    dy[dy >  L[1]/2] -= L[1]
    dy[dy < -L[1]/2] += L[1]

    dz[dz >  L[2]/2] -= L[2]
    dz[dz < -L[2]/2] += L[2]


    data = {
    ("gascuts", "particle_position_x"): dx,
    ("gascuts", "particle_position_y"): dy,
    ("gascuts", "particle_position_z"): dz,
    ("gascuts", "velocity_x"): ad[("gascuts", "velocity_x")],
    ("gascuts", "velocity_y"): ad[("gascuts", "velocity_y")],
    ("gascuts", "velocity_z"): ad[("gascuts", "velocity_z")],
    ("gascuts", "density"): ad[("gascuts", "density")],
    ("gascuts", "emission_measure"): ad[("gascuts", "emission_measure")],
    ("gascuts", "temperature"): ad[("gascuts", "temperature")],
    ("gascuts", "metallicity"): ad[("gascuts", "metallicity")],
    ("gascuts", "mass"): ad[("gascuts", "mass")],
    ("gascuts", "smoothing_length"): ad[("gascuts", "smoothing_length")]}

    yt.save_as_dataset(
            ad.ds,
            f"/Volumes/easystore/RAFIKI_CGM_mock_library/RAFIKI_A/snap_z0_1/X-ray/particles/galaxy_{i}.h5",
            data=data
        )


index_sample_a = [i for i in range(501)]
if __name__ == '__main__':
    with ProcessPoolExecutor(8) as executor:
        executor.map(process_galaxy, index_sample_a)