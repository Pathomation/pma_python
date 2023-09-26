import os, warnings
warnings.simplefilter('ignore')
from pma_python import *


def scenario1(url, username, password, verify):
    print("Session ID: ", connect(url, username, password, verify))


def scenario2(url):
    print(f'PMA.core.lite: {is_lite(url)}')


def scenario3(url, verify):
    print(f'\npmaviewURL version: {get_version_info(url)}')
    print(f'PMA.core API version: {get_api_version(url, verify)}')
    print(f'Built revision: {get_build_revision(url, verify)}')


def scenario4(parent_dir, sub_dir, session_id, recursive, verify):
    print(f'\nRoot directories: {get_root_directories(session_id, verify)}\n')
    print(f'Sub-directories: {get_directories(parent_dir, session_id, recursive, verify)}\n')
    print(f'Available slides: {get_slides(sub_dir, session_id, recursive, verify)}')

    
def scenario5(slide, session_id, verify):
    print(f'\nSlide "{os.path.basename(os.path.normpath(slide))}" info: {get_slide_info(slide, session_id, verify)}\n')
    print(f'Slide "{os.path.basename(os.path.normpath(slide))}" UID: {get_uid(slide, session_id, verify)}\n')
    print(f'Slide "{os.path.basename(os.path.normpath(slide))}" fingerprint: {get_fingerprint(slide, session_id, verify)}\n')
    print(f'Slide "{os.path.basename(os.path.normpath(slide))}" barcode: {get_barcode_text(slide, session_id, verify)}')


def main():
    try:
        url = str(input("\nEnter the PMA.core URL: "))
        username = str(input("\nUsername: "))
        password = str(input("\nPassword: "))    

        scenario_num = int(input("\nEnter the scenario number: "))
        
        if scenario_num == 1:
            # 1. Connect to PMA.core instance
            scenario1(url=url, username=username, password=password, verify=False)
        elif scenario_num == 2:
            # 2. Check if PMA.core.lite (server component of PMA.start)
            scenario2(url=url)
        elif scenario_num == 3:
            # 3a. Check the 'pmaviewURL' version 
            # 3b. Check the API version exposed by the underlying PMA.core
            # 3c. Get build revision from PMA.core instance running at pmacoreURL
            scenario3(url=url, verify=False)
        elif scenario_num == 4:
            # 4a. Return an array of root-directories available to sessionID
            # 4b. Return an array of sub-directories available to sessionID in the startDir directory
            # 4c. Return an array of slides available to sessionID in the startDir directory
            parent_dir = str(input("\nEnter the parent directory: "))
            sub_dir = str(input("\nEnter the sub-directory: "))
            scenario4(parent_dir=parent_dir, sub_dir=sub_dir,                      
                      session_id=connect(url, username, password, False), 
                      recursive=False, verify=False)
        elif scenario_num == 5:
            # 5a. Return raw image information in the form of nested dictionaries
            # 5b. Get the UID for a specific slide
            # 5c. Get the fingerprint for a specific slide
            # 5d. Get the text encoded by the barcode (if there IS a barcode on the slide to begin with)
            sub_dir = str(input("\nEnter the sub-directory: "))
            selected_slide = get_slides(sub_dir, connect(url, username, password, False), False, False)[0]
            scenario5(slide=selected_slide, session_id=connect(url, username, password, False), verify=False)
        else:
            raise ValueError("Invalid input. Please enter a value [1-5]")    
    except Exception as e:
        print(f'Error: {str(e)}')
        print(f'URL or wrong information (credentials, directories)')


if __name__ == '__main__':
    main()
    