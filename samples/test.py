import os, warnings
warnings.simplefilter('ignore')
from pma_python import *


def scenario1(pma_url, username, password, verify):
    print("Session ID: ", connect(pma_url, username, password, verify))

def scenario2(pma_url):
    print(f'PMA.core.lite: {is_lite(pma_url)}')

def scenario3(pma_url, verify):
    print(f'\npmaviewURL version: {get_version_info(pma_url)}')
    print(f'PMA.core API version: {get_api_version(pma_url, verify)}')
    print(f'Built revision: {get_build_revision(pma_url, verify)}')

def scenario4(parent_dir, sub_dir, session_id, recursive, verify):
    print(f'\nRoot directories: {get_root_directories(session_id, verify)}\n')
    print(f'Sub-directories: {get_directories(parent_dir, session_id, recursive, verify)}\n')
    print(f'Available slides: {get_slides(sub_dir, session_id, recursive, verify)}')
    
def scenario5(slide, session_id, verify):
    print(f'\nSlide "{os.path.basename(os.path.normpath(slide))}" info: {get_slide_info(slide, session_id, verify)}\n')
    print(f'Slide "{os.path.basename(os.path.normpath(slide))}" UID: {get_uid(slide, session_id, verify)}\n')
    print(f'Slide "{os.path.basename(os.path.normpath(slide))}" fingerprint: {get_fingerprint(slide, session_id, verify)}\n')
    print(f'Slide "{os.path.basename(os.path.normpath(slide))}" barcode: {get_barcode_text(slide, session_id, verify)}')


if __name__ == '__main__':
    url = "https://192.168.1.6/core/"
    _pmaCoreUrl = "http://localhost:54001/"

    scenario_num = int(input("\nEnter the scenario number: "))
    if scenario_num == 1:
        # 1. Connect to PMA.core instance
        scenario1(pma_url=url, username='pma_admin', password='P4th0-M4t!on', verify=False)
    elif scenario_num == 2:
        # 2. Check if PMA.core.lite (server component of PMA.start)
        scenario2(pma_url=url)
    elif scenario_num == 3:
        # 3a. Check the 'pmaviewURL' version 
        # 3b. Check the API version exposed by the underlying PMA.core
        # 3c. Get build revision from PMA.core instance running at pmacoreURL
        scenario3(pma_url=url, verify=False)
    elif scenario_num == 4:
        # 4a. Return an array of root-directories available to sessionID
        # 4b. Return an array of sub-directories available to sessionID in the startDir directory
        # 4c. Return an array of slides available to sessionID in the startDir directory
        scenario4(parent_dir='Local/hgx-svs-check', sub_dir='Local/hgx-svs-check/Original', 
                  session_id=connect(url, 'pma_admin', 'P4th0-M4t!on', False), 
                  recursive=False, verify=False)
    elif scenario_num == 5:
        # 5a. Return raw image information in the form of nested dictionaries
        # 5b. Get the UID for a specific slide
        # 5c. Get the fingerprint for a specific slide
        # 5d. Get the text encoded by the barcode (if there IS a barcode on the slide to begin with)
        selected_slide = get_slides('Local/hgx-svs-check/Original', connect(url, 'pma_admin', 'P4th0-M4t!on', False), False, False)[0]
        scenario5(slide=selected_slide, session_id=connect(url, 'pma_admin', 'P4th0-M4t!on', False), verify=False)
    else:
        raise ValueError("Invalid input. Please enter a value [1-5]")