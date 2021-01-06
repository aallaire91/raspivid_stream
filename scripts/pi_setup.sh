#!/bin/bash
# ${1} - hostname
# ${2} - stream config file

# 3. copy ssh keys to pi

ssh-copy-id pi@${1}

# 4. copy `raspivid_stream` folder to rasberry pi

scp -r raspivid_stream pi@${1}:/home/pi/

# 5. copy config file (ex: `${hostname}_stream_cfg.yml`) to rasberry pi as `/home/pi/raspivid_stream/# stream_cfg.yml`

scp ${2} pi@${1}:/home/pi/raspivid_stream/stream_cfg.yml

# 6. make stop_stream and start_stream scripts executable and copy to usr/bin


ssh pi@${1} 'chmod +x /home/pi/raspivid_stream/stop_stream' 
ssh pi@${1} 'chmod +x /home/pi/raspivid_stream/start_stream' 
ssh pi@${1} 'chmod +x /home/pi/raspivid_stream/raspivid_stream.sh' 
ssh pi@${1} 'sudo cp /home/pi/raspivid_stream/stop_stream /usr/bin'
ssh pi@${1} 'sudo cp /home/pi/raspivid_stream/start_stream /usr/bin'
ssh pi@${1} 'stop_stream'


# 7. create and enable service (to automatically start at boot)


ssh pi@${1} 'sudo cp /home/pi/raspivid_stream/raspivid_stream.service /etc/systemd/system/'
ssh pi@${1} 'sudo systemctl enable raspivid_stream'

# install gawk
ssh pi@${1} 'sudo apt-get -y install gawk'
