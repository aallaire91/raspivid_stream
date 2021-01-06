import subprocess as sp
import cv2
import cv2.aruco as aruco
import numpy as np
from PIL import Image
import tensorflow as tf
import os
import time
import threading

WIDTH = 640
HEIGHT = 480
FPS = 90
STREAM_FPS = 120  # make this a little higher than actual frame rate to avoid buffering

PICAM0_PIPE = "/tmp/picam0"
PICAM1_PIPE = "/tmp/picam1"
PICAM0_PORT = 5000
PICAM1_PORT = 5001

tf.compat.v1.disable_eager_execution()
ffmpeg_cmd_1 = ["ffmpeg",
                "-i",  "/tmp/picam0",
                "-pix_fmt", "bgr24",
                "-vcodec", 'rawvideo',
                "-an", "-sn",
                "-f", "image2pipe",
                "-"]

ffmpeg_cmd_2 = ["ffmpeg",
                "-i",  "/tmp/picam1",
                "-pix_fmt", "bgr24",
                "-vcodec", 'rawvideo',
                "-an", "-sn",
                "-f", "image2pipe",
                "-"]

ssh_picam0 = "ssh pi@10.0.0.115"
ssh_picam1 = "ssh pi@10.0.0.115"

srv_cmds = [["/bin/bash","video_stream_server_ws.sh",str(PICAM0_PIPE),str(PICAM0_PORT)],
            ["/bin/bash","video_stream_server_ws.sh",str(PICAM1_PIPE),str(PICAM1_PORT)]]
start_stream_cmds = [ssh_picam0 + " \'start_stream\'",ssh_picam1 + " \'start_stream\'"]
stop_stream_cmds = [ssh_picam0 + " \'stop_stream\'",ssh_picam1 + " \'stop_stream\'"]

# always stop stream first
# os.system(stop_stream_cmds[0])
os.system(stop_stream_cmds[1])

# start video server on ws
# srvs = [sp.Popen(srv_cmds[0]),sp.Popen(srv_cmds[1])]
sp.Popen(srv_cmds[1])
time.sleep(0.1)

# read from pipe and decode h264 stream to image
# ffmpeg1 = sp.Popen(ffmpeg_cmd_1, stdout=sp.PIPE, bufsize=10**8)
ffmpeg2 = sp.Popen(ffmpeg_cmd_2, stdout=sp.PIPE, bufsize=10**8)
time.sleep(1)

# send start stream command
# os.system(start_stream_cmds[0])
os.system(start_stream_cmds[1])

global image0, image1, running, fps0, fps1, st0, st1
# st0 = time.time()
st1 = time.time()

# image0 = np.zeros((HEIGHT,WIDTH,3),dtype='uint8')
image1 = np.zeros((HEIGHT,WIDTH,3),dtype='uint8')
w = WIDTH
h = HEIGHT
running = True
# avg_dt0=0.0
avg_dt1 = 0.0

def thread1():
    global running
    while running:
        raw_image = ffmpeg2.stdout.read(int(w*h*3))  # read bytes of single frames

        global image1, st1, avg_dt1
        image1 = np.fromstring(raw_image,dtype='uint8')
        if image1.size>0:
            dt = time.time() - st1
            avg_dt1 += (dt - avg_dt1) * 0.03
            st1 = time.time()




# def thread1():
#     global running
#     while running:
#         raw_image = ffmpeg2.stdout.read(int(w*h*3))  # read bytes of single frames
#
#         global image1, st1, avg_dt1
#         image1 = np.fromstring(raw_image,dtype='uint8')
#         if image1.size>0:
#             dt = time.time() - st1
#             # fps1 = 1.0/dt
#             # ct1+=1
#             avg_dt1 += (dt - avg_dt1) * 0.03
#             st1 = time.time()


t1 = threading.Thread(target=thread1)
# t1 = threading.Thread(target=thread1)

t1.start()
# t1.start()

# image_combined = np.zeros((HEIGHT, WIDTH,3),dtype='uint8')
# ffmpegs = [ffmpeg1]#[ffmpeg1, ffmpeg2]

count = 0

fps0_avg = 0
fps1_avg = 0
while True:
    # images =[image1,image0]
    # for i in range(len(images)):
    #     # images
    #     if images[i].size > 0:
    #         image_combined[:, w*i:w*i + w,:] = images[i].reshape((h,w,3))

    ffmpeg2.stdout.flush()
    image =  image1.reshape((h,w,3))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # set dictionary size depending on the aruco marker selected
    aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)

    # detector parameters can be set here (List of detection parameters[3])
    parameters = aruco.DetectorParameters_create()
    parameters.adaptiveThreshConstant = 10
    parameters.detectInvertedMarker=True
    # lists of ids and the corners belonging to each id
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    aruco.drawDetectedMarkers(image, corners)
    cv2.imshow("Video", image)
    fps1_avg = 1.0/avg_dt1 if avg_dt1 > 0 else 0
    # fps1_avg = 1.0/avg_dt1 if avg_dt1 > 0 else 0
    left_fps_str = "fps: %0.3f" % fps1_avg
    # right_fps_str = "right fps: %0.3f" % fps0_avg
    cv2.displayOverlay("Video", left_fps_str )
    #     fps0_avg = 0
    #     fps1_avg = 0
    #     count = 0
    # else:
    #     count+=1
    #     fps0_avg+=fps0
    #     fps1_avg+=fps1

    if cv2.waitKey(1) & 0xFF == ord('q'):

        running = False
        os.system(stop_stream_cmds[1])
        # os.system(stop_stream_cmds[1])
        break

t1.join()
# t1.join()
cv2.destroyAllWindows()
