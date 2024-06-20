# Program_InstructionSynthesis.py
# Definitions for Back-End Functionality of Instruction Synthesis App                                                        SEE ISOLATED COMMENTS FOR QUICK EDITS
# Mirko Glavan
# 5/29/2024
#                                                                                           ISOLATED COMPONENTS REQUIRE MODIFICATION FOR SOME ASPECTS OF RECYCLING
#
# Documentation Provided
#
# 
#

# begin by importing the modules necessary for image processing and file storage                                                   SET DIRECTORY
import os
import requests
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import time
from  fpdf import FPDF
import matplotlib.pyplot as plt

# set the directory to where all app launch files are stored 
directory = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\File Locator Project\\Project Step One'
try:
    os.chdir(directory)
except OSError:
    print("Error: Directory not Set Up")

# import modules for GUI setup
from github import Github, UnknownObjectException       #                                                              ENSURE ALL MODULES DOWNLOADED VIA PIP
import easygui
import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import ListProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView

# import modules for AI text extraction and Machine Learning
from pytesseract import *
import numpy as np
import math as m

# remove buggy red-dot emulators (Multitouch is On-Demand)
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# define popup windows

# confirm exits
def exit_popup():
    try:
        choice = easygui.boolbox(msg = 'Are you sure you want to exit? All files will be lost and app data will reset...', title = 'Exit Confirmation',
                                 choices = ('Exit', 'Go Back'))
        return choice
    except ValueError:
        return False

# 404 error on GitHub URL
def url_error_404(lost):
    easygui.msgbox(msg= f'404 Not Found Error with GitHub URL. Check the URL concatenation and try again. \n\nExcraction of {lost} was aborted. Close the aplication if necessary.\n\nIf error persists, contact Mirko Glavan for updated access token.',
                   title = '404 GitHub URL Error', ok_button = "OK")

# no images in a folder
def no_images():
     easygui.msgbox(msg= 'The provided folder is empty. Check that Step 1 was completed and pushed to "main" and try again.',
                   title = 'Empty Folder Warning', ok_button = "OK")
    
# GitHub connection error
def githib_disconnect():
    easygui.msgbox(msg= 'Error connecting to GitHub. Check internet stability and try again.',
                   title = 'Connection Error', ok_button = "OK")

# nonexisting folder
def folder_does_not_exist():
    easygui.msgbox(msg= 'The typed folder does not exist. Check case and try again.',
                   title = 'Folder Error', ok_button = "OK")

# no input given
def no_typed_input():
    easygui.msgbox(msg= 'No Typed Input. Enter a value and refresh again',
                   title = 'Input Warning', ok_button = "OK")

# runtime warning
def runtime_warning():
    try:
        choice = easygui.boolbox(msg = 'The following process will implement either Machine Learning, AI, or Image Processing and may take up to 5 minutes to run. \n\nContinue?',
                                 title = 'Runtime Warning',
                                 choices = ('Continue', 'Close App'))
        return choice
    except ValueError:
        return False

# assembly folder does not start with 2/5/7
def folder_nameerror():
    try:
        choice = easygui.boolbox(msg = 'The selected folder does not start with 7, 5, or 2. The app detects it not to be an assembly folder. \n\nOverride?',
                                 title = 'Name Convention Warning',
                                 choices = ('Override', 'Back'))
        return choice
    except ValueError:
        return False

# no folder passed
def no_folder_popup():
    easygui.msgbox(msg= 'Cannot Proceed Without a Folder. Try Again',
                   title = 'Folder Error', ok_button = "OK")

# preview a step outside the bounds of the instructions
def display_bounds_popup(max_step):
    easygui.msgbox(msg= f'Cannot proceed beyond the final step ({max_step}) or below 0. Try Again',
                   title = 'Display Bounds Error', ok_button = "OK")

# over 180 characters sent to the insert function
def char_limit_popup():
    easygui.msgbox(msg= '180 character limit exceeded. A portion of the inserted text was sliced.\n\n' + r'If inserting again, begin input with the \n new line keyphrase.',
                   title = 'Character Overflow Warning', ok_button = "OK")

    
# access the GitHub repository
try:
    g = Github('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')                  
    current_user = g.get_user()
    repo = g.get_repo('mglavan07/WorkInstructions')
except (AssertionError, socket.gaierror):
    github_disconnect()

