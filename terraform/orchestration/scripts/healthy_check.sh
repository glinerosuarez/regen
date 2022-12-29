#!/bin/bash

max_retry=60
counter=0

until [ `docker inspect --format='{{json .State.Health.Status}}' $1 | tr -d '"'` = healthy ]
do
   sleep 1
   [[ counter -eq $max_retry ]] && echo "Failed!" && exit 1
   echo "Trying again. Try #$counter"
   ((counter++))
done