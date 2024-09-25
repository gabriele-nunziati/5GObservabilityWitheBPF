#Configuration Files Generator
# 2024-04-24 - by Gabriele Nunziati
#
#Insert the maximum desired number of UEs in the deployment in the prompt
#
#INPUT FILES: ./docker-compose-original.yaml, oai_db-original.sql
#GENERATED FILES: ./docker-compose.yaml, oai_db.sql

import logging
import datetime
import sys
import os
import time
import csv
import sched
import subprocess

bashCommand="cp ./docker-compose-original.yaml ./docker-compose.yaml"
os.system(bashCommand)

bashCommand="cp ./oai_db-original.sql ./oai_db.sql"
os.system(bashCommand)

#log configs
bashCommand="mkdir -p ./logs_autodeploy"
os.system(bashCommand)
fileName="./logs_autodeploy/logs-"+str(datetime.datetime.now())+".log"
logging.basicConfig(filename=fileName, level=logging.INFO, force=True)
logging.FileHandler(filename=fileName, mode='a',encoding=None,delay=False)
logger = logging.getLogger("__script___")
logger.setLevel(logging.INFO)
logger.info("####"+str(datetime.datetime.now())+"#####")

#csv
bashCommand="mkdir -p ./csv_time"
os.system(bashCommand)
fileName = "./csv_time/+csvtimes-"+str(datetime.datetime.now())+".csv"
csvTimeFile = open(fileName, 'w+', newline='')
csvWriter = csv.writer(csvTimeFile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)

#1. Parameters
#Please note that BASE_MSIN must have a digit not equal to 0 as the first digit
MCC=208
MNC=99
BASE_MSIN=1000001000
FOURTH_GROUP_IP_BASE=141

#OPERATOR KEY MUST BE THE SAME AS THE ONE IN AMF SECTION
OPERATOR_KEY="c42449363bbad02b66d16bc975d77cc1"

print("***** UEs GENERATOR by Lele *****")
print("MCC="+str(MCC)+", MNC:"+str(MNC))

try:
    MAX_UE = int(input("Enter the numer of UEs you want to generate:"))
    print("Number of UEs to generate (MAX IS 50!): "+str(MAX_UE))
except ValueError:
    print("Invalid input. Please enter an integer.")

if (MAX_UE > 50):
    sys.exit(104)

#First line to append
APPEND_TO_DB="-- ***** UEs added by Lele script ******\n"
APPEND_TO_DOCKER=""

#Generating DB entry and docker-file-entry for each UE to deploy
for i in range(MAX_UE):
    logger.info("Creating the "+str(i)+" UE")
    IMSI=MCC*(pow(10,12))+MNC*(pow(10,10))+BASE_MSIN+i
    logger.info("IMSI:"+str(IMSI))


    #Assign .136 .137 .138 and .139
    if i == 0:
        FOURTH_GROUP_IP = 136
    elif i == 1:
        FOURTH_GROUP_IP = 137
    elif i == 2:
        FOURTH_GROUP_IP = 138
    elif i == 3:
        FOURTH_GROUP_IP = 139
    else:
    	FOURTH_GROUP_IP = FOURTH_GROUP_IP_BASE+i


    #Generating DB entry
    DB_ENTRY="INSERT INTO `users` VALUES ('"+str(IMSI)+"','1','55000000000000',NULL,'PURGED',50,40000000,100000000,47,0000000000,1,0xfec86ba6eb707ed08905757b1bb44b8f,0,0,0x40,'ebd07771ace8677a',0x"+OPERATOR_KEY+");"
    logger.info("DB_ENTRY:"+str(DB_ENTRY))
    APPEND_TO_DB=APPEND_TO_DB+DB_ENTRY+"\n"

    #Generating docker-compose
    DOCKER_ENTRY="    oai-nr-ue"+str(i)+":\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        image: oaisoftwarealliance/oai-nr-ue:develop\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        privileged: true\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        container_name: rfsim5g-oai-nr-ue"+str(i)+"\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        environment:\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            USE_ADDITIONAL_OPTIONS: -E --sa --rfsim -r 106 --numerology 1 --uicc0.imsi "+str(IMSI)+" -C 3619200000 --rfsimulator.serveraddr 192.168.71.140 --log_config.global_log_options level,nocolor,time\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        depends_on:\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            - oai-gnb\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        networks:\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            public_net:\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"                ipv4_address: 192.168.71."+str(FOURTH_GROUP_IP)+"\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        volumes:\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            - ../../conf_files/nrue.uicc.conf:/opt/oai-nr-ue/etc/nr-ue.conf\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"        healthcheck:\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            test: /bin/bash -c \"pgrep nr-uesoftmodem\"\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            interval: 10s\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            timeout: 5s\n"
    DOCKER_ENTRY=DOCKER_ENTRY+"            retries: 5\n"

    logger.info("DOCKER_ENTRY:"+str(DOCKER_ENTRY))
    APPEND_TO_DOCKER=APPEND_TO_DOCKER+DOCKER_ENTRY

APPEND_TO_DB=APPEND_TO_DB+"-- ***** end UEs part ******\n"

##APPENDING IN THE MIDDLE OF DB FILE
with open("./oai_db.sql", "r") as f:
    contents = f.readlines()
#218 old value
contents.insert(220,APPEND_TO_DB)

with open("./oai_db.sql", "w") as f:
    contents = "".join(contents)
    f.write(contents)

#DELETING ALREADY PRESENT UEs in docker-compose
lines = []
    # read file
with open(r"./docker-compose.yaml", 'r') as fp:
# read an store all lines into list
    lines = fp.readlines()
# Write file
with open(r"./docker-compose.yaml", 'w') as fp:
    # iterate each line
    for number, line in enumerate(lines):
        # delete line 5 and 8. or pass any Nth line you want to remove
        # note list index starts from 0
        if number not in range(102,282): #(5,8) 6,7,8
            fp.write(line)

##ADDING IPROUTE LINES TO UPF
##192.168.72.129 as GATEWAY
with open("./docker-compose.yaml", "r") as f:
    contents = f.readlines()

ROUTE_UPF="        #entrypoint: /bin/bash -c \\ \n"
ROUTE_UPF=ROUTE_UPF+"            #\"sleep 120; ip route delete default;\"\\\n"
ROUTE_UPF=ROUTE_UPF+"            #\"ip route add default via 192.168.72.129 dev eth1; sleep infinity\"\n"

contents.insert(49,ROUTE_UPF)
with open("./docker-compose.yaml", "w") as f:
    contents = "".join(contents)
    f.write(contents)

##APPENDING IN THE MIDDLE OF docker-copose
with open("./docker-compose.yaml", "r") as f:
    contents = f.readlines()

contents.insert(105,APPEND_TO_DOCKER)

with open("./docker-compose.yaml", "w") as f:
    contents = "".join(contents)
    f.write(contents)

logger.info("ENDED Configuration Files EDIT SCRIPT")
################# ****** END FILE GENERATION ######################
