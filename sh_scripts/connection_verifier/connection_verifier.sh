#read -p "Enter how many UEs to poll: " totalUes

totalUes=$1

i=0
OK=0

#PATCHING UPF
docker exec -it rfsim5g-oai-upf /usr/bin/ip route delete default
if [[ $? != 0 ]]
then
    echo "Couldn't patch UPF default route"
    exit 1
fi

docker exec -it rfsim5g-oai-upf /usr/bin/ip route add default via 192.168.72.129 dev eth1
if [[ $? != 0 ]]
then
    echo "Couldn't patch UPF default route"
    exit 2
fi

printf "\n\n"
echo "-------> Patched UPF default route"
printf "\n\n"

#Check if every UE can ping via the tunnel
while [ $i -lt $totalUes ]
    do

        docker exec -it rfsim5g-oai-nr-ue$i ping -I oaitun_ue1 www.elpais.com -c 2
        pingStatus=$?

        if [[ $pingStatus -eq 1 ]]
        then 
            echo "UE$i NOT CONNECTED TO INTERNET VIA TUNNEL!"
        elif [[ $pingStatus -eq 0 ]]
        then
            OK=$(($OK + 1))
        fi


        i=$(($i + 1))
    done

printf "\n\n"
echo "-------> Connected UE: $OK"
printf "\n\n"

#Cambio gateway and check that default is tunnel via traceroute

i=0
OK_W_ROUTE=0
while [ $i -lt $totalUes ]
    do

        docker exec -it rfsim5g-oai-nr-ue$i /usr/bin/ip route delete default
        if [[ $? != 0 ]]
        then
            echo "Couldn't patch UE$i default route"
            #exit 3
        fi
        docker exec -it rfsim5g-oai-nr-ue$i /usr/bin/ip route add default via 12.1.1.1 dev oaitun_ue1
        if [[ $? != 0 ]]
        then
            echo "Couldn't patch UE$i default route"
            #exit 4
        fi

        docker exec -it rfsim5g-oai-nr-ue$i /usr/bin/traceroute www.elpais.com -m 2 | grep 12.1.1.1
        tracerouteStatus=$?
        if [[ $tracerouteStatus != 0 ]]
        then
            echo "UE$i: Route doesn't go to 12.1.1.1 (the tunnel) as default"
            #exit 6
        elif [[ $tracerouteStatus == 0 ]]
        then
            OK_W_ROUTE=$(($OK_W_ROUTE + 1))
        fi

        i=$(($i + 1))
    done

printf "\n\n"
echo "-------> UEs with tunnel as default route: $OK_W_ROUTE"
printf "\n\n"