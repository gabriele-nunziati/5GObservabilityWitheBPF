#!/bin/bash
#read -p "Enter how many UEs to install dependencies: " totalUes

totalUes=$1

i=0
OK_W_ROUTE=0

#APT-GET UPDATE, THEN INSTALL TRACEOUTE
while [ $i -lt $totalUes ]
    do
        echo "[UE $i] apt-get update"
        docker exec -it rfsim5g-oai-nr-ue$i /usr/bin/apt-get update 1>/dev/null
        if [[ $? != 0 ]]
        then
            echo "[UE $i] Couldn't apt-get update UE$i"
            #exit 5
        fi

        echo "[UE $i] Installing traceroute"
        docker exec -it rfsim5g-oai-nr-ue$i /usr/bin/apt-get install traceroute 1>/dev/null
        if [[ $? != 0 ]]
        then
            echo "[UE $i] Couldn't install traceroute UE$i"
            #exit 6
        fi

        i=$(($i + 1))
    done

#INSTALLING IPERF IN EVERY UE   
i=0
printf "\n\n"
while [ $i -lt $totalUes ]
    do
        echo "[UE $i] Installing iperf on UE$i" 
        docker exec -it rfsim5g-oai-nr-ue$i /usr/bin/apt-get install iperf  1>/dev/null

        if [[ $? != 0 ]]
        then
            echo "[UE $i] Couldn't install IPERF on UE$i"
            #exit 7
        fi

        i=$(($i + 1))
    done

#INSTALLING IPER ON ext-dn

printf "\n\n"
echo "-------> [ext-dn] apt-get update"
printf "\n\n"

docker exec -it rfsim5g-oai-ext-dn /usr/bin/apt-get update 1>/dev/null
if [[ $? != 0 ]]
    then
        echo "[!!!EXT-DN] Couldn't apt-get update"
        #exit 5
    fi

printf "\n\n"
echo "-------> [ext-dn] installing iperf"
printf "\n\n"

docker exec -it rfsim5g-oai-ext-dn /usr/bin/apt-get install iperf 1>/dev/null
if [[ $? != 0 ]]
    then
        echo "[!!!EXT-DN] Couldn't install iperf"
        #exit 5
    fi