# allow for multiple windows
class WindowManager(ScreenManager):
    pass

# class for storage of cross-window image metadata
class AppImageData:

    # initialize default class attributes 
    def __init__(self):
        self.folder = None                      # name of the selected import assembly folder
        self.raw_images = []                    # imported (.png/jpg) files on the GitHub folders stored as file names
        self.image_addresses = []               # local storage addresses for all in raw_images
        self.preprocessed_images = []           # storage of numpy arrays for preprocessed images (cv2)
        self.segmented_images = []              # storage of numpy arrays for segmented images
        self.final_instruction_images = []      # storage of numpy arrays for finalized images with typed instructions pasted
        self.display_step = 1                   # class attribute for step to display in PreviewWindow

    # function that verifies the suffix of a string
    @staticmethod
    def my_endswith(string, ending):
        string_length = len(str(string))
        ending_length = len(str(ending))
        if ending_length > string_length:
            return False
        for i in range(-1, (-1 * ending_length) - 1, -1):
            if list(string)[i] != list(ending)[i]:
                return False
        return True

    # get all images in the selected GitHub converter and fill self.image_addresses by accessing byte content at the GitHub url
    def get_images(self):
        try:
            g = Github('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')
            current_user = g.get_user()
            branch = 'main'
            repo = g.get_repo('mglavan07/WorkInstructions')
            contents = repo.get_contents(self.folder, ref = branch)
            accepted_extensions = [".png", ".jpg"]                                                   # acceptable image file extensions
            for file in contents:
                if file.type == "file":
                    file_name = file.name
                    file_name_lower = file.name.lower()
                    for ext in accepted_extensions:
                        if AppImageData.my_endswith(file_name_lower, ext):
                            self.raw_images.append(file_name)

            if len(self.raw_images) <= 0:
                no_images()
                time.sleep(2)
                g.close()
                App.get_running_app().stop()
                Window.close()
                
            else:
                for name in self.raw_images:                                                       
                    PAT = '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'                                 # separate key for accessing cloud for downloads
                    headers = {
                        'Authorization': f'token {PAT}',
                        'Accept': 'application/vnd.github.v3.raw',
                    }
                    path = self.folder+ '/' + name

                    # Construct the API URL for the file
                    api_url = f'https://api.github.com/repos/mglavan07/WorkInstructions/contents/{path}?ref=main' 
                    url = f'https://raw.githubusercontent.com/mglavan07/WorkInstructions/main/{self.folder}/{name}'     
                    local_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\' + name   # HARD CODED PATH FOR DOWNLOADED FILES TO BE STORED LOCALLY
                    response = requests.get(api_url, headers=headers)
                    if response.status_code == 404 or response.status_code == 400:
                        url_error_404(path)
                    elif response.status_code == 200:
                        with open(local_path, 'wb') as file:
                            file.write(response.content)
                        self.image_addresses.append(local_path)
                g.close()       
        except (AssertionError, socket.gaierror):
            g.close()
            github_disconnect()

    # preprocess the images by bounding and "standardizing" BGR cells around detected text
    def preprocess(self):
        for file in self.image_addresses:
            image = cv2.imread(file)
            
            # redefine the original image under default and resized dimensions
            image_original = image
            image_new = cv2.resize(image_original, [1280, 720])                                                        # 2560x1440 --> 1280x720
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
                if instance['conf'][i] > 70:                                                            # PREPROCESSING C-LEVEL FOR ADJUSTING (70%)
        
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
            self.preprocessed_images.append(image_new)


    # segment the images using the UNET architecture
    def segment(self):
        self.segmented_images = self.preprocessed_images

    # method accessed through AppImageData to combine segmented images with completed text
    def synthesize_instructions(self, texts_list):
        for i, text_str in enumerate(texts_list):
            segmented_img = self.segmented_images[i]

            # add the text to the segmented image
            x_pos, y_pos = 20, 20
            font = cv2.FONT_HERSHEY_COMPLEX
            font_scale = 0.4
            font_color = (0,0,0)
            thickness = 1
            
            # split the string into lines
            lines = text_str.split('\n')

            # find the max width of a line
            text_size = cv2.getTextSize(lines[0], font, font_scale, thickness)[0]
            max_text_w, oneline_height = text_size

            for line in lines:

                # change the maximum width if the line is the longest
                text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
                text_w, oneline_height = text_size

                if text_w > max_text_w:
                    max_text_w = text_w

                # add text
                cv2.putText(segmented_img, line, (x_pos, y_pos), font, font_scale, font_color, thickness, cv2.LINE_AA)
                y_pos += 15

            # textbox rectangle
            x1, y1 = 5,5
            x2 = max_text_w + x_pos + 15
            y2 = y_pos
            cv2.rectangle(segmented_img, (x1,y1), (x2, y2), font_color, thickness)

            # image border
            x3,y3 = 1,1
            y4,x4, channels = segmented_img.shape
            cv2.rectangle(segmented_img, (x3,y3), (x4 - 1, y4 - 1), font_color, thickness)

            
            
            # append to the final instruction images
            self.final_instruction_images.append(segmented_img)

