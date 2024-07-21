"""
Helper module for Butler library
"""

from sys import maxsize
from sys import platform as getplatform
from os.path import abspath, isdir
from os import makedirs, remove
from zipfile import ZipFile
from .exceptions import IncompatiblePlatform
import requests, logging
from re import findall


def get_latest_version(
    installlocation: str, platform: str = None, head: str = False) -> str:
    """
    Downloads the latest version of Butler from https://broth.itch.zone/butler and extracts to `installlocation`. 
    If successful, returns full executable path as string.
    
    Parameters:
    - `installlocation`: Directory location where butler will be extracted to. Required.
    - `platform`: Platform to download butler for. Attempts to detect host platform if unspecified.
    - `head`: If `True`, downloads bleeding edge version of butler. Default `False`.
    
    NOTE: When specifying `platform`, use platform names listed on broth. Do NOT use the platforms suffixed with `-head`. Use `head` parameter instead.
    
    Exceptions:
    - `IncompatiblePlatform`: Raised when an invalid platform is specified or detected.
    - `HTTPError`, `ConnectionError` or any exception defined under `requests.exceptions`: Raised when Butler is unable to be downloaded.
    - `OSError`: Raised when the downloaded ZIP file is unable to be written to disk.
    - `BadZipFile`: Raised when the downloaded ZIP file containing Butler is corrupted. Try again. 
    """
    CompatiblePlatforms = [
        "windows-386",
        "windows-amd64",
        "darwin-amd64",
        "linux-386",
        "linux-amd64",
    ]
    if not platform:
        logging.info('Platform not provided. Attempting to detect platform...')
        
        sysplatform = getplatform
        if sysplatform in ('linux', 'linux2'):
            sysplatform = 'linux'
            executable = 'butler'
        elif sysplatform == 'darwin':
            # No need to modify sysplatform again.
            executable = 'butler'
        elif sysplatform in ('win32', 'cygwin', 'msys'):
            sysplatform = 'windows'
            executable = 'butler.exe'
        else:
            raise IncompatiblePlatform(
                f"sys.platform returned a platform ({platform}) that isn't compatible with Butler. Specify platform to override."
            )
        if maxsize > 2**32:
            platform = f"{sysplatform}-amd64"
        else:
            platform = f"{sysplatform}-386"
        logging.info(f'Detected platform as "{platform}".')
    else:
        if platform not in CompatiblePlatforms:
            raise IncompatiblePlatform(
                f"Specified platform ({platform}) isn't compatible with Butler, or invalid platform was given."
            )
        if head:
            platform = f"{platform}-head"
    
    DownloadEndpoint = (
        f"https://broth.itch.zone/butler/{platform}/LATEST/archive/default"
    )

    logging.debug(f"Downloading Butler from {DownloadEndpoint}...")
    
    download = requests.get(DownloadEndpoint, timeout=10)
    download.raise_for_status()

    installlocation = abspath(installlocation)
    if not isdir(installlocation):
        makedirs(installlocation, exist_ok=True)
    
    zipfilename = findall("filename=(.+)", download.headers['content-disposition'])[0].replace('"', '')
    downloadlocation = f'{installlocation}\\{zipfilename}'
    
    logging.debug(f'Writing downloaded ZIP file to {downloadlocation}')
    with open(downloadlocation, "wb") as file:
        file.write(download.content)

    logging.debug(f'Extracting ZIP file to {installlocation}')
    with ZipFile(downloadlocation, "r") as zip_ref:
        zip_ref.extractall(installlocation)
    
    logging.debug('Deleting ZIP file')
    try:
        remove(downloadlocation)
    except OSError:
        logging.warn('Error deleting butler ZIP file, Ignoring due to low severity.')
    

    return f'{installlocation}\\{executable}'