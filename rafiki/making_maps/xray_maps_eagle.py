import yt
import pyxsim
import soxs
import numpy as np
from yt.utilities.cosmology import Cosmology
import os
import csv
import eagleSqlTools as sql
from concurrent.futures import ProcessPoolExecutor

soxs.set_soxs_config("frgnd_spec_model", "halosat")
cosmo = Cosmology(hubble_constant=0.6774, omega_matter=0.3089, omega_lambda=0.6911)
#Load in relevant files
ds = yt.load('/Volumes/easystore/EAGLE/RefL0050N0752/snapshot_027_z000p101/snap_027_z000p101.0.hdf5')
output_directory = "/Volumes/easystore/RAFIKI_CGM_mock_library/EAGLE/snap_z0_1/X-ray/pyxsim/"


redshift = 0.1

exp=2000 #ks
scale_change = 1  #Set to 5.75 at low z, 1 at high z

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


galaxy_sample_ids = [] # big (following rebeca)
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
        nenhdV *= data["gascuts", "H_nuclei_density"] * 1.171375267970105 #supposed to be El_number_density but broken
        return nenhdV

ds.add_field(
        name=("gascuts", "filtered_emission_measure"),
        function=_emission_measure,
        sampling_type="local",
        units="cm**(-3)",
    )

#Various parameters to set

exp_time = (exp, "ks") 
area = (2100.0, "cm**2")  # collecting area
#radius = 200 #radius in kpc you want around each galaxy
#Make X-ray source model (thermal CIE) and xray fields
source_model = pyxsim.CIESourceModel("apec", 0.5, 2.0, 1000,Zmet =('cuts', 'metallicity'), temperature_field = ('gascuts', 'temperature'),emission_measure_field=("gascuts", "filtered_emission_measure"))
xray_fields = source_model.make_source_fields(ds, 0.5, 2.0)


def process_galaxy(i):
    #where i is the index of the galaxy we want to sample
    radius=1500
    ad = ds.sphere([xpos_dict[i]*0.6777,ypos_dict[i]*0.6777,zpos_dict[i]*0.6777],(radius, "kpc"))
    with open(output_directory+'galaxy_sample_properties.csv','a', newline = '') as f: 
        w = csv.writer(f)
        c = w.writerow([i,stellar_mass_dict[i],halo_mass_dict[i],ages_dict[i],sfr_dict[i]])
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

if __name__ == '__main__':
    with ProcessPoolExecutor(8) as executor:
        executor.map(process_galaxy, galaxy_sample_ids)