# instance of the AppImageData class
imagedata = AppImageData()

# class for storge of cross-window text metadata                                                         # has dependency on AppImageData instance
class AppTextData:

    # initialize default class attributes 
    def __init__(self):
        self.folder = None              # stores the folder selection
        self.complete_text = []         # stores strings of completed annotation text
        self.raw_text = []              # stores strings of text as extracted via AI: overwritten with saves
        self.iteration_text = None      # temporary text storage pre-save
        self.max_step = 0               # maximum number of steps (number of images)
        self.current_step = 1           # current step for list indexing on edits

    # uses the pytesseract to extract text from all images
    def get_text(self):
        self.max_step = len(imagedata.raw_images)
        for image in imagedata.image_addresses:
            pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'                # locate the tesseract.exe file
            image_open = cv2.imread(image)
            image_text = cv2.resize(image_open, [1280, 720])
            image_text = cv2.cvtColor(image_text, cv2.COLOR_BGR2RGB)
            text_str = pytesseract.image_to_string(image_text)
            text_str = AppTextData.ascii_filter(list(text_str))
            text_str = ''.join(text_str)
            self.raw_text.append(text_str)

        # preprocess images after text has been extracted
        imagedata.preprocess()

    # filters out non-ascii characters from a string and replaces with "error codes"
    @staticmethod
    def ascii_filter(char_list):
        for i in range(len(char_list)):
            try:
                table_val = ord(char_list[i])
                if table_val > 127 or table_val < 0:        # 0-127 are traditional ascii values
                    char_list[i] = '*'                      # error codes -- ensure these are not typed in the annotations
            except TypeError: 
                char_list[i] = '*'
        return char_list

    # count the number of instances of a wrong character in the list
    @staticmethod
    def count_instances(char_list, find):
        try:
            count = 0
            for i in range(len(char_list)):
                if char_list[i] == find:
                    count += 1
                else:
                    pass
        except (ValueError, IndexError): 
            return 0
        return count

    # create a list of the indicies at which a character occurs
    @staticmethod
    def index_instances(char_list, find):
        try:
            instances = []
            for i in range(len(char_list)):
                if char_list[i] == find:
                    instances.append(i)
                else:
                    pass 
        except (ValueError, IndexError):
            return []
        return instances 
                
# instance of the AppTextData classes
textdata = AppTextData() 

# window classes
class WelcomeWindow(Screen):

    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()
    
