# ******** !!!!!!!! *****
#autodeploy-v4.01.py does not change configuration files
#You must have in the working directory docker-compose.yaml and oai_db.yaml
#previously generated with config_files_generator.py
#
#There shall be present ./ues_planv3.txt file in the working directory with a valid deployment plan
#
#Make sure that every container is down before executing this script
#
#2024-07-04 by Gabriele Nunziati

import logging
import datetime
import sys
import os
import time
import csv
import sched
import subprocess
from enum import Enum

class DeploType(Enum):
        DEPLOY = 'DEPLOY'
        UNDEPLOY = 'UNDEPLOY'

def string_to_type(type_string):
    if type_string == 'D':
        return DeploType.DEPLOY
    elif type_string == 'U':
        return DeploType.UNDEPLOY
    else:
        raise ValueError('Invalid type string')

class Event():
    def __init__(self,type,time,indexes):
        self.type=string_to_type(type)
        self.time=time
        self.indexes= [int(numeric_string) for numeric_string in indexes]
    def __str__(self):
        res=str(self.type)+"-"+str(self.time)+"-"+str(self.indexes)
        res=str(res)
        return res
    def __repr__(self):
        res=str(self.type)+"-"+str(self.time)+"-"+str(self.indexes)
        res=str(res)
        return res
    def getIndexes(self):
        return self.indexes
    def getTime(self):
        return self.time
    def getType(self):
        return self.type

############# FUNCTIONS ############

def create_seid_mapping_file():
    global seid_map_filename

    with open(seid_map_filename, "w") as file:
        pass

def append_to_seid_mappings_file(integer1):
    global expected_seid  # Declare that we are using the global variable
    global seid_map_filename

    with open(seid_map_filename, "a") as file:
        file.write(f"{expected_seid}\t{integer1}\n")
        print("Appending ue" + str(integer1) + " seid " + str(expected_seid))

    expected_seid = expected_seid + 1

def get_running_ue_containers():
    bashCommand="docker compose ps --services --status running"
    output=subprocess.run(['docker','compose','ps','--services','--status','running'],stdout=subprocess.PIPE)
    services=output.stdout.decode("utf-8")
    services=str(services)
    services=services.split("\n")
    print(services)

    RUNNING_UES=0
    for service in services:
        if "oai-nr-ue" in service:
            RUNNING_UES=RUNNING_UES+1

    return RUNNING_UES

def parse_ues_plan_file(name="./ues_planv4.txt"):

    try:
        planFileopen=open(name,'r')
    except IOError:
        print("Missing UEs plan file at "+name+" . Exiting.")
        sys.exit(-1)

    lines=planFileopen.readlines()

    #leggi la prima riga, di che quello è uesCounter, e mettici un # così la ignora
    firstLine=lines[0]
    try:
        uesCounter=int(firstLine)
        lines[0]="#"
    except:
        raise TypeError("The first line must be the TOTAL number of UEs you want to deploy.")

    events = []
    for line in lines:
        if "#" in line:
            continue
        elif "+" not in line:
            continue
        elif "\t" not in line:
            continue

        array=line.split("\t")

        if len(array) != 3:
            continue

        type=array[0]
        time=float(array[1])
        indexes=array[2]

        indexes=indexes.split(",")
        for index in indexes:
            index=int(index)

        event=Event(type,time,indexes)
        events.append(event)

    print(event)
    print(str(events))

    return uesCounter, events

def logger_setup():
#log configs
    bashCommand="mkdir -p ./logs_autodeploy"
    os.system(bashCommand)
    fileName="./logs_autodeploy/logs-"+str(datetime.datetime.now())+".log"
    logging.basicConfig(filename=fileName, level=logging.INFO, force=True)
    logging.FileHandler(filename=fileName, mode='a',encoding=None,delay=False)
    logger = logging.getLogger("__script___")
    logger.setLevel(logging.INFO)
    logger.info("####"+str(datetime.datetime.now())+"#####")

    return logger

def csv_writer_setup():
    #csv
    bashCommand="mkdir -p ./csv_time"
    os.system(bashCommand)
    fileName = "./csv_time/+csvtimes-"+str(datetime.datetime.now())+".csv"
    csvTimeFile = open(fileName, 'w+', newline='')
    csvWriter = csv.writer(csvTimeFile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)

    return csvWriter

def deploy_many_ues(indexes):

    currentRunningUEs=get_running_ue_containers()

    #creating bash command
    bashCommand="docker compose up -d "
    for index in indexes:
        bashCommand=bashCommand+"oai-nr-ue"+str(index)+" "

    os.system(bashCommand)

    csvWriter.writerow(['UE'+str(indexes)+' start time',str(datetime.datetime.now())])
    logger.info("!!! UE"+str(indexes)+" started at: "+str(datetime.datetime.now())+"\n")

    for i in indexes:
        append_to_seid_mappings_file(i)

    if currentRunningUEs+len(indexes) != get_running_ue_containers():
        raise IndexError("SOME CONTAINERS WERE NO DEPLOYED")
    else:
        return True

