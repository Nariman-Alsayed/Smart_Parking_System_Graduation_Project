# https://stackoverflow.com/questions/53347759/importerror-libcblas-so-3-cannot-open-shared-object-file-no-such-file-or-dire
from concurrent.futures import process
import cv2
import numpy as np
import pytesseract
import urllib.request
from time import time

# configuration variables
skipCount = 200
waitInterval = 1
hostname = '192.168.1.7'
caps = [
    cv2.VideoCapture('2.mp4')  # , cv2.CAP_DSHOW),
]


def detectPlate(img):
    plateClassifier = cv2.CascadeClassifier(
        'haarcascade_russian_plate_number.xml')

    # detect plates
    plates = plateClassifier.detectMultiScale(img)

    # sort by area
    if len(plates) > 0:
        # sort plates by size in ascending order
        plates = sorted(plates, key=lambda plate: plate[2]*plate[3])

        # select the plate with the biggest area and extract its coordinates
        return plates[-1]

    return ()


# runtime variables
timeouts = [0] * len(caps)
lastDetectedPlates = [''] * len(caps)
# # read image
# img = cv2.imread('img/car0.jpg')

# configure the capture devices

# img = cv2.resize(img, (640, 480))

# read
while True:
    # iterate over the defined capture devices
    for i, cap in enumerate(caps):
        # attempt to read image if the capture device is open
        if cap.isOpened():
            # read image
            success, img = cap.read()

            # image read successfully
            if success:
                # cv2.imshow(f"cam{i}", img)

                # if in timeout period, skip this frame
                if timeouts[i] > 0:
                    timeouts[i] -= 1
                else:
                    # gray scale
                    greyImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    # smooth the image to remove noise
                    greyImg = cv2.bilateralFilter(greyImg, 5, 15, 15)

                    # perform detection
                    coordinates = detectPlate(greyImg)

                    # process the plate img if one was found
                    if len(coordinates) == 4:
                        (x, y, w, h) = coordinates

                        # display original image with ROI
                        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(img, "Plate", (int(x*0.75), int(y*0.95)),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                        cv2.imshow(f"cam{i}", img)

                        # # display plate
                        # cv2.imshow(f"plate{i}", plateImg)

                        # extract plate from img
                        plateImg = greyImg[y:y+h, x:x+w]

                        # convert to binary image
                        (threshold, plateImg) = cv2.threshold(
                            plateImg, 127, 255, cv2.THRESH_OTSU)

                        # extract plate number using tesseract
                        plateNumber = pytesseract.image_to_string(
                            plateImg, 'eng', config='--tessdata-dir ./tessdata')

                        # strip whitespace characters
                        plateNumber = plateNumber.strip()

                        if not len(plateNumber):
                            continue

                        print("Detected license plate Number is:", plateNumber)

                        if lastDetectedPlates[i] == plateNumber:
                            timeouts[i] = skipCount
                            print(
                                f"Duplicate plate number detected!, skipping {skipCount*waitInterval}ms")
                        else:
                            lastDetectedPlates[i] = plateNumber
                            # contact server to report detected plate number

                            if i == 0:  # entry camera
                                print("Sending entry data to server")
                                try:
                                    print(urllib.request.urlopen(
                                        f"http://{hostname}/SmartParking/api/carEntry.php?car_plate_number={plateNumber}").read())
                                except:
                                    print("No response from server")

                            else:  # exit camera
                                print(f"Sending exit data to server")
                                try:
                                    print(urllib.request.urlopen(
                                        f"http://{hostname}/SmartParking/api/carExit.php?car_plate_number={plateNumber}").read())
                                except:
                                    print("No response from server")

    if cv2.waitKey(waitInterval) == ord('q'):
        break

# release
for cap in caps:
    cap.release()

# # process image
# detectPlate(img)

cv2.destroyAllWindows()
