import numpy as np
from astropy.io import fits
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u
from random import randint
from scipy.stats import bootstrap
from scipy.stats import bootstrap
import h5py
import soxs
import os
import glob
from .catalog import load_catalog
from importlib.resources import files


#USE TO BUILD AND REGISTER CUSTOM SOXS INSTRUMENTS IF DESIRED

def make_erosita():
    instrument_dir = files("rafiki.data.erosita")

    soxs.set_soxs_config("soxs_data_dir", str(instrument_dir))

    rmf_file = instrument_dir / "sixte_erormf_normalized_singles_20170725.rmf"
    bkg_file = instrument_dir / "particle_bkg_eFEDS_V2_20210607.pha"

    for tm in range(1, 8):
        arf_file = instrument_dir / f"tm{tm}_arf_filter_000101v02.fits"
        psf_file = instrument_dir / f"tm{tm}_2dpsf_190219v05.fits"

        inst = {
            "name": f"erosita{tm}",
            "arf": str(arf_file),
            "rmf": str(rmf_file),
            "bkgnd": [str(bkg_file), 1.0],
            "num_pixels": 384,
            "fov": 61.8,
            "aimpt_coords": [0.0, 0.0],
            "chips": [["Box", 0, 0, 384, 384]],
            "focal_length": 1.6,
            "dither": False,
            "psf": ["multi_image", str(psf_file)],
            "imaging": True,
            "grating": False,
        }

        if inst["name"] not in soxs.instrument_registry:
            soxs.add_instrument_to_registry(inst)

