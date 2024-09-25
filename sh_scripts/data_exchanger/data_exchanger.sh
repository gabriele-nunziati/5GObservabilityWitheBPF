#read -p "Enter how many UEs that have to start exchanging data: " totalUes

totalUes=$1
trigger_i=$2

#Creating directory iper on ext-dn
docker exec -it rfsim5g-oai-ext-dn /usr/bin/mkdir -p iperf
docker exec -it rfsim5g-oai-ext-dn /usr/bin/touch iperf/output_iperf.txt

#press to continue
read -p "Press any key to start iperf SERVER or CTRL+C to exit ..."

docker exec -itd rfsim5g-oai-ext-dn /usr/bin/bash -c "iperf -s -p 5201 -u -i 1 -b 500K -B 192.168.72.135 > ./iperf/output_iperf.txt"

printf "\n\n"
echo "-------> *** Starting iperf traffic ***"
printf "\n\n"

echo "[ext-dn] STARTING IPERF SERVER, on port 5201, IP 192.168.72.135"
#docker exec -itd rfsim5g-oai-ext-dn /usr/bin/bash -c "iperf -s -p 5201 -u -i 1 -b 500K -B 192.168.72.135 > ./iperf/output_iperf.txt"

if [[ $? != 0 ]]
then
    echo "Couldn't start iperf server"
    exit 2
fi


i=0
#START CLIENT FROM EVERY UE
printf "\n"
echo "!!! STARTING UEs CLIENTS"
printf "\n"

while [ $i -lt $totalUes ]
    do

        echo "[UE $i] STARTING IPERF client, server IP 192.168.72.135, port 5201"
        docker exec -itd rfsim5g-oai-nr-ue$i /usr/bin/iperf -c 192.168.72.135 -p 5201 -u -i 1 -t 250 -b 500K

        if [[ $? != 0 ]]
        then
            echo "Couldn't start iperf client on $i UE"
            exit 3
        fi

        sleep 1

        i=$(($i + 1))
    done

sleep 60

cd /home/gabriele/april/FULL_STACK/fifth/openairinterface5g/ci-scripts/yaml_files/5g_rfsimulator
docker compose down oai-nr-ue$trigger_i

echo "TRIGGERED UNDEPLOYMENT UE-$triggered_i"

sleep 75
printf "\n\n### fine attacco\n"
#docker exec -it rfsim5g-oai-ext-dn /usr/bin/kill iperf
