
import requests
from pathlib import Path

def download_data(config, remotepath):
    """
    Downloads the relevant data file from Cloudflare if it is not already saved

    :param config: input yaml file
    :type config: yaml  
    :param remotepath: path to file for download
    :type remotepath: string
    :return: path to downloaded file
    :rtype: string
    
    """
    remote_url = "https://pub-978f7726476c460383c469555c7b769d.r2.dev/v1"

    cache = config["package_data"]["path"]
    local_file = Path(cache+f"/{remotepath}")

    if local_file.exists():
        print("File already downloaded, proceeding with analysis.")
        return local_file
    
    local_file.parent.mkdir(parents=True, exist_ok=True)

    url = f"{remote_url}/{remotepath}"

    print(f"Downloading {remotepath}...")

    response = requests.get(url)
    response.raise_for_status()

    with open(local_file, "wb") as f:
        f.write(response.content)

    return local_file
    

