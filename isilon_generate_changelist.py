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

def escape( str ):
    str = str.replace("&", "&amp;")
    str = str.replace("<", "&lt;")
    str = str.replace(">", "&gt;")
    str = str.replace("\"", "&quot;")
    return str

def write_xml_result(xml_filename, index,  deletes_on,  results):
    total_size=0
    total_count=0
    delete_count=0

    try:
        xml_file = open(xml_filename, "w") 
    except OSError:
        print("Could not open/read file:" + xml_filename)
        sys.exit(4)

    for entry in results:
	
        if entry['file_type'] == 'regular':
            if entry['change_types'][0] == 'ENTRY_ADDED' or entry['change_types'][0] == 'ENTRY_MODIFIED':
                total_size = total_size +  entry['size']
                total_count = total_count + 1
        elif deletes_on == True and entry['change_types'][0] == 'ENTRY_REMOVED':
            delete_count = delete_count + 1
        
    xml_file.write("<files scanned=\"" + str(total_count) + "\" selected=\"" + str(total_count) + "\" size=\"" + str(total_size) + "\" bad_dir_count=\"0\" delete_count=\"" + str(delete_count) + "\">\n");
    
    for entry in results:

        if entry['file_type'] == 'regular':
            if entry['change_types'][0] == 'ENTRY_ADDED' or entry['change_types'][0] == 'ENTRY_MODIFIED':
                 xml_file.write("    <file name=\"" + escape(entry['path']) + "\" size=\"" + str(entry['size'])  + "\" mode=\"0x777\"  type=\"F_REG\" mtime=\"" + str(entry['mtime']['sec']) + "\" atime=\"" + str(entry['atime']['sec']) + "\" owner=\"" + str(entry['uid']) + "\" group=\"" + str(entry['gid']) + "\" index=\"" + str(index) + "\"/>\n")
            
        elif entry['change_types'][0] == 'ENTRY_REMOVED':
            xml_file.write("    <delete-file name=\"" + escape(entry['path']) + "\" size=\"" + str(entry['size']) + "\" mode=\"0x777\"  type=\"F_REG\" mtime=\"" + str(entry['mtime']['sec']) + "\" atime=\"" + str(entry['atime']['sec']) + "\" owner=\"" + str(entry['uid']) + "\" group=\"" + str(entry['gid']) + "\" index=\"" + str(index) + "\"/>\n")

    xml_file.write("</files>")
    xml_file.close()

def getChangeList(cid):

    endpoint = '/1/snapshot/changelists'
    response = session.get(papi + endpoint, data=data, headers=headers, verify=False)
    checkerrors(response)

    for changelist in response.json()['changelists']:
        if changelist['id'] == cid:
            return(changelist)

    return(None)

def runChangeListCreate():

    running = True
    while running == True:
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(5)
        response = session.get(papi + endpoint, data=data, headers=headers, verify=False)
        checkerrors(response)

        job_response = response.json()['jobs'][0]
        if ( job_response['state'] == 'succeeded' ):
            running = False

        elif job_response in error_states:
            print(job_response)
            sys.exit(1)


error_states =  [ "paused_user",
                  "paused_system",
                  "paused_policy",
                  "paused_priority",
                  "cancelled_user",
                  "cancelled_system",
                  "failed",
                  "failed_not_retried",
                 "unknown" ]

possible_states =  [ "running",
                  "paused_user",
                  "paused_system",
                  "paused_policy",
                  "paused_priority",
                  "cancelled_user",
                  "cancelled_system",
                  "failed",
                  "succeeded",
                  "failed_not_retried",
                  "unknown" ]


def get_scan_folder_output_folder(project_name, project_guid):

    is_linux=0
    if platform.system() == "Linux":
        DNA_CLIENT_SERVICES = '/etc/StorageDNA/DNAClientServices.conf'
        is_linux=1
    elif platform.system() == "Darwin":
        DNA_CLIENT_SERVICES = '/Library/Preferences/com.storagedna.DNAClientServices.plist'

    fastScanWorkFolder = ""

    if is_linux == 1:
        config_parser = ConfigParser()
        config_parser.read(DNA_CLIENT_SERVICES)
        if config_parser.has_section('General') and config_parser.has_option('General','FastScanWorkFolder'):
            section_info = config_parser['General']
            fastScanWorkFolder = section_info['FastScanWorkFolder']
    else:
        with open(DNA_CLIENT_SERVICES, 'rb') as fp:
            my_plist = plistlib.load(fp)
            fastScanWorkFolder  = my_plist["FastScanWorkFolder"]
    
    if (len(fastScanWorkFolder) == 0):
        fastScanWorkFolder = "/tmp"
     
    fastScanWorkFile = fastScanWorkFolder + '/sdna-scan-files/' + project_guid
    return fastScanWorkFile


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
    parser.add_argument('-g', '--projectguid', required = True, help = 'Project guid we are performing scan for.')
    parser.add_argument('-i', '--sourceindex', required = True, help = 'Numeric index of source folders')
    parser.add_argument('--prevsnapshotid', required = True, help = 'Required prev snapshot')
    parser.add_argument('--newsnapshotid', required = True, help = 'Required new snapshot')
    parser.add_argument('-d', '--deletes', help = 'Use mirror deletes', action='store_true')

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

    output_folder = get_scan_folder_output_folder(args.projectname, args.projectguid)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    if not os.path.isdir(output_folder):
        pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
        print("Unable to create output folder")
        exit(4)

    prev_snapshot_id = int(args.prevsnapshotid)
    new_snapshot_id = int(args.newsnapshotid)

    endpoint = '/3/job/jobs'
    data = json.dumps({"type":"changelistcreate","changelistcreate_params":{"newer_snapid":new_snapshot_id,"older_snapid":prev_snapshot_id}})
    response = session.post(papi + endpoint, data=data, headers=headers, verify=False)

    checkerrors(response)

    ### Get Job ID
    jobid = response.json()['id']
    ### Set endpoint for the jobid
    endpoint = '/3/job/jobs/'+str(jobid)

    ### Get Changelist by id function
    cid = str(prev_snapshot_id) + '_' + str(new_snapshot_id)
    cl = getChangeList(cid)

    ### Create Changelist Function
    ### Run Changelist Job

    if not cl:
        runChangeListCreate()

    cl = getChangeList(cid)

    if not cl:
        print("Error creating changelist")
        sys.exit(1)

    ### Get list of changelist entries

    endpoint = "/8/snapshot/changelists/%s/entries" % cl['id']
    response = session.get(papi + endpoint, data=data, headers=headers, verify=False)
    checkerrors(response)

    results = response.json()
    results = results['entries']

    output_file = output_folder + "/" + str(args.sourceindex) + "-files.xml"
    print(output_file)
    write_xml_result(output_file, args.sourceindex,  args.deletes, results)
    exit(0)

