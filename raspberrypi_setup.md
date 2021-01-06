1. enable camera 

`sudo raspi-config`

- Select Interfacing Options then Camera and hit Enter. Choose Yes then Ok. 
- Select Interfacing Options then SSH and hit Enter. Choose Yes then Ok.
- Go to Finish and you'll be prompted to reboot, but wait to reboot until step 2. 

2. change hostname to device `name` specified in `dual_stream.yml` and `single_stream.yml`

- edit /etc/hosts -> change hostname for 127.0.1.1 to new hostname
- edit /etc/hostname -> change hostname to new hostname
- reboot to take effect

3. copy ssh keys to pi

`ssh-copy-id pi@${hostname}`

4. copy `raspivid_stream` folder to rasberry pi. from remote computer, run

`scp -r raspivid_stream pi@${hostname}:/home/pi/` 

5. copy config file (ex: `${hostname}_stream_cfg.yml`) to rasberry pi as `/home/pi/raspivid_stream/stream_cfg.yml`. from remote computer, run

`scp config/${hostname}_stream_cfg.yml pi@${hostname}:/home/pi/raspivid_stream/stream_cfg.yml`

6. make stop_stream and start_stream scripts executable and copy to usr/bin

```
ssh pi@${hostname} 'chmod +x /home/pi/raspivid_stream/stop_stream' 
ssh pi@${hostname} 'chmod +x /home/pi/raspivid_stream/start_stream' 
ssh pi@${hostname} 'sudo cp /home/pi/raspivid_stream/stop_stream /usr/bin'
ssh pi@${hostname} 'sudo cp /home/pi/raspivid_stream/start_stream /usr/bin'
ssh pi@${hostname} 'stop_stream'
```

6. create and enable service (to automatically start at boot)

```
ssh pi@${hostname} 'cp /home/pi/raspivid_stream/raspivid_stream.service /etc/systemd/system/'
ssh pi@${hostname} 'sudo systemctl enable raspivid_stream'
```


