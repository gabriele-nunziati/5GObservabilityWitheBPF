#bin/bash

#How many UEs to poll

read -p "Enter how many UEs to poll: " totalUes

i=0

TIME_ZERO=$(date +%s.%N | awk '{printf "%.4f\n", $0}')
echo $TIME_ZERO

mkdir -p ./ue_poller_csv

filename="./ue_poller_csv/$(date '+%Y-%m-%d-%H:%M:%S.%3N').csv"
touch $filename

echo "TIME--> DOWN,UP NO REG,UP & REG"
echo "TIME,DOWN,UP NO REG,UP & REG" >>$filename
while :
do
    DOWN=0
    UP_NOT_REG=0
    UP_REG=0

    TIME_ABS=$(date +%s.%N | awk '{printf "%.4f\n", $0}')
    TIME=$(echo "$TIME_ABS - $TIME_ZERO" | bc | awk '{printf "%.4f\n", $0}')
 
    while [ $i -lt $totalUes ]
    do

        OUTPUT_i=$(docker exec -it rfsim5g-oai-nr-ue$i /usr/sbin/ifconfig 2>/dev/null)

        if [[ $? == 1 ]]
        then 
            DOWN=$(($DOWN+1))
        elif [[ $OUTPUT_i == *"oaitun_ue1:"* ]]
        then
            UP_REG=$(($UP_REG+1))
        elif [[ $OUTPUT_i == "eth0:"* ]] && [[ $OUTPUT_i != *"oaitun_ue1:"* ]]
        then
            UP_NOT_REG=$(($UP_NOT_REG+1))
        fi

        i=$(($i + 1))
    done
    
    echo "$TIME--> $DOWN,$UP_NOT_REG,$UP_REG" 
    echo "$TIME,$DOWN,$UP_NOT_REG,$UP_REG" >>$filename

    i=0
    sleep 1

done
