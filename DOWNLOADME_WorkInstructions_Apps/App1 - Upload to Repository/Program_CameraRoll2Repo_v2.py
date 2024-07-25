# Program_CameraRoll2Repo_v2.py
# Definitions for Back-End Functionality of File Uploader App                                                        SEE ISOLATED COMMENTS FOR QUICK EDITS
# Mirko Glavan
# 5/20/2024
#                                                                                       ISOLATED COMPONENTS REQUIRE MODIFICATION FOR SOME ASPECTS OF RECYCLING
#
# Documentation Provided
#
# NOTE: possible logic error that can persist is uploading the same
# file in different runs. This will not be problematic when addressed by
# synthesis method. all other errors, mainly relating to excessive
# runtime or flawed input are addressed by popups. 
#
# Connection to github errors can also occur. these can be resolved by running the app again

# begin by setting the directory to where all app launch files are stored                                                   SET DIRECTORY
import os
directory = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\File Locator Project\\Project Step One'
try:
    os.chdir(directory)
except OSError:
    print("Error: Directory not Set Up")

# imports for GUI setup
from github import Github, UnknownObjectException       #                                                                  ENSURE ALL MODULES DOWNLOADED VIA PIP
import easygui
import kivy
from kivy.app import App
from kivy.uix.label import Label
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

# remove buggy red-dot emulators (Multitouch is On-Demand)
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# access the repository
g = Github('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')
current_user = g.get_user()
repo = g.get_repo('mglavan07/WorkInstructions')

# create a class for storing all relevant global app metrics during runtime
class AppData:
    # intialize all variables to default
    def __init__(self):
        self.files = []
        self.count = 0
        self.branch = None
        self.folder = None
        self.index = 0
        self.press_count = 0
        self.submit_count = 0
        self.foldersel_count = 0
        
    # update file count and file list when called
    def update_data(self, new):
        self.files = AppData.append_new(new, self.files)
        self.count = len(self.files)

    # send files to GitHub when called
    def send_files(self):
        upload_in_progress_popup()
        i = self.index
        for local_file in self.files:
            AppData.send_to_repo(self.folder, local_file, self.branch, AppData.git_filename(local_file, i, self.folder))
            i = i + 1

    # create a conventioned GitHub filename when called as a static
    @staticmethod
    def git_filename(filename, index, folder):
        git_filetype = '.jpg' # HARD CODED NAMING CONVENTION                                                           GITHUB NAMING HERE (extension)
        git_prefix = 'annotated_image'  # HARD CODED NAMING CONVENTION                                                 GITHUB NAMING HERE (prefix)
        file_index = str(index) 
        filename = git_prefix + "_" + folder + "_" + file_index + git_filetype
        return(filename)

    # prepares and moves to the repository when called as a static
    @staticmethod
    def send_to_repo(folder, local_file, branch, file_name_git):
        g = Github('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')
        current_user = g.get_user()
        repo = g.get_repo('mglavan07/WorkInstructions')
        
        repo_path = folder + '/' + file_name_git
        message = "importing files from CameraROll2Repo App"
        with open(local_file, "rb") as image:
            f = image.read()
            image_byte = bytearray(f)
        repo.create_file(repo_path, message, bytes(image_byte), branch)
        g.close()

    # filters duplicates in the same upload when called as a static
    # NOTE: duplicates may be uploaded in different app launches if desired
    @staticmethod
    def append_new(new_vals, old_vals):
        try:
            for new in new_vals:
                duplicate = False
                for old in old_vals:
                    if new == old:
                        duplicate = True
                if duplicate:
                    pass
                else:
                    old_vals.append(new)
            return old_vals
        except TypeError:
            pass

# instance of the AppData
data = AppData()

# define popups for common user errors
def exit_popup():
    # check if the user really wants to exit
    try:
        choice = easygui.boolbox(msg = 'Are you sure you want to exit? All files will be lost and app data will reset...', title = 'Exit Confirmation',
                                 choices = ('Exit', 'Go Back'))
        return choice
    except ValueError:
        return False
    
def double_button_press_popup():
    # stops the user from double refreshing (count resets if page is left)
    easygui.msgbox(msg= 'Duplicate request detected. App response time was conserved. \n\nIf duplicate action was intentional, press "Back" and try again.',
                   title = 'Excessive Input Warning', ok_button = "OK")
    
