#!/bin/bash

# Function to check if the input is a number
is_number() {
re='^[0-9]+$'
if ! [[ $1 =~ $re ]] ; then
    return 1 # Not a number
else
    return 0 # Is a number
fi
}

# Check if there are two arguments and if they're numbers
if [ "$#" -eq 2 ] && is_number "$1" && is_number "$2"; then
    totalUes=$1
    trigger_i=$2
    echo "The number of UEs deployed is: $totalUes"
    echo "The trigger index is: $trigger_i"
else
    # Prompt for the first number if not provided or not a valid number
    if ! is_number "$1"; then
    echo "Please enter how many UEs are deployed:"
    read -r totalUes
    while ! is_number "$totalUes"; do
        echo "That's not a valid number. Please enter how many UEs are deployed:"
        read -r totalUes
    done
    else
        totalUes=$1
    fi

    # Prompt for the second number if not provided or not a valid number
    if ! is_number "$2"; then
        echo "Please enter the trigger index:"
        read -r trigger_i
        while ! is_number "$trigger_i"; do
            echo "That's not a valid number. Please enter the trigger index:"
            read -r trigger_i
        done
    else
        trigger_i=$2
    fi

    echo "The number of UEs deployed is: $totalUes"
    echo "The trigger index is: $trigger_i"
fi

../../dep_installer/v1/dep_installer.sh $totalUes

../../connection_verifier/connection_verifier.sh $totalUes

../../data_exchanger/data_exchanger.sh $totalUes $trigger_i