# folder selection
class StartWindow(Screen):

    # collect properties of the window for manipulating
    folder = ObjectProperty(None)
    folder_options = ListProperty()
    folder_header_text = StringProperty()
    selected_folder = None
    
    # initialize window headers
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder_options = StartWindow.get_folders()
        self.folder_header_text = "Select an Assembly's Folder of Annotated Images"
        self.extract_count = 0
        self.override_choice = False
        self.popped = False

    # on_enter methods function as __init__
    def on_enter(self):
        self.override_choice = False
        self.popped = False

    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()
            
    # dropdown text
    def folder_selection(self, value):
        textdata.folder = value
        imagedata.folder = value
        self.selected_folder = value
        self.folder_header_text = "Selected Assembly Folder: " + self.selected_folder

    # make a dropdown selection and modify app data
    def refresh(self):
        if self.folder.text != '' and self.folder.text != "Quick Search by Assembly Number:":
            if StartWindow.validate_folder(self.folder.text):
                textdata.folder = self.folder.text
                imagedata.folder = self.folder.text
                self.selected_folder = self.folder.text
                self.folder.text = ''
                self.folder_header_text = "Selected Assembly Folder: " + self.selected_folder
            else:
                folder_does_not_exist()
                self.folder_header_text = "Invalid Input. Check Commits to Main"
        else:
            no_typed_input()
            self.folder_header_text = "No Typed or Chosen Selection"

    # get dropdown options
    @staticmethod
    def get_folders():
        try:
            g = Github('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')
            current_user = g.get_user()
            branch = 'main'
            repo = g.get_repo('mglavan07/WorkInstructions')
            contents = repo.get_contents("", ref = branch)
            folders = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    folders.append(file_content.name)
            g.close()
            return folders
        except (AssertionError, socket.gaierror):
            github_disconnect()
            g.close()
            return ['Error. Close the App Now.']

    # return a t/f for the folder existing
    @staticmethod
    def validate_folder(value):
        selection = value
        avail = StartWindow.get_folders()
        valid = False
        for folder in avail:
            if selection == folder:
                valid = True
        return valid

    # gather images and extract text upon changing the window
    def gather_extract_data(self):
        if imagedata.folder == None:
            if not self.popped:
                no_folder_popup()
                self.popped = True
            return False
        elif list(imagedata.folder)[0] != '7' and list(imagedata.folder)[0] != '5' and list(imagedata.folder)[0] != '2' and not self.override_choice:
            if not self.popped:
                self.override_choice = folder_nameerror()
                self.popped = True
            return self.override_choice
        else:
            
            # this function is called twice in the .kv file for the transition: a counter ensures images are only processed once
            self.extract_count += 1
            if self.extract_count <= 1:

                # runtime confirmation
                choice = runtime_warning()
                if not choice:
                        App.get_running_app().stop()
                        Window.close()
                else:
                    # get images from the folder
                    print("[INFO   ] [COLLECTING IMAGES ]")
                    imagedata.get_images()                                 
                    time.sleep(2)

                    # retrieve text from images (also preprocesses)
                    print("[INFO   ] [COLLECTING TEXT ]")
                    textdata.get_text()
                    time.sleep(2)
                    print("[INFO   ] [PREPROCESSING COMPLETE ]")
                    
                    # segment images
                    imagedata.segment()
                    time.sleep(2)
                    print("[INFO   ] [SEGMENTATION COMPLETE ]")
            return True

# text viewing and interation interface
class TextNavWindow(Screen):

    # collect properties of the window for manipulating
    textbox_text = StringProperty()
    progress_text = StringProperty()
    header_text = StringProperty()
        
    # initialize window headers
    def on_enter(self):
        textdata.iteration_text = textdata.raw_text[textdata.current_step - 1] 
        self.textbox_text = "AI Generated Text:\n" + textdata.iteration_text
        self.progress_text = "Show Current Image (Step " + str(textdata.current_step) + "/" + str(textdata.max_step) + ")"
        self.header_text ="Assembly Number: " + imagedata.folder + "  | This Process Will Be Repeated for Each Image (Instruction Step)"

    # launches the indexed image
    @staticmethod
    def launch_image():
        view = imagedata.image_addresses[textdata.current_step - 1]
        view_arr = cv2.imread(view)
        cv2.imshow("Step " + str(textdata.current_step) + " Image Viewer", view_arr)
    
    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()

    # increment the step, move to the next
    def increment_step(self):
        textdata.complete_text.append(textdata.raw_text[textdata.current_step - 1])
        textdata.current_step += 1

    # chose to move to preview or progress 
    def check_complete(self):
        if textdata.current_step > textdata.max_step:
            choice = runtime_warning()
            if choice:

                # synthesize images by placing complete text on a segmented image
                imagedata.synthesize_instructions(textdata.complete_text)
            else:
                App.get_running_app().stop()
                Window.close()   
            return True
        else:
            return False
        
