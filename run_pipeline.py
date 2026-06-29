import yaml
import argparse
from rafiki.pipeline import run_sz, run_xray 

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    if any([config['analysis']['sz_radial_profiles'],
            config['analysis']['sz_moment_profiles'],
            config['analysis']['sz_stacked_image'],
            config['analysis']['thermal_energy']]):
        run_sz(config)
    
    if any([config['analysis']['xray_profiles'],config['analysis']['xray_stacked_image']]):
        run_xray(config)

if __name__ == '__main__':
    main()