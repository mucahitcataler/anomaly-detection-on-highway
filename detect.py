import cv2 as cv
import numpy as np
import time

import serial
from pyfirmata import Arduino,util
from pyfirmata import OUTPUT,INPUT
from serial import Serial
import sys
import os

normalColor = (0, 175, 0)
warningColor = (0, 0, 175)
lastWarningTime = 0
camera = 1
classesNames = ["vehicle", "animal", "rock"]

# In Turkish as in the screenshots
# classesNames = ["arac", "hayvan", "kaya"]

# connect Arduino to write warning on lcd displays
# arduino = serial.Serial('COM7',9600)
# arduino2 = serial.Serial('COM5',9600)

# Write warning messages to lcd displays and video on the sceen
def sendWarning(img, x, y, w, h, warningCode, cameraId=camera):
    message = "WARNING"
    if warningCode == 0:
        message = "A VEHICLE IS IN THE SAFETY STRIP"
    elif warningCode == 1:
        message = "AN ANIMAL DETECTED ON THE HIGHWAY"
    elif warningCode == 2:
        message = "A ROCK DETECTED ON THE HIGHWAY"
    cv.rectangle(img, (0, img.shape[0] - 30), (img.shape[1], img.shape[0]), warningColor, -1)
    cv.putText(img, message, (5, img.shape[0] - 7), cv.FONT_HERSHEY_TRIPLEX, 0.7, (255 ,255 ,255), 1)
    
    currentTime = time.time()
    global lastWarningTime
    if currentTime - lastWarningTime > 20: #seconds
        if cameraId == 1:
            print("Anomaly detected in area 1.")
            # Write a message on lcd display.
            # arduino.write(b'2')
            # arduino2.write(b'2')
        elif cameraId == 2:
            print("Anomaly detected in area 2.")
            # Write a message on lcd display.
            # arduino.write(b'4')
            # arduino2.write(b'2')
        lastWarningTime = currentTime
    return

# Find cars position and if they are on wrong strip detect as an anomaly.
# For anomalies return False
def carPosition(x, y, w, h, cameraId=camera):
    pointX = x + w//2
    pointY = y + h//2

    #CAMERA 1
    if cameraId == 1:
        if np.all(wrongStrip1[pointY][pointX] == np.array([255,255,255])):
            return False

    #CAMERA 2
    if cameraId == 2:
        if np.all(wrongStrip2[pointY][pointX] == np.array([255,255,255])):
            return False

    return True