# INSERT text to a string    
class InsertWindow(Screen):

    # collect properties of the window for manipulating
    textbox_text = StringProperty()
    insert_text = ObjectProperty(None)
    after_char = ObjectProperty(None)
    after_inst = ObjectProperty(None)
    
    
    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()
            
    # on_enter methods evaluate as an __init__
    def on_enter(self):
        textdata.iteration_text = textdata.raw_text[textdata.current_step - 1]
        self.textbox_text = "AI Generated Text:\n" + textdata.iteration_text

    # execute the insertion
    def insert_click(self):
        try:
            insert_text = self.insert_text.text
            after_char = self.after_char.text
            after_inst = int(self.after_inst.text)
            textdata.iteration_text = list(textdata.iteration_text)
            textdata.iteration_text = InsertWindow.insert_text(textdata.iteration_text, after_char, after_inst, insert_text)
            textdata.iteration_text = ''.join(textdata.iteration_text)
            self.textbox_text = "AI Generated Text:\n" + textdata.iteration_text
            self.after_char.text = ''
            self.after_inst.text = ''
        except ValueError:
            self.textbox_text = "AI Generated Text:\n" + textdata.iteration_text
            self.after_char.text = ''
            self.after_inst.text = ''
            
    # allow insertion to a given location in the string
    @staticmethod
    def insert_text(char_list, after_char, after_instance, text):
        try:
            # apply a character limit                       overflow control: 180 characters per insert (2 lines), about 16 maximum lines of text (8 inserts) 
            text_list = list(text)
            if len(text_list) > 180:
                text_list = text_list[0:180] #              will come out to about 2 standard complete sentences (about 3-5 instruction phrases)
                char_limit_popup()
            if len(char_list) == 0:
                insert_index = 0
            else:
                text = ' ' + text
                indicies = textdata.index_instances(char_list, after_char)
                insert_index = indicies[after_instance - 1]
                insert_index += 1
            i = 0
            while i < len(text_list) - 1:#                  find newline characters (\n) necessary for preventing overflow in the app and making new pdf paragraphs                   
                if text_list[i] == '\\' and text_list[i+1] == 'n':
                    char_list.insert(insert_index+i, '\n')
                    del text_list[i+1]
                else:
                    char_list.insert(insert_index+i, text_list[i])
                i += 1
            char_list.insert(insert_index+i, text_list[i])
        except (ValueError, IndexError):
            return char_list
        return char_list

    # save the insertion
    def save_insert(self):
        textdata.raw_text[textdata.current_step - 1] = textdata.iteration_text

# DELETE text from a string
class DeleteWindow(Screen):

    # collect properties of the window for manipulating
    textbox_text = StringProperty()
    words_delete = ObjectProperty(None)
    after_char = ObjectProperty(None)
    after_inst = ObjectProperty(None)

    # on_enter methods execute as __init__
    def on_enter(self):
        textdata.iteration_text = textdata.raw_text[textdata.current_step - 1]
        self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text

    # execute a deletion
    def delete_click(self):
        try:
            num_words = int(self.words_delete.text)
            after_char = self.after_char.text
            after_inst = int(self.after_inst.text)
            textdata.iteration_text = list(textdata.iteration_text)
            textdata.iteration_text = DeleteWindow.delete_text(textdata.iteration_text, after_char, after_inst, num_words)
            textdata.iteration_text = ''.join(textdata.iteration_text)
            self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
            self.words_delete.text = ''
            self.after_char.text = ''
            self.after_inst.text = ''
        except ValueError:
            self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
            self.words_delete.text = ''
            self.after_char.text = ''
            self.after_inst.text = ''

    # static method for deletion
    @staticmethod
    def delete_text(char_list, after_char, after_instance, num_words):
        try:
            # Adjust for space handling
            if after_char == " ":
                adder = 1
            else:
                adder = 0
            
            # Get indices of instances
            indices = textdata.index_instances(char_list, after_char)
            
            # Get the starting index
            start_index = indices[after_instance - 1]
            
            # Initialize counters
            words_deleted = 0 + adder
            
            while words_deleted < num_words:
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
    
    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()

    # save the deletion
    def save_delete(self):
        textdata.raw_text[textdata.current_step - 1] = textdata.iteration_text

# REPLACE ALL of a given character in a string
class ReplaceAllWindow(Screen):

    # collect properties of the window for manipulating
    textbox_text = StringProperty()
    find = ObjectProperty(None)
    replace = ObjectProperty(None)

    # on_enter methods evaluate as __init__
    def on_enter(self):
        textdata.iteration_text = textdata.raw_text[textdata.current_step - 1]
        self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text

    # execute the replacement
    def replace_click(self):
        find_char = self.find.text
        replace_str = self.replace.text
        textdata.iteration_text = list(textdata.iteration_text)
        textdata.iteration_text = ReplaceAllWindow.replace_all(textdata.iteration_text, find_char, replace_str)
        textdata.iteration_text = ''.join(textdata.iteration_text)
        self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
        self.find.text = ''
        self.replace.text = ''

    # static method defining replace all
    @staticmethod
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

    # save the replacement 
    def save_replace(self):
        textdata.raw_text[textdata.current_step - 1] = textdata.iteration_text
    
    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()

