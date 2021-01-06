import subprocess as sp
import cv2
import numpy as np
from PIL import Image

import os
import time
import threading
import yaml



dev_file = open("config/single_stream.yml", 'r')
dev_list = yaml.load(dev_file,yaml.FullLoader)["devices"]

NUM_DEVS = len(dev_list)

MAX_WIDTH = 0
MAX_HEIGHT = 0
MAX_FPS = 0
MAX_FPS_DEV = 0
thread_list = []
ffmpeg_list = []
srv_list = []
start_stream_cmds = []
stop_stream_cmds = []
dev_cfgs = []

# frames_available = []
# tf.compat.v1.disable_eager_execution()
for i,dev in enumerate(dev_list):
    # load config
    cfg_file = open(os.path.join("config",dev["config_file"]),'r')
    dev_cfg = yaml.load(cfg_file,yaml.FullLoader)
    dev_cfgs.append(dev_cfg)

    PIPE = os.path.join("/tmp",dev["name"])
    PORT = int(dev_cfg["netcat"]["port"])


    ffmpeg_cmd = ["ffmpeg",
                    "-i", PIPE,
                    "-pix_fmt", "bgr24",
                    "-vcodec", 'rawvideo',
                    "-an", "-sn",
                    "-f", "image2pipe",
                    "-"]


    ssh_prefix = f"ssh pi@{dev['name']}"

    set_cfg_cmd = f"scp config/{dev['name']}_stream_cfg.yml pi@{dev['name']}:/home/pi/raspivid_stream/stream_cfg.yml"

    srv_cmd = ["/bin/bash","receive_stream_remote.sh",str(PIPE),str(PORT)]

    start_stream_cmd = ssh_prefix + " \'start_stream\'"
    stop_stream_cmd = ssh_prefix + " \'stop_stream\'"


    start_stream_cmds.append(start_stream_cmd)
    stop_stream_cmds.append(stop_stream_cmd)

    # always stop stream first
    os.system(stop_stream_cmd)

    # copy new config file over
    os.system(set_cfg_cmd)
    # start video server on remote
    srv = sp.Popen(srv_cmd)
    time.sleep(0.1)
    srv_list.append(srv)

    # read from pipe and decode h264 stream to image
    ffmpeg = sp.Popen(ffmpeg_cmd, stdout=sp.PIPE, bufsize=10**8) 
    time.sleep(1)
    ffmpeg_list.append(ffmpeg)

    if int(dev_cfg["video"]["width"]) > MAX_WIDTH:
        MAX_WIDTH =int(dev_cfg["video"]["width"])
    if int(dev_cfg["video"]["height"]) > MAX_HEIGHT:
        MAX_HEIGHT =int(dev_cfg["video"]["height"])
    if int(dev_cfg["video"]["fps"]) > MAX_FPS:
        MAX_FPS =int(dev_cfg["video"]["fps"])
        MAX_FPS_DEV = i
    # frames_available.append(threading.Event())

global combined_image_flat, running
image_combined = np.zeros((MAX_HEIGHT*int(np.ceil(NUM_DEVS/2)), MAX_WIDTH*min(NUM_DEVS,2),3),dtype='uint8')
combined_image_flat = np.zeros((MAX_HEIGHT*MAX_WIDTH*3*NUM_DEVS),dtype='uint8')
running = True

def thread(dev=0):
    global running, combined_image_flat,  avg_dt, ffmpeg_list
    w = dev_cfgs[dev]["video"]["width"]
    h = dev_cfgs[dev]["video"]["height"]
    fps = dev_cfgs[dev]["video"]["fps"]
    st = time.time()
    while running:

        image = np.fromstring(ffmpeg_list[dev].stdout.read(int(w * h * 3)),
                              dtype='uint8')  # read bytes of single frames
        if image.size > 0:
            dt = time.time() - st
            st = time.time()
            avg_dt[dev] += (dt - avg_dt[dev]) * 0.03

            start_i = MAX_HEIGHT * MAX_WIDTH * 3 * dev
            end_i = MAX_HEIGHT * MAX_WIDTH * 3 * dev + image.size
            combined_image_flat[start_i:end_i] = image

        elif (time.time() - st) < (1 / (fps + 10)):
            time.sleep((1 / (fps + 10)) - (time.time() - st))

for i in range(NUM_DEVS):
    os.system(start_stream_cmds[i])
# TODO Synchronize Start of multiple cameras
# send start stream command
for i in range(NUM_DEVS):
    thread_list.append(threading.Thread(target=thread, kwargs={'dev': i}))
    thread_list[i].start()




avg_dt=[0.0]*NUM_DEVS
fps_avg = [0]*NUM_DEVS
first_loop = True
disp_dt = 0.0
start = time.time()
while True:
    end = time.time()

    if (end- start) < (1 / (MAX_FPS + 10)):
        time.sleep((1 / (MAX_FPS + 10)) - (end - start))

    disp_dt += ((time.time() - start) - disp_dt) * 0.005
    start = time.time()




    image_combined = combined_image_flat.reshape(
        (MAX_HEIGHT * int(np.ceil(NUM_DEVS / 2)), MAX_WIDTH * min(NUM_DEVS, 2), 3))
    for i in range(NUM_DEVS):
        ffmpeg_list[i].stdout.flush()
        fps_avg = 1.0/avg_dt[i] if avg_dt[i] > 0 else 0
        fps_str = "FPS: %0.3f" % fps_avg
        image_combined = cv2.putText(image_combined, fps_str, ((MAX_HEIGHT * int(np.ceil(i/ 2)))+20,(MAX_WIDTH * (i%2)) + 50) , cv2.FONT_HERSHEY_SIMPLEX ,0.5, (0,0,255), 1, cv2.LINE_AA)
    cv2.imshow("Video", image_combined)

    disp_fps = 1.0/disp_dt if disp_dt > 0 else 0
    disp_fps_str = "Display FPS: %0.3f" % disp_fps
    cv2.displayOverlay("Video", disp_fps_str )


    if cv2.waitKey(1) & 0xFF == ord('q'):

        running = False
        for i in range(NUM_DEVS):
            os.system(stop_stream_cmds[i])

        break



for i in range(NUM_DEVS):
    thread_list[i].join()
cv2.destroyAllWindows()
