import cv2
import numpy as np
from scipy import ndimage
import time

# Load your image here
image = cv2.imread("C:\\Users\\Bogom\\Pictures\\Screenshots\\TEST4.jpg")
image = cv2.resize(image, [1280, 720])
cv2.imshow(" ", image)
cv2.waitKey(0)

# Convert the image to grayscale
img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Sobel operator
sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=3)
sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=3)

# Calculate magnitude of gradients
sobel = np.sqrt(sobelx**2 + sobely**2)
sobel = np.uint8(np.absolute(sobel))

# Convert to Binary
binary_image = cv2.adaptiveThreshold(sobel, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 3)

# Find contours
contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = list(contours)

# Find the next largest contour
largest_contour = max(contours, key=cv2.contourArea)

# Get the bounding box coordinates
x, y, w, h = cv2.boundingRect(largest_contour)

# Create a mask for the object
mask = np.zeros(img_gray.shape, dtype=np.uint8)
cv2.drawContours(mask, [largest_contour], -1, (255,255,255), thickness=cv2.FILLED)


bottom = int(0.15 * img_gray.shape[0])
right = int(0.2 * img_gray.shape[1])
for i in range(img_gray.shape[0]):
    for j in range(right):
        mask[i,j] = 0

for i in range(bottom):
    for j in range(img_gray.shape[1]):
        mask[img_gray.shape[0] - i - 1,j] = 0

for i in range(bottom):
    for j in range(img_gray.shape[1]):
        mask[i,j] = 0

# Perform a Dilation
kernel = np.ones((20,20), np.uint8)
mask = cv2.dilate(mask, kernel, iterations=3)

# erode on large images
if cv2.contourArea(largest_contour) > 400000:
    
    # erode noise
    kernel = np.ones((50,10), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)

    kernel = np.ones((10,30), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=2)

rows, cols, channels = image.shape
segmented = np.zeros(image.shape, dtype = np.uint8)

for i in range(rows):
    for j in range(cols):
        if mask[i, j] == 255:
            segmented[i, j] = image[i, j]

# show the bounding box
cv2.rectangle(segmented, (x, y), (x + w, y + h), (100, 255, 0), 2)
cv2.imshow(" ", segmented)