# Find objects in image and detect if there is an anomaly in it.
def findObjects(outputs, img, confThreshold=0.5, nmsThreshold=0.2, cameraId=0):
    H, W = img.shape[:2]

    boxes = []
    confidences = []
    classIDs = []

    for output in outputs:
        for det in output:
            scores = det[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            if confidence > confThreshold:
                x, y, w, h = det[:4] * np.array([W, H, W, H])
                p0 = int(x - w//2), int(y - h//2)
                p1 = int(x + w//2), int(y + h//2)
                boxes.append([*p0, int(w), int(h)])
                confidences.append(float(confidence))
                classIDs.append(classID)
                # cv.rectangle(img, p0, p1, (0, 255, 0), 1)

    indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    if len(indices) > 0:
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            pointX = x + w//2
            pointY = y + h//2
            if cameraId == 1:
                if np.all(detectionArea1[pointY][pointX] == np.array([0,0,0])):
                    continue
            if cameraId == 2:
                if np.all(detectionArea2[pointY][pointX] == np.array([0,0,0])):
                    continue    
            
            color = normalColor

            # Detect anomalies.
            if classIDs[i] == 0:
                if not carPosition(x, y, w, h, cameraId=cameraId):
                    sendWarning(img, x, y, w, h, 0, cameraId=cameraId)
                    color = warningColor
            elif classIDs[i] == 1:
                sendWarning(img, x, y, w, h, 1, cameraId=cameraId)
                color = warningColor
            elif classIDs[i] == 2:
                sendWarning(img, x, y, w, h, 2, cameraId=cameraId)
                color = warningColor

            cv.rectangle(img, (x, y), (x + w, y + h), color, 2)
            # text = "{}: {:.2f}%".format(classesNames[classIDs[i]], confidences[i]*100)
            text = f"{classesNames[classIDs[i]]}"
            cv.rectangle(img, (x - 1, y - 25), (x + w + 1, y + 5), color, -1)
            cv.putText(img, text, (x + 1, y - 5), cv.FONT_HERSHEY_TRIPLEX, 0.7, (255 ,255 ,255), 1)

# Initilize and mask image for each camera.
# Masking detection area and wrong strip for vehicles.
# CAMERA-1
wrongStrip1 = np.zeros((480, 640, 3), np.uint8)
pt1 = (165, 120)
pt2 = (0, 45)
pt3 = (170, 0)
pt4 = (310, 50)
triangle_cnt = np.array( [pt1, pt2, pt3, pt4] )
cv.drawContours(wrongStrip1, [triangle_cnt], 0, (255,255,255), -1)
detectionArea1 = np.zeros((480, 640, 3), np.uint8)
pt1 = (30, 100)
pt2 = (635, 155)
pt3 = (630, 70)
pt4 = (165, 20)
triangle_cnt = np.array( [pt1, pt2, pt3, pt4] )
cv.drawContours(detectionArea1, [triangle_cnt], 0, (255,255,255), -1)
# CAMERA-2
wrongStrip2 = np.zeros((480, 640, 3), np.uint8)
pt1 = (460, 160)
pt2 = (640, 0)
pt3 = (210, 50)
triangle_cnt = np.array( [pt1, pt2, pt3] )
cv.drawContours(wrongStrip2, [triangle_cnt], 0, (255,255,255), -1)
detectionArea2 = np.zeros((480, 640, 3), np.uint8)
pt1 = (0, 90)
pt2 = (470, 0)
pt3 = (640, 120)
pt4 = (0, 235)
triangle_cnt = np.array( [pt1, pt2, pt3, pt4] )
cv.drawContours(detectionArea2, [triangle_cnt], 0, (255,255,255), -1)

# Give the configuration and weight files for the model and load the network.
net = cv.dnn.readNetFromDarknet('yolov3_testing.cfg', 'yolov3_training_last.weights')
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

cap = cv.VideoCapture(1)
cap2 = cv.VideoCapture(0)

while True:
    success, img = cap.read()
    success2, img2 = cap2.read()

    # Detect objects and check anomalies for camera 1.
    blob = cv.dnn.blobFromImage(img, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layerNames = net.getLayerNames()
    outputNames = [layerNames[i - 1] for i in net.getUnconnectedOutLayers()]
    outputs = net.forward(outputNames)
    findObjects(outputs, img, cameraId=1)

    # Detect objects and check anomalies for camera 2.
    blob = cv.dnn.blobFromImage(img2, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layerNames = net.getLayerNames()
    outputNames = [layerNames[i - 1] for i in net.getUnconnectedOutLayers()]
    outputs = net.forward(outputNames)
    findObjects(outputs, img2, cameraId=2)

    cv.rectangle(img, (240, 0), (400, 30), (0,0,0), -1)
    cv.putText(img, "CAMERA - 1", (248, 22), cv.FONT_HERSHEY_TRIPLEX, 0.7, (255 ,255 ,255), 1)
    cv.rectangle(img2, (240, 0), (400, 30), (0,0,0), -1)
    cv.putText(img2, "CAMERA - 2", (248, 22), cv.FONT_HERSHEY_TRIPLEX, 0.7, (255 ,255 ,255), 1)
    
    cv.imshow("Camera1", img)
    cv.imshow("Camera2", img2)

    if cv.waitKey(1) & 0xFF == ord('d'):
        break

cap.release()
cap2.release()
cv.destroyAllWindows()