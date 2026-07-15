import yaml
import argparse
from .pipeline import run_sz, run_xray, select_galaxies 

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    run_sz_flag = any([
    config['analysis']['sz_radial_profiles'],
    config['analysis']['sz_moment_profiles'],
    config['analysis']['sz_stacked_image'],
    config['analysis']['thermal_energy'],
    ])

    run_xray_flag = any([
        config['analysis']['xray_profiles'],
        config['analysis']['xray_stacked_image'],
    ])

    # Only select once if anything needs it
    if run_sz_flag or run_xray_flag:
        gal_sample_indices, redshifts = select_galaxies(config)

    if run_sz_flag:
        run_sz(config, gal_sample_indices, redshifts)

    if run_xray_flag:
        run_xray(config, gal_sample_indices, redshifts)

if __name__ == '__main__':
    main()