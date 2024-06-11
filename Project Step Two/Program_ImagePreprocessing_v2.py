# clear globals to prevent undefined behavior with images
globals().clear()

# import modules
from pytesseract import *
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math as m

# locate the tesseract.exe file as downloaded 
pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# import the image
image = cv2.imread('C:\\Users\\Bogom\\Pictures\\Screenshots\\Screenshot (342).png')

# resize and recolor the image before reading (improves accuracy)
image_text = cv2.resize(image, [1280, 720])
image_text = cv2.cvtColor(image_text, cv2.COLOR_BGR2RGB)

# extract and store text as a string and list (separately)
text_str = pytesseract.image_to_string(image_text)
text_list = list(text_str) # mainly manipulate the list of characters

# filter ascii characters out, replace with "NaN"
def ascii_filter(char_list):
    for i in range(len(char_list)):
        try:
            table_val = ord(char_list[i])
            if table_val > 127 or table_val < 0: # 0-127 are traditional ascii values
                char_list[i] = 'NaN'
        except TypeError:
            char_list[i] = 'Err'
    return char_list

# count the number of instances of a wrong character in the list
def count_instances(char_list, find):
    try:
        count = 0
        for i in range(len(char_list)):
            if char_list[i] == find:
                count += 1
            else:
                pass
    except ValueError or IndexError: 
        return 0
    return count

# create a list of the indicies at which a character occurs
def index_instances(char_list, find):
    try:
        instances = []
        for i in range(len(char_list)):
            if char_list[i] == find:
                instances.append(i)
            else:
                pass 
    except ValueError or IndexError:
        return []
    return instances 
    
# allow find and replacement by replace all
def replace_all(char_list, find, replace):
    try:
        for i in range(len(char_list)):
            if char_list[i] == find:
                char_list[i] = replace
            else:
                pass
    except ValueError or IndexError:
        return ['Err']
    return char_list
        
# allow find and replacement by a streak of values
def replace_streak(char_list, find, replace, start, number):
    try:
        indicies = index_instances(char_list, find)
        for i in range(number):
            main_index = indicies[start + i - 1]
            char_list[main_index] = replace
    except (ValueError, IndexError):
        return char_list
    return char_list

# allow find and replacement by an individual instance
def replace_specific(char_list, instance, find, replace):
    try:
        indicies = index_instances(char_list, find)
        main_index = indicies[instance - 1]
        char_list[main_index] = replace
    except (ValueError, IndexError):
        return char_list
    return char_list

# allow insertion to a given location in the string
def insert_text(char_list, after_char, after_instance, text):
    try:
        indicies = index_instances(char_list, after_char)
        insert_index = indicies[after_instance - 1]
        insert_index += 1
        char_list.insert(insert_index, text)
    except (ValueError, IndexError):
        return char_list
    return char_list

# allow deletion to a given location in the string
def delete_text(char_list, after_char, after_instance, num_words):
    try:
        # Adjust for space handling
        if after_char == " ":
            adder = 1
        else:
            adder = 0
        
        # Get indices of instances
        indices = index_instances(char_list, after_char)
        
        # Get the starting index
        start_index = indices[after_instance - 1] + 1
        
        # Initialize counters
        words_deleted = 0 + adder
        
        while words_deleted <= num_words:
            if start_index >= len(char_list):
                break
            character = char_list[start_index]
            
            # Delete character
            del char_list[start_index]
            
            # Check if character is a word boundary
            if character == " " or character == "\n":
                words_deleted += 1
        
        # Add a space at the end of the deleted portion
        char_list.insert(start_index, ' ')
        
    except (ValueError, IndexError):
        return char_list
    return char_list

# redefine the original image under default and resized dimensions
image_original = image
image_new = cv2.resize(image_original, [1280, 720])
image_new = cv2.cvtColor(image_new, cv2.COLOR_BGR2RGB)

# assign the RGB values from the recolored, scaled image
r = image_new[:,:,0]
g = image_new[:,:,1]
b = image_new[:,:,2]

# perform a squared average of the RGB values for a "background" color
sum_r = np.array(0, dtype = np.float64)
sum_g = np.array(0, dtype = np.float64)
sum_b = np.array(0, dtype = np.float64)

for i in range(r.shape[1]):
    for j in range(r.shape[0]):
        sum_r += r[j,i] ** 2
        sum_g += g[j,i] ** 2
        sum_b += b[j,i] ** 2
        
sum_r /= ((r.shape[0]) * (r.shape[1]))
sum_g /= ((r.shape[0]) * (r.shape[1]))
sum_b /= ((r.shape[0]) * (r.shape[1]))

avg_r = m.sqrt(sum_r)
avg_g = m.sqrt(sum_b)
avg_b = m.sqrt(sum_g)

# assign the average RGB value to a tuple
avg_color = (avg_r, avg_g, avg_b)

# ratio of original to scaled image for bounding boxes
y_1, x_1, channels = image_original.shape
y_2, x_2, channels = image_new.shape

# the pytesseract module has a class for treating each word of detected text as an object
instance = pytesseract.image_to_data(image_original, output_type=Output.DICT)
n_boxes = len(instance['level'])

# iterate through each text box attribute the class made
for i in range(n_boxes):
    
    # use 70% confidence to filter the massive boxes
    if instance['conf'][i] > 70:                                                                                    
        
        # box dimensions
        x, y, w, h = instance['left'][i], instance['top'][i], instance['width'][i], instance['height'][i]

        # scale to new image
        x *= x_2 / x_1
        y *= y_2 / y_1
        w *= x_2 / x_1
        h *= y_2 / y_1

        # Draw bounding boxes and color them with the "background" color
        cv2.rectangle(image_new, (int(x), int(y)), (int(x + w), int(y + h)), avg_color, 3)
        for j in range(int(w)):
            for k in range(int(h)):
                image_new[int(k+y),int(j+x)] = avg_color
        
        # print the confidence level above each box (TEMPORARY)
        #confidence = "Confidence: " + str(instance['conf'][i]) + " Text: " + instance['text'][i]
        #cv2.putText(image_new, confidence, (int(x),int(y - h /2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)

# Display the original image with bounding boxes and recolor next to the original
fig, ax = plt.subplots(1,2, figsize = (10, 10))
ax[0].imshow(image_text)
ax[1].imshow(image_new)
plt.show()