# REPLACE CONSECUTIVE given characters in a string
class ReplaceStreakWindow(Screen):

    # collect properties of the window for manipulating
    textbox_text = StringProperty()
    find = ObjectProperty(None)
    replace = ObjectProperty(None)
    streak = ObjectProperty(None)
    start_inst = ObjectProperty(None)

    # on_enter methods evaluate as __init__
    def on_enter(self):
        textdata.iteration_text = textdata.raw_text[textdata.current_step - 1]
        self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text

    # save replacement
    def save_replace(self):
        textdata.raw_text[textdata.current_step - 1] = textdata.iteration_text

    # execute the replacement
    def replace_click(self):
        try:
            find_char = self.find.text
            replace_str = self.replace.text
            streak_len = int(self.streak.text)
            start_inst = int(self.start_inst.text)
            textdata.iteration_text = list(textdata.iteration_text)
            textdata.iteration_text = ReplaceStreakWindow.replace_streak(textdata.iteration_text, find_char, replace_str, start_inst, streak_len)
            textdata.iteration_text = ''.join(textdata.iteration_text)
            self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
            self.find.text = ''
            self.replace.text = ''
            self.streak.text = ''
            self.start_inst.text = ''
        except ValueError:
            self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
            self.find.text = ''
            self.replace.text = ''
            self.streak.text = ''
            self.start_inst.text = ''  

    # defines consecutive replacement
    @staticmethod
    def replace_streak(char_list, find, replace, start, number):
        try:
            indicies = textdata.index_instances(char_list, find)
            for i in range(number):
                main_index = indicies[start + i - 1]
                char_list[main_index] = replace
        except (ValueError, IndexError):
            return char_list
        return char_list
    
    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()

# REPLACE ONE character in a string
class ReplaceOneWindow(Screen):

    # collect properties of the window for manipulating
    textbox_text = StringProperty()
    find = ObjectProperty(None)
    replace = ObjectProperty(None)
    inst = ObjectProperty(None)

    # on_enter methods evaluate as __init__
    def on_enter(self):
        textdata.iteration_text = textdata.raw_text[textdata.current_step - 1]
        self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text

    # save the replacement
    def save_replace(self):
        textdata.raw_text[textdata.current_step - 1] = textdata.iteration_text

    # execute the replacement
    def replace_click(self):
        try:
            find_char = self.find.text
            replace_str = self.replace.text
            inst = int(self.inst.text)
            textdata.iteration_text = list(textdata.iteration_text)
            textdata.iteration_text = ReplaceOneWindow.replace_specific(textdata.iteration_text, inst, find_char, replace_str)
            textdata.iteration_text = ''.join(textdata.iteration_text)
            self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
            self.find.text = ''
            self.replace.text = ''
            self.inst.text = ''
        except ValueError:
            self.textbox_text = "AI Extracted Text: \n" + textdata.iteration_text
            self.find.text = ''
            self.replace.text = ''
            self.inst.text = ''

    # static method that defines replacing one character
    @staticmethod
    def replace_specific(char_list, instance, find, replace):
        try:
            indicies = textdata.index_instances(char_list, find)
            main_index = indicies[instance - 1]
            char_list[main_index] = replace
        except (ValueError, IndexError):
            return char_list
        return char_list

    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()

# tracks progress while image text remains to be modified
class ProgressWindow(Screen):

    # collect properties of the window for manipulating
    label_text = StringProperty()

    # on_enter methods evaluate as __init__
    def on_enter(self):
        self.label_text = 'Images Completed: ' + str(textdata.current_step - 1) + '\nImages Remaining: ' + str(textdata.max_step - textdata.current_step + 1)

    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()

