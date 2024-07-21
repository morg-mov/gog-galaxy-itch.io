from zipfile import ZipFile
import requests, os, sys
from shutil import move, rmtree

def main(src_folder):
    print("Downloading GOG Galaxy API to source folder...")
    APIVERSIONENDPOINT = "https://api.github.com/repos/gogcom/galaxy-integrations-python-api/releases/latest"
    
    request = {}
    responses = {}

    print(f'Getting latest version of Galaxy API from Github...')
    request['initial'] = requests.get(APIVERSIONENDPOINT, timeout=5)
    responses['initial'] = request['initial'].json()

    print(f'Downloading Galaxy API...')
    request['galaxy_src_zipfile'] = requests.get(responses['initial']['zipball_url'], timeout=5)
    responses['galaxy_src_zipfile'] = request['galaxy_src_zipfile'].content

    print('Writing to ZIP file...')
    with open('./gog-galaxy-api.zip', 'wb') as f:
        f.write(responses['galaxy_src_zipfile'])
        ziplocation = os.path.abspath('./gog-galaxy-api.zip')
    
    print('Extracting ZIP file...')
    with ZipFile('./gog-galaxy-api.zip', 'r') as zip_ref:
        filename = zip_ref.namelist()[0]
        zip_ref.extractall('.')
        extractlocation = os.path.abspath(f'./{filename}')
    
    print(f'Moving API to {src_folder}...')
    os.chdir(f'{filename}\\src')
    move('./galaxy/', f'{src_folder}/galaxy/')

    print('Cleaning up...')
    os.chdir('..\\..')
    os.remove(ziplocation)
    rmtree(extractlocation)

    print("Done!")
    return True

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print('Usage: python readydev.py [source folder]')
        exit()
    else:
        src_folder = os.path.abspath(args[1])
        main(src_folder)
        