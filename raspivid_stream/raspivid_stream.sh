#!/bin/bash

set -e
source /home/pi/raspivid_stream/yaml.sh

shell_pid=$$

pstream=false
cstream=false

kill_descendant_processes() {
    local pid="$1"
    local and_self="${2:-false}"
    if children="$(pgrep -P "$pid")"; then
        for child in $children; do
            kill_descendant_processes "$child" true
        done
    fi
    if [[ "$and_self" == true ]]; then
        kill -SIGTERM "$pid"
    fi
}


while true
do
  if [[ $cstream == "true" ]]
  then
    if [[ $pstream == "false" ]]
    then
     echo "Reading stream configuration file..."
     # print file to stdout
     parse_yaml /home/pi/raspivid_stream/stream_cfg.yml && echo

     # get variables from file
     create_variables /home/pi/raspivid_stream/stream_cfg.yml

     echo "Starting stream ..."
     raspivid --flush -v -n -o - -t 0 -w ${video_width} -h ${video_height} -fps ${video_fps} -b ${video_bitrate} | nc ${netcat_remote_ip} ${netcat_port} &

    fi
  elif [[ $cstream == "false" ]]
  then

       kill_descendant_processes ${shell_pid}
  fi

  pstream=${cstream}
  cstream=$(</home/pi/raspivid_stream/stream_state)
 
done