# displays a preview of instructions before they are uploaded to GitHub
class PreviewWindow(Screen):

    # collect properties of the window for manipulating
    relaunch_text = StringProperty()

    # on_enter methods evaluate as __init__
    def on_enter(self):
        self.relaunch_text = "Click Here to Launch Step " + str(imagedata.display_step)
        PreviewWindow.launch_image()

    # launch an image
    @staticmethod
    def launch_image():
        view_arr = imagedata.final_instruction_images[imagedata.display_step - 1]
        view_arr = cv2.cvtColor(view_arr, cv2.COLOR_RGB2BGR)
        cv2.imshow("Step " + str(imagedata.display_step) + " Image Viewer", view_arr)

    # proceed to the next step
    def increment_step(self):
        imagedata.display_step += 1
        if imagedata.display_step > textdata.max_step:
            imagedata.display_step -= 1
            self.relaunch_text = "Click Here to Launch Step " + str(imagedata.display_step)
            display_bounds_popup(textdata.max_step)
        else:
            self.relaunch_text = "Click Here to Launch Step " + str(imagedata.display_step)
            PreviewWindow.launch_image()
            

    # return to a previous step
    def decrement_step(self):
        imagedata.display_step -= 1
        if imagedata.display_step <= 0:
            imagedata.display_step += 1
            self.relaunch_text = "Click Here to Launch Step " + str(imagedata.display_step)
            display_bounds_popup(textdata.max_step)
            
        else:
            self.relaunch_text = "Click Here to Launch Step " + str(imagedata.display_step)
            PreviewWindow.launch_image()        

    # publish the instruction images to github as a PDF
    def github_instruction_publish(self):
        try:
            g = Github('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')                  
            current_user = g.get_user()
            repo = g.get_repo('mglavan07/WorkInstructions')

            # make the PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto = True, margin = 15)
            pdf.set_font("Arial", size = 11)

            side_margin = pdf.w * 0.05
            top_margin = pdf.h * 0.025

            page_width = pdf.w - 2 * side_margin
            page_height = pdf.h - 2 * top_margin
            
            # iterate through all the arrays in imagedata.final_instruction_images
            for i, image in enumerate(imagedata.final_instruction_images):
                pil_image = Image.fromarray(image)

                image_width = page_width
                image_height = pil_image.height * (image_width / pil_image.width)
                
                x1 = (page_width - image_width) / 2 + pdf.l_margin
                y1 = (page_height - image_height) / 2 + pdf.t_margin

                temp_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\' + imagedata.folder + str(i + 1) + '.png'
                pil_image.save(temp_path)

                # add them in order to a PDF
                pdf.add_page()             # y = y1
                pdf.image(temp_path, x = x1, y= 2 * top_margin, w=image_width, h=image_height)

                # add the text as well as a typed string on the PDF
                x2 = x1
                y2 = 2 * top_margin + image_height + pdf.h * 0.025
                pdf.set_xy(x2,y2)
                pdf.multi_cell(page_width, 10, txt = 'Written Instructions:\n' + textdata.complete_text[i], align = "L") 

                # step numbers on each page
                pdf.set_y(5)
                pdf.set_x(10)
                pdf.cell(0, 10, f'Step {i + 1}', 0, 0, 'C')
                pil_image.close()
            
            # save the PDF to github
            pdf_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\' + imagedata.folder + '.pdf'
            file_name_git = imagedata.folder + '_WorkInstructions.pdf'
            pdf.output(pdf_path)
            repo_path = imagedata.folder + '/' + file_name_git
            message = "Uploaded Instructions from InstructionSynthesis.py"
            with open(pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            repo.create_file(repo_path, message, pdf_content, branch='main')
            g.close()
        except (AssertionError):
            github_disconnect()
            g.close()

    # functional window close
    def close_button(self):
        choice = exit_popup()
        if choice:
            App.get_running_app().stop()
            Window.close()
    
# closes the app
class CloseWindow(Screen):
    
    # functional window close
    def close_button(self):
        App.get_running_app().stop()
        Window.close()
    

# locate the .kv file
kv = Builder.load_file("AppStructure_InstructionSynthesis.kv")

# define an app class as the .kv file instance as a child of App
class ImageApp(App):
    def build(self):
        return kv
        
# run an instance of the app
if __name__ == "__main__":
    try:
        ImageApp().run()
    except AttributeError:
        print("[CLOSE  ] [CLOSEOUT PRIOR TO RUNTIME ]") 

# close the repo
g.close()