def double_folder_press_popup():
    # check if the user really wants to select a new folder
    try:
        choice = easygui.boolbox(msg = 'Are you sure you want to select another folder? Repetitive requests may slow down the Python Shell...',
                                 title = 'Selection Confirmation', choices = ('Proceed', 'Cancel'))
        return choice
    except ValueError:
        return False
    
def upload_in_progress_popup():
    # has message telling user uploads are in progress and not to close window
    # THIS PROGRAM DID NOT USE THE PROGRESS BAR AS IT IS A MEMBER OF THE tkinter FAMILY.
    # adding a progress bar, or updated message beyond a popup message can be added via its own class                     # WINDOWS OS PROGRESS BAR CAN GO HERE
    easygui.msgbox(msg= 'File Upload Initiated. Please do not close the window until prompted.',
                   title = 'File Upload Notification', ok_button = "OK")

def no_files_popup():
    # prevents the user from submitting no files
    # will stop user from clicking "submit" with this condition (can proceed up to this point)
    easygui.msgbox(msg= 'No files have been attatched. Navigate "Back" or close the app. ', title = 'No Files Warning', ok_button = "OK")

def no_branch_selected_popup():
    # error when pressed no branch selected
    easygui.msgbox(msg= 'No Branch was selected. Press "Back" and select a Branch\n\nOr, refresh the Dropdown by pressing "Refresh Dropdown". ',
                   title = 'No Branch Warning', ok_button = "OK")

def no_folder_selected_popup():
    # prevents user from not selecting a folder
    easygui.msgbox(msg= 'No Folder was selected. Press "OK" and select a Folder. ', title = 'No Folder Warning', ok_button = "OK")


def non_png_popup():
    # warns users against uploading non PNG images (give contact if needed change)
    try:
        choice = easygui.boolbox(msg = 'One of the selected files was not a JPG image. All files will be uploaded to GitHub as JPG. Submit Anyway? \n\nIf issue persists, please contact Mirko Glavan',
                                 title = 'Non-JPG Warning', choices = ('Proceed', 'Cancel'))
        return choice
    except ValueError:
        return False
    
def main_branch_popup():
    # prevents a user from uploading to main branch
    easygui.msgbox(msg= 'Main Branch should not be populated except for manual commits. \n\nIf "main" needs to be populated please contact Mirko Glavan for a manual GitHub commit.',
                   title = 'Main Branch Warning', ok_button = "OK")  


def submit_confirmation():
    # clarifies submission
    # if user still sends to wrong place, importhere as a branch will allow for the user to easily delete the change, simply don't push the commit
    try:
        if data.count == 1:
            noun = 'file'
        else:
            noun = 'files'
        choice = easygui.boolbox(msg = 'Are you sure you want to submit files to the repository?\n\n' + str(data.count) + ' '+noun+' will be sent to ' + data.branch + "/" + data.folder,
                                 title = 'Submit Confirmation', choices = ('Submit', 'Go Back'))
        return choice
    except ValueError:
        return False

# welcome window class and methods
class WelcomeWindow(Screen):

    # close button
    def close(self):
        if exit_popup():
            App.get_running_app().stop()
            Window.close()
        else:
            pass
        
# start window class and methods
class StartWindow(Screen):
    dropbox_input = []
    num_files = StringProperty()
    files_print = StringProperty()

    # default text
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files_print = 'Selected Files for Upload: '
        self.num_files = 'File Count: ' + str(data.count)
        
    # close button
    def close(self):
        if exit_popup():
            App.get_running_app().stop()
            Window.close()
        else:
            pass
    
    # file dropbox
    def get_files(self):
        file_paths = easygui.fileopenbox(default = '/', multiple = True)
        try:
            files = []
            nonPNG = False
            for file in file_paths:
                files.append(file)
        
            for name in files:
                extension = name[-4:].lower() # LOOK AT LAST 4 LETTERS HARD CODED                                                      # EXTENSION FILTERING HERE
                if extension != '.jpg': # NEEDS TO BE '.jpg' HARD CODED
                    nonPNG = True
                    
            if nonPNG:
                if non_png_popup():
                    self.dropbox_input = files
                else:
                    pass  
            else:
                self.dropbox_input = files
            StartWindow.update_text_data()
        except TypeError:
            pass

    # update text on page
    def update_text_data(self):
        data.update_data(self.dropbox_input)
        self.num_files = "File Count: " + str(data.count)
        self.files_print = 'Selected Files for Upload: '
        for file in data.files:
            self.files_print = self.files_print + "\n" + file