def undeploy_many_ues(indexes):

    currentRunningUEs=get_running_ue_containers()

    #creating bash command
    bashCommand="docker compose down "
    for index in indexes:
        bashCommand=bashCommand+"oai-nr-ue"+str(index)+" "

    os.system(bashCommand)

    csvWriter.writerow(['UE'+str(indexes)+' stop time',str(datetime.datetime.now())])
    logger.info("!!! UE"+str(indexes)+" stop at: "+str(datetime.datetime.now())+"\n")

    if currentRunningUEs-len(indexes) != get_running_ue_containers():
        return False#raise IndexError("SOME CONTAINERS WERE NOt UNDEPLOYED")
    else:
        return True


def deploy_UE(i):
    currentRunningUEs=get_running_ue_containers()

    print("Deploying the nr-ue"+str(i)+"\n")
    bashCommand="docker compose up -d oai-nr-ue"+str(i)
    os.system(bashCommand)

    csvWriter.writerow(['UE'+str(i)+' start time',str(datetime.datetime.now())])
    logger.info("!!! UE"+str(i)+" started at: "+str(datetime.datetime.now())+"\n")

    append_to_seid_mappings_file(i)

    if get_running_ue_containers() != (currentRunningUEs+1):
        return -1
    else:
        return 0

def undeploy_UE(i):
    currentRunningUEs=get_running_ue_containers()

    print("UNdeploying the nr-ue"+str(i)+"\n")
    bashCommand="docker compose down oai-nr-ue"+str(i)
    os.system(bashCommand)

    csvWriter.writerow(['UE'+str(i)+' stop time',str(datetime.datetime.now())])
    logger.info("!!! UE"+str(i)+" stopped at: "+str(datetime.datetime.now())+"\n")

    if get_running_ue_containers() != (currentRunningUEs-1):
        return -1
    else:
        return 0

def schedule_UE_events(events):

    for event in events:
        type=event.getType()
        time=event.getTime()
        indexes=event.getIndexes()

        time=time+TIMEZERO

        if type == DeploType.DEPLOY:
            #Deploy
            scheduler.enterabs(time,1,deploy_many_ues,argument=[indexes])
        elif type == DeploType.UNDEPLOY:
             #Undeploy
            scheduler.enterabs(time,1,undeploy_many_ues,argument=[indexes])

    scheduler.run()

def repeat_print_ues():
    currentTime=time.time()-TIMEZERO
    print("\nTIME="+str(currentTime)+" deployed_UEs="+str(get_running_ue_containers())+"\n")
    #scheduler.enter(2, 1, repeat_print_ues, ())


# Defining main function
def main():

    #Parsing the UEs plan file to get number of UEs and running periods
    MAX_UE, events = parse_ues_plan_file()

    global logger
    logger =logger_setup()

    global csvWriter
    csvWriter = csv_writer_setup()

    global seid_map_filename
    seid_map_filename = "seid_mappings.txt"

    global expected_seid
    expected_seid = 1

    #Setting up seid mapping file
    create_seid_mapping_file()

    print("***** autodeploy-v4.01 by Lele *****")
    print("UEs to deploy: "+str(MAX_UE))

    #try:
    #    MAX_UE = int(input("Enter the numer of UEs you want to generate:"))
    #    print("Number of UEs to generate (MAX IS 50!): "+str(MAX_UE))
    #except ValueError:
    #    print("Invalid input. Please enter an integer.")

    if (MAX_UE > 50):
        print("Too many UEs:"+MAX_UE+" . They shall be less than 51.")
        sys.exit(-2)

################# CONTAINERS DEPLOYMENT #######################

    #1. Mysql deployment
    bashCommand="docker compose up -d mysql"
    os.system(bashCommand)
    csvWriter.writerow(['mysql START TIME',str(datetime.datetime.now())])

    time.sleep(18)

    #2. AMF,SMF,UPF,EXT-DN deployment
    bashCommand="docker compose up -d oai-amf oai-smf oai-upf oai-ext-dn"
    os.system(bashCommand)
    csvWriter.writerow(['core NFs START TIME',str(datetime.datetime.now())])

    time.sleep(8)

    #3. gNB deployment
    bashCommand="docker compose up -d oai-gnb"
    os.system(bashCommand)

    csvWriter.writerow(['gnb START TIME',str(datetime.datetime.now())])
    logger.info("!!! gNB started at: "+str(datetime.datetime.now())+" <<<<<<<\n")

    time.sleep(10)

    global TIMEZERO
    TIMEZERO = time.time()

    #4. Scheduling UEs deployment/undeployment
    global scheduler

    scheduler = sched.scheduler(time.time, time.sleep)

    schedule_UE_events(events)


# Using the special variable
# __name__
if __name__=="__main__":
    main()
