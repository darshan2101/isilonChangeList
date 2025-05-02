from pprint import pprint
import os
import requests
import json
import urllib3
import platform
import time
import sys
import time    
import argparse
from configparser import ConfigParser
import plistlib

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Supresses the self signed cert warning

ISILON_CLUSTER_IP = "IsilonClusterIP"
ISILON_CLUSTER_PORT = "IsilonClusterPort"
ISILON_USERNAME = "IsilonUsername"
ISILON_PASSWORD = "IsilonPassword"

def checkerrors(response):

    if 'errors' in response.json():

        for err in response.json()['errors']:

            print("%s: %s" % (err['code'], err['message']))

        sys.exit(0)

def get_isilon_config_dictionary():

    is_linux=0
    if platform.system() == "Linux":
        DNA_CLIENT_SERVICES = '/etc/StorageDNA/DNAClientServices.conf'
        is_linux=1
    elif platform.system() == "Darwin":
        DNA_CLIENT_SERVICES = '/Library/Preferences/com.storagedna.DNAClientServices.plist'

    config_dictionary = {}

    if is_linux == 1:
        config_parser = ConfigParser()
        config_parser.read(DNA_CLIENT_SERVICES)
        if config_parser.has_section('General'):
            section_info = config_parser['General']
            if config_parser.has_option('General',ISILON_CLUSTER_IP):
                config_dictionary[ISILON_CLUSTER_IP] = section_info[ISILON_CLUSTER_IP]
            if config_parser.has_option('General',ISILON_CLUSTER_PORT):
                config_dictionary[ISILON_CLUSTER_PORT] = section_info[ISILON_CLUSTER_PORT]
            if config_parser.has_option('General',ISILON_USERNAME):
                config_dictionary[ISILON_USERNAME] = section_info[ISILON_USERNAME]
            if config_parser.has_option('General', ISILON_PASSWORD):
                config_dictionary[ISILON_PASSWORD] = section_info[ISILON_PASSWORD]
 
    else:
        with open(DNA_CLIENT_SERVICES, 'rb') as fp:
            my_plist = plistlib.load(fp)
            config_dictionary[ISILON_CLUSTER_IP] = my_plist[ISILON_CLUSTER_IP]
            config_dictionary[ISILON_CLUSTER_PORT] = my_plist[ISILON_CLUSTER_PORT]
            config_dictionary[ISILON_USERNAME] = my_plist[ISILON_USERNAME]
            config_dictionary[ISILON_PASSWORD] = my_plist[ISILON_PASSWORD]

    if len(config_dictionary[ISILON_CLUSTER_IP]) == 0 or len(config_dictionary[ISILON_CLUSTER_PORT]) == 0 or len(config_dictionary[ISILON_USERNAME]) == 0 or len(config_dictionary[ISILON_PASSWORD]) == 0:
        print("Missing isilon settings, please check DNAClientServices for " + " " + ISILON_CLUSTER_IP + " " + ISILON_CLUSTER_PORT + " " + ISILON_USERNAME + " " + ISILON_PASSWORD)
        sys.exit(23)

    return config_dictionary

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--projectname', required = True, help = 'Project we are performing scan for.')
    parser.add_argument('-s', '--isilonsourcepath', required = True, help = 'Source path to scan')
    args = parser.parse_args()

    config_dict = get_isilon_config_dictionary()

    uri = "https://%s:%s" % (config_dict[ISILON_CLUSTER_IP], config_dict[ISILON_CLUSTER_PORT])
    papi = uri + '/platform'
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'username': config_dict[ISILON_USERNAME], 'password': config_dict[ISILON_PASSWORD], 'services': ['platform']})

    session = requests.Session()
    response = session.post(uri + "/session/1/session", data=data, headers=headers, verify=False)
    session.headers['referer'] = uri
    session.headers['X-CSRF-Token'] = session.cookies.get('isicsrf')

    epoch_time = int(time.time())
    new_snapshot_name = args.projectname + "-" + str(epoch_time)

   ### Get Jobs List
#    new_snapshot_name="DanSnapshotXYZ_15"
    new_snapshot_path = args.isilonsourcepath

    snapshot_endpoint = papi + '/11/snapshot/snapshots'
    # Now create the new snapshot
    create_data = json.dumps({"name":new_snapshot_name,"path":new_snapshot_path})
    response = session.post(snapshot_endpoint, data=create_data, headers=headers, verify=False)

    if response.status_code != 201:
        print("Snapshot generation failed: " + response.reason)
        exit(1)
    
    json_response = response.json()
    new_snapshot_id = json_response["id"]

    print(new_snapshot_id)
    exit(0)