# branch window class and methods
class BranchWindow(Screen):
    branch_header_text = StringProperty()
    branch_spinner_text = StringProperty()

    # default text
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.branch_header_text = "Select a Destination Branch Below "
        self.branch_spinner_text = 'Browse Available: '

    # close button
    def close(self):
        if exit_popup():
            App.get_running_app().stop()
            Window.close()
        else:
            pass

    # returns all github branches when called as a static
    @staticmethod
    def get_branches():
        g = Github('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')
        current_user = g.get_user()
        repo = g.get_repo('mglavan07/WorkInstructions')
        branches = []
        for branch in repo.get_branches():
            branches.append(branch.name)
        g.close()
        return(branches)

    # branches dropdown
    def branches_selection(self, value):
        if value == "main":
            main_branch_popup()
            self.branch_spinner_text = 'Browse Available: '
            
        else:
            self.branch_header_text = "Selected Branch: " + value
            data.branch = value

# folder window class and methods
class FolderWindow(Screen):
    folder_header_text = StringProperty()
    folder_options = ListProperty()
    folder_spinner_text = StringProperty()

    # default text
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.folder_header_text = "Select a Destination Folder Below "
        self.folder_options = ["No Branch Selected Yet"]
        self.folder_spinner_text = "Browse Available: "

    # close button
    def close(self):
        if exit_popup():
            App.get_running_app().stop()
            Window.close()
        else:
            pass

    # refresh button
    def refresh_button(self):
        num_refreshes = data.press_count
        if num_refreshes == 0:
            self.folder_options = FolderWindow.get_folders()
            data.press_count = data.press_count + 1
        else:
            double_button_press_popup()

    @staticmethod
    # resets counts associated with popups
    def reset_button_count():
        data.press_count = 0
        data.submit_count = 0
        data.foldersel_count = 0

    # returns all folders in the branch when called as a static
    @staticmethod
    def get_folders():
        try:
            g = Github('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')
            current_user = g.get_user()
            repo = g.get_repo('mglavan07/WorkInstructions')
            contents = repo.get_contents("", ref = data.branch)
            folders = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    folders.append(file_content.name)
            g.close()
            return(folders)
        except AssertionError:
            g.close()
            return ["No Folders Exist in this Branch"]

    # folder dropdown
    def folder_selection(self, value):
        select_count = data.foldersel_count
        if value == "No Branch Selected Yet" or value == "No Folders Exist in this Branch":
            no_branch_selected_popup()
            self.folder_spinner_text = "Browse Available: "
        else:
            if select_count <= 1: # USER GETS 1 RE-SELECTION OF FOLDER BEFORE GETTING POPUP
                self.folder_header_text = "Selected Folder: " + value
                data.folder = value
                FolderWindow.countfiles()
                data.foldersel_count = data.foldersel_count + 1
            else:
                if double_folder_press_popup():
                    self.folder_header_text = "Selected Folder: " + value
                    data.folder = value
                    FolderWindow.countfiles()
                    data.foldersel_count = data.foldersel_count + 1
                else:
                    pass
                    

    # returns number of files in a folder to allow multiple uploads to one folder 
    @staticmethod
    def countfiles():
        g = Github('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')
        current_user = g.get_user()
        repo = g.get_repo('mglavan07/WorkInstructions')
        contents = repo.get_contents(data.folder, ref = data.branch)
        data.index = len(contents)
        g.close()

    # next button
    @staticmethod
    def folders_next_button():
        if data.folder == None:
            no_folder_selected_popup()
            return False
        else:
            if data.count == 0:
                no_files_popup()
                return False
            else:
                num_submits = data.submit_count
                if submit_confirmation():
                    if num_submits == 0:
                        data.send_files()
                        data.submit_count = data.submit_count + 1
                        return True
                    else:
                        double_button_press_popup()
                        return False
                else:
                    return False

    @staticmethod
    # determines if the program has submitted or not before transition
    def has_submitted():
        count = data.submit_count
        if count == 0:
            return False
        elif count == 1:
            return True

# close window class and methods
class CloseWindow(Screen):
    # close button
    def close(self):
        App.get_running_app().stop()
        Window.close()

# allow for multiple windows
class WindowManager(ScreenManager):
    pass

# locate the .kv file
kv = Builder.load_file("AppStructure_CameraRoll2Repo_v2.kv")

# define an app class as the .kv file instance as a child of App
class ImageApp(App):
    def build(self):
        return kv
        
# run an instance of the app
if __name__ == "__main__":
    ImageApp().run()

# close the repo
g.close()
    




