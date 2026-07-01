import yt
import pyxsim
import soxs
import caesar
import numpy as np
from yt.utilities.cosmology import Cosmology
from concurrent.futures import ProcessPoolExecutor
import eagleSqlTools as sql

#CLEAN SCRIPT
soxs.set_soxs_config("frgnd_spec_model", "halosat")
cosmo = Cosmology(hubble_constant=0.6774, omega_matter=0.3089, omega_lambda=0.6911)
#Load in relevant files
ds = yt.load('/Volumes/easystore/EAGLE/RefL0050N0752/snapshot_027_z000p101/snap_027_z000p101.0.hdf5')
#Extract galaxy quantities
con = sql.connect("hhb195", password= "YCV99tfw")
sim_name = 'RefL0050N0752'
snapshot = 27

# SQL query to extract relevant galaxy properties
query = f"""
SELECT 
    SH.MassType_Star AS stellar_mass,
    FOF.GroupMass as halo_mass,
    SH.InitialMassWeightedStellarAge AS mass_weighted_age,
    SH.StarFormationRate AS sfr,
    SH.CentreOfPotential_X AS xpos,
    SH.CentreOfPotential_Y AS ypos,
    SH.CentreOfPotential_Z AS zpos,
    SH.GalaxyID AS id
FROM 
    {sim_name}_SubHalo AS SH,
    {sim_name}_FOF as FOF
WHERE 
    SH.SnapNum = {snapshot} AND
    SH.MassType_Star > 1e8 AND
    FOF.SnapNum = SH.SnapNum AND  
    FOF.GroupID = SH.GroupID

"""

# Execute 
data = sql.execute_query(con, query)

galaxy_ids = np.array(data['id'])
galaxy_stellar = np.array(data['stellar_mass'])  
halo = np.array(data['halo_mass'])    
ages = np.array(data['mass_weighted_age'])  
sfr = np.array(data['sfr'])  
# Extract positions and apply necessary scaling if needed
xpos = np.array(data['xpos'])
ypos = np.array(data['ypos'])
zpos = np.array(data['zpos'])

stellar_mass_dict = {}
halo_mass_dict = {}
ages_dict = {}
sfr_dict = {}
xpos_dict = {}
ypos_dict = {}
zpos_dict = {}

# Populate dictionaries
for i, galaxy_id in enumerate(galaxy_ids):
    stellar_mass_dict[galaxy_id] = galaxy_stellar[i]
    halo_mass_dict[galaxy_id] = halo[i]
    ages_dict[galaxy_id] = ages[i]
    sfr_dict[galaxy_id] = sfr[i]
    xpos_dict[galaxy_id] = xpos[i]
    ypos_dict[galaxy_id] = ypos[i]
    zpos_dict[galaxy_id] = zpos[i]


galaxy_sample_ids = [] 
for i in stellar_mass_dict.keys():
    if 10**(10.6)<=stellar_mass_dict[i]:
        galaxy_sample_ids.append(i)


def cuts(pfilter, data):
    filter = data[(pfilter.filtered_type, "H_nuclei_density")]  < 0.1
    return filter
yt.add_particle_filter(
    "cuts", function=cuts, filtered_type="PartType0",requires=["H_nuclei_density"])

def gascuts(pfilter, data):
    filter = data[(pfilter.filtered_type, "H_nuclei_density")]  < 0.1
    return filter
yt.add_particle_filter("gascuts", function=gascuts, filtered_type="gas", requires=["H_nuclei_density"])

ds.add_particle_filter("cuts")
ds.add_particle_filter("gascuts")

def _emission_measure(field, data):
        dV = data["gascuts", "mass"] / data["gascuts", "density"]
        nenhdV = data["gascuts", "H_nuclei_density"] * dV
        nenhdV *= data["gascuts", "H_nuclei_density"] * 1.171375267970105 #EAGLE doesn't contain electron number density, taking average value
        return nenhdV

ds.add_field(
        name=("gascuts", "emission_measure"),
        function=_emission_measure,
        sampling_type="local",
        units="cm**(-3)",
    )






radius=1500

def process_galaxy(i):
    ad = ds.sphere([xpos_dict[i]*0.6777,ypos_dict[i]*0.6777,zpos_dict[i]*0.6777],(radius, "kpc"))

    #ACCOUNT FOR PERIODIC BOUNDARIES-ADJUST COORDINATES
    sphere_center = ds.arr([xpos_dict[i]*0.6777,ypos_dict[i]*0.6777,zpos_dict[i]*0.6777],"code_length")
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
            f"/Volumes/easystore/RAFIKI_CGM_mock_library/EAGLE/snap_z0_1/X-ray/particles/galaxy_{i}.h5",
            data=data
        )



if __name__ == '__main__':
    with ProcessPoolExecutor(8) as executor:
        executor.map(process_galaxy, galaxy_sample_ids)