#!/bin/bash
# ${1} - fifo pipe name
# ${2} - server port number

# delete fifo if already exists
if [[ -p ${1} ]]
then
  rm ${1}
fi

# create fifo with read/write permission
mkfifo -m 0666 ${1}
# start netcat server at specified port (${2}) and pipe recieved data to fifo
nc -l -p ${2} > ${1}


rm ${1}
# note - output to pipe operation is blocking until a process reads from the pipe. if no process is actively reading
# from the pipe, the video client connection will close immediately bc the connection is blocked by the pipe. To work
# around this, a process on the server side that reads from the pipe must be started before the client connection is
# initiated.

exit 0