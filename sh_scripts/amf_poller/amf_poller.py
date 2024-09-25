import re
import subprocess
import os
import time
import datetime
import logging
import sched
import csv

from enum import Enum

def logger_setup():
#log configs
    bashCommand="mkdir -p ./logs_amf_poller"
    os.system(bashCommand)
    fileName="./logs_amf_poller/logs-"+str(datetime.datetime.now())+".log"
    logging.basicConfig(filename=fileName, level=logging.INFO, force=True)
    logging.FileHandler(filename=fileName, mode='a',encoding=None,delay=False)
    logger = logging.getLogger("__script___")
    logger.setLevel(logging.INFO)
    logger.info("####"+str(datetime.datetime.now())+"#####")

    return logger

def csv_writer_setup():
    #csv
    bashCommand="mkdir -p ./csv_amf_poller"
    os.system(bashCommand)
    fileName = "./csv_amf_poller/csv_amf_poller-"+str(datetime.datetime.now())+".csv"
    csvTimeFile = open(fileName, 'w+', newline='')
    csvWriter = csv.writer(csvTimeFile, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
    
    return csvWriter

# Define the State enumeration
class State(Enum):
    REGISTERED = 'REGISTERED'
    REG_INITIATED = 'REG-INITIATED'
    DEREGISTERED = 'DEREGISTERED'

# Function to convert a string to a State enumeration
def string_to_state(state_string):
    if state_string == '5GMM-REGISTERED':
        return State.REGISTERED
    elif state_string == '5GMM-REG-INITIATED':
        return State.REG_INITIATED
    elif state_string == '5GMM-DEREGISTERED':
        return State.DEREGISTERED
    else:
        raise ValueError('Invalid state string')

# Modify the AmfUe class
class AmfUe:
    def __init__(self, ue_info):
        self.index = int(ue_info['Index'])
        self.gmm_state = string_to_state(ue_info['5GMM State'])
        self.imsi = int(ue_info['IMSI'])
        self.guti = ue_info['GUTI']
        self.ran_ue_ngap_id = int(ue_info['RAN UE NGAP ID'])
        self.amf_ue_id = int(ue_info['AMF UE ID'])
        self.plmn = ue_info['PLMN']
        self.cell_id = ue_info['Cell ID']

    def get_index(self):
        return self.index

    def get_gmm_state(self):
        return self.gmm_state

    def get_imsi(self):
        return self.imsi

    def get_guti(self):
        return self.guti

    def get_ran_ue_ngap_id(self):
        return self.ran_ue_ngap_id

    def get_amf_ue_id(self):
        return self.amf_ue_id

    def get_plmn(self):
        return self.plmn

    def get_cell_id(self):
        return self.cell_id

    def __str__(self):
        return (f"Index: {self.index}, "
        f"5GMM State: {self.gmm_state.value}, "
        f"IMSI: {self.imsi}, "
        f"GUTI: {self.guti}, "
        f"RAN UE NGAP ID: {self.ran_ue_ngap_id}, "
        f"AMF UE ID: {self.amf_ue_id}, "
        f"PLMN: {self.plmn}, "
        f"Cell ID: {self.cell_id}")
    
def total_registration_messages(log_string):
    return log_string.count('Response body {"cause":255}')

def extract_logs_after_last_ue_info(logs):
    # Split the logs into lines
    lines = logs.split('\n')

    # Find the index of the last occurrence of the UEs' information line
    last_ue_info_index = None
    for i in range(len(lines) - 1, -1, -1):
        if "|----------------------------------------------------UEs' information------------------------------------------------|" in lines[i]:
            last_ue_info_index = i
            break

    # Check if the line was found
    if last_ue_info_index is not None:
        # Return the lines after the last UEs' information line
        return '\n'.join(lines[last_ue_info_index + 1:])
    else:
        # Return an empty string if the line was not found
        return ''

def total_registered_messages(log_string):
    return log_string.count('Response body {"cause":255}')

def parse_logs(logs):
    logs=extract_logs_after_last_ue_info(logs)
    # Define the pattern to match each line of the UEs' information
    pattern = r'\|\s*(\d+)\s*\|\s*([\w-]+)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+),\s*(\d+)\s*\|\s*(0x\s*[a-fA-F0-9]+)\|'

    # Find all matches in the logs
    matches = re.findall(pattern, logs)

    # Create a list to hold the parsed data
    parsed_data = []

    # Iterate over the matches and create a dictionary for each entry
    for match in matches:
        entry = {
        'Index': int(match[0]),
        '5GMM State': match[1],
        'IMSI': match[2],
        'GUTI': match[3].strip() if match[3].strip() else None,
        'RAN UE NGAP ID': int(match[4]),
        'AMF UE ID': int(match[5]),
        'PLMN': f"{match[6]}, {match[7]}",
        'Cell ID': match[8]
        }
        parsed_data.append(entry)

    # Return the list of dictionaries
    return parsed_data

def poll_amf():

    bashCommand="docker logs rfsim5g-oai-amf"
    output=subprocess.run(['docker','logs','rfsim5g-oai-amf'],stdout=subprocess.PIPE,stderr = subprocess.DEVNULL)
    logs=output.stdout.decode("utf-8")
    logs=str(logs)

    if "No such container" in logs:
        return []
    
    registrationMsgs=total_registration_messages(logs)
    parsedLogs=parse_logs(logs)

    return registrationMsgs, parsedLogs

def get_amf_ues_list():

    registrationMsgs,entries=poll_amf()
    amfUes=[]

    for entry in entries:
        ue=AmfUe(entry)
        amfUes.append(ue)

    return registrationMsgs,amfUes

def get_running_ue_containers():
    """get_running_UEs() is a function that returns the current number of deployed UEs

    /return             int     Number of UEs currently running
    """
    bashCommand="docker compose ps --services --status running"
    output=subprocess.run(['docker','compose','ps','--services','--status','running'],stdout=subprocess.PIPE)
    services=output.stdout.decode("utf-8")
    services=str(services)
    services=services.split("\n")

    #RUNNING_UES=0
    ueServices = [x for x in services if "oai-nr-ue" in x]
    #for service in services:
        #if "oai-nr-ue" in service:
            #RUNNING_UES=RUNNING_UES+1

    return len(ueServices)

def are_not_registered_ues(indexes):
    
    registrationMsgs,amfUes = get_amf_ues_list()

    for amfUe in amfUes:
        index=amfUe.get_index()
        state=amfUe.get_gmm_state()

        if index in indexes and state == State.REGISTERED:
            indexes.remove(index)
            
    return indexes

def printing_loop():
    scheduler.enter(0.9998,1,printing_loop)

    logger=logger_setup()
    #while True:

    registrationMsgs,amfUes = get_amf_ues_list()

    amfUesRegistered = [x for x in amfUes if x.get_gmm_state() == State.REGISTERED]
    amfUesRegInitiated = [x for x in amfUes if x.get_gmm_state() == State.REG_INITIATED]
    amfUesDeregistered = [x for x in amfUes if x.get_gmm_state() == State.DEREGISTERED]

    now=time.time() - TIME_ZERO
    runningUeContainers = get_running_ue_containers()
    print("\n"+str(now)+":\n")
    print("RUNNING UE CONTS: "+str(runningUeContainers))
    print("total RegMSGs: "+str(registrationMsgs))
    print("REGISTERED: "+str(len(amfUesRegistered))+"\nREG_INITIATED: "+str(len(amfUesRegInitiated))+
        "\nDEREGISTERED: "+str(len(amfUesDeregistered)))
    logger.info("REGISTERED: "+str(len(amfUesRegistered))+"\nREG_INITIATED: "+str(len(amfUesRegInitiated))+
        "\nDEREGISTERED: "+str(len(amfUesDeregistered)))
    csvWriter.writerow([str(now),
                        str(runningUeContainers),
                        str(registrationMsgs),
                        str(len(amfUesRegistered)),
                        str(len(amfUesRegInitiated)),
                        str(len(amfUesDeregistered))])

        #time.sleep(0.6)

TIME_ZERO = time.time()
global scheduler
scheduler = sched.scheduler(time.time, time.sleep)

global csvWriter
csvWriter = csv_writer_setup()
csvWriter.writerow(['deltaT','RUNNING UE CONTAINERS','tot REGISTRATION MSGS','REGISTERED UEs','REG-INITIATED UEs','DEREGISTERED UEs'])

scheduler.enter(1,1,printing_loop)
scheduler.run()
