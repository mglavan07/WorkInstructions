##################################################################
#
# WorkInstruction Maker
# Mirko Glavan
# 6/20/2024
#
# Accesses a folder to generate a manual set of Work Instructions
# Inputs: TXT file of required information
#         JPG images of the build process
# Outputs: A PDF of Work Instructions with convention
#
##################################################################

# Before running, ensure:
# 1) A folder has been made for the assembly (Name = AssemblyNO)
# 2) The folder contains all images (tools, before-after(s)) and a text file
#
#       - The text file may have any name so long as there is only one .txt file in the folder
#       - The tool images must have the same alphapetical order as the list in the .txt file
#           - EX: (.txt) --> Torque Wrench, Torque Seal (.jpg) --> Image_AA (wrench), ImageAB (seal)
#       - The assembly images must have the same aplhabeical order as chronological
#           - EX: Image_AA, Image_AB --> before, after
#
# 3) ONLY The images for tools are cropped down to have no dimensions greater than 1000ptx
# 4) The text file is organized in rows of information:
#
#     1. Tool Names (csv, parallel to tool images)
#     2. Part Name-Numbers (csv)
#     3. Part BOM Numbers (csv, parallel, ascending)
#     4. FOR EACH STEP:
#            n. One Line Description
#            n+1. Operation Time
#            n+2. Operation Parts - BOM
#            n+3. Quantities of each Operation Part (parallel)
#            n+4. Operation Tools
#     5. Repeat Step 4 until complete
# NOTE: NO BLANK LINES. Either just use the Heat Exchanger as a part of (by hand) as a tool

# Import the modules for use in the project
import numpy as np
import math as m
import cv2
import os
import glob
from PIL import Image
from  fpdf import FPDF

# create a class for Images
class AssemblyImages():
    
    # Initialization method -- collect and sort images from the assembly folder
    def __init__(self, path):
        self.folder = path
        self.get_images()
        self.tool_images = []
        self.product_images = []
        self.sort_images()
    
    # Returns a list of image arrays from the specified folder
    def get_images(self):
        
        # Ensure the folder path ends with a slash
        self.folder = os.path.join(self.folder, '')
    
        # Use glob to find all .jpg files in the folder
        self.all_images = glob.glob(os.path.join(self.folder, '*.jpg'))

    # Uses a full self.all_images to separate image arrays into tools and assemblies
    def sort_images(self):

        # catch the case of having no images in the folder
        try:

            # images sorted by size
            for address in self.all_images:
                img = cv2.imread(address)
                rows, cols, channels = img.shape

                # by default images are either 3264x1836 or 2560x1440. Anything that is this size is uncropped.
                if (cols == 3264 or cols == 2560) and (rows == 1836 or rows == 1440):
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)                                                                 # Recolor the image to RGB scheme
                    self.product_images.append(img)

                # if not the default size, it must have been cropped hence it is a tool
                else:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)                                                                 # Recolor the image to RGB scheme
                    self.tool_images.append(img)
                    
        except TypeError:
            print('No Images in the Folder. Please Try Again.')

# create a class for Text
class AssemblyText():

    # Initialization method -- collect and sort text from the assembly folder
    def __init__(self, path):
        self.folder = path
        self.get_text()
        self.tool_names = []
        self.part_names = []
        self.bom_locations = []
        self.operation_descriptions = []
        self.operation_times = []
        self.operation_tools = []
        self.operation_parts = []
        self.part_quantities = []
        self.operation_bom_parts = []
        self.sort_text()

    # Returns an array of words -- rows -> lines, cols -> words 
    def get_text(self):
        
        # Ensure the folder path ends with a slash
        self.folder = os.path.join(self.folder, '')
    
        # Use glob to find all .jpg files in the folder
        self.all_text = glob.glob(os.path.join(self.folder, '*.txt'))[0]                                                    # Take index 0 assuming only 1 txt file

        # assign all text to a local variable
        with open(self.all_text, 'r') as textfile:
            textfile_lines = textfile.readlines()

        # remove whitespace and newline characters from each line and overwrite the class attribute
        overwrite = []
        for line in textfile_lines:
            line_text = line.strip()
            overwrite.append(line_text)

        # execute the overwrite after the execution of the for loop
        self.all_text = overwrite
        
    # Uses a full self.all_text to separate the text into groups of information for the class
    def sort_text(self):
        try:

            # the first line is all the tool names (CSV, parallel to tool images)
            self.tool_names = self.all_text[0].split(',')

            # the second line is all the Part Names hyphenated before the its Part Number (CSV)
            self.part_names = self.all_text[1].split(',')

            # the third line are the ascending BOM numbers for each Part. This is assumed to be parallel to the second line (CSV)
            self.bom_locations = self.all_text[2].split(',')

            # each line starting with the fourth will have four lines for each operation 
            i = 3
            while i < len(self.all_text):

                # the first line is the description
                if i % 5 == 3:
                    self.operation_descriptions.append(self.all_text[i])

                # the second line is the operation time
                elif i % 5 == 4:
                    self.operation_times.append(self.all_text[i])

                # the third line is the #BOM parts
                elif i % 5 == 0:
                    self.operation_bom_parts.append(self.all_text[i])

                    # fill also the operation part names
                    bom_parts = self.all_text[i].split(',')
                    part_names = ''

                    # the part name lies at the #BOM / 10 - 1 index in the parallel list
                    for bom in bom_parts:
                
                        name_index = int(int(bom) / 10 - 1)
                        part_names = part_names + self.part_names[name_index] + ','
                        
                    # remove the last comma and append 
                    part_names = part_names[:-1]
                    self.operation_parts.append(part_names)

                # the fourth line is quantities
                elif i % 5 == 1:
                    self.part_quantities.append(self.all_text[i])

                # the fifth line is the required tools
                else:
                    self.operation_tools.append(self.all_text[i])

                # increment while loop
                i += 1

        # catch empty text file case
        except IndexError:
            print("Blank or Missing Text File. Try Again.")

# define the folder's path
folder_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\2597195'                                             # Hardcoded Folder Location

# create instances of the Image and Text Classes
imagedata = AssemblyImages(folder_path)
textdata = AssemblyText(folder_path)

# create a class for a Standard PDF
class StandardPDF(FPDF):

    # Initialization method -- stores the page count as well as the maximum number of pages
    def __init__(self, orientation='P', unit='mm', format='A4', operations_count = None, tools_count = None, path = None):
        super().__init__(orientation, unit, format)

        self.total_pages = operations_count + tools_count
        self.current_operation = 1
        self.folder_path = path
        self.assembly_number = 'None Found'
        self.page_number = 0
        self.remaining_operations = operations_count
        self.remaining_tools = tools_count
        self.date = '07-11-2024'
        self.accumulated_time = 0
        self.seen_tools = 0

        # Control to show or hide header and footer
        self.show_header_footer = True
        self.tool_pages = True
        self.operation_pages = False

        # Page Breaks
        self.set_auto_page_break(auto = True, margin = 15)

        # Margins (Manual)
        self.side_margin = self.w * 0.05
        self.top_margin = self.h * 0.075

        self.page_width = self.w - 2 * self.side_margin
        self.page_height = self.h - 2 * self.top_margin

    # Headers for all non-title pages
    def header(self):
        if self.show_header_footer:

            # Gather the HYDAC Logo and Cooler Code
            logo_image_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\AVIX-WorkInstruction Parallel\\HYDAC_LOGO.png'

            # Place the Logo at the Top
            logo_img = cv2.imread(logo_image_path)
            logo_img = cv2.cvtColor(logo_img, cv2.COLOR_BGR2RGB)

            rows, cols, channels = logo_img.shape
            aspect_ratio = cols / rows

            # reshape the image to have height of 0.15*page_height and keep aspect ratio
            image_h = 0.15 * self.page_height
            image_w = aspect_ratio * image_h
            logo_img = cv2.resize(logo_img, [int(image_w), int(image_h)])

            # dimensions are measured from the top-left of cell, from the top-left of page
            cell_x, cell_y = self.side_margin + (self.page_width - image_w) / 2 , self.top_margin
            cell_w, cell_h = image_w, image_h
            
            self.set_xy(cell_x, cell_y)
            self.set_font('Arial', '', 48)
            self.cell(cell_w, cell_h, '', 1, 0, 'C')

            # save images to a temporary path to allow for PDF upload
            pil_img = pil_img = Image.fromarray(logo_img)
            temp_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\logo_image.png'
            pil_img.save(temp_path)
            self.image(temp_path, cell_x+5, cell_y+5/aspect_ratio, cell_w - 10, cell_h - 10 / aspect_ratio)
            pil_img.close()

            # make left corner box
            cell_x, cell_y = self.side_margin, self.top_margin
            self.set_xy(cell_x, cell_y)
            cell_w, cell_h = (self.page_width - image_w) / 2, cell_h
            self.set_font('Arial', '', 12)
            self.cell(cell_w, cell_h, txt='PYTHON Work Instrunctions', border=1, ln=0, align='C', fill=False)

            # make right corner box
            cell_x, cell_y = self.side_margin + (self.page_width - image_w) / 2 + image_w , cell_y
            self.set_xy(cell_x, cell_y)
            cell_w, cell_h = (self.page_width - image_w) / 2, cell_h
            self.set_font('Arial', '', 12)
            self.cell(cell_w, cell_h, txt=f'', border=1, ln=0, align='C', fill=False)

            cell_x, cell_y = self.side_margin + self.page_width - cell_w + 3, cell_y
            self.set_xy(cell_x, cell_y)
            text = f'\nCooler Code:\n{self.assembly_number}'
            self.multi_cell(cell_w - 5, 8, text, border=0, align='L', fill=False)

            # execute a footer as well (not automatic f_x call)
            self.custom_footer()

    # Footers for all non-title pages
    def custom_footer(self):
        if self.show_header_footer:

            # Unique footer for tool pages
            if self.tool_pages:

                # Gather Date and Page Number (done via class attribute)

                # Make Issued Box
                cell_x, cell_y = self.side_margin, self.top_margin + self.page_height - self.page_height * 0.15
                cell_w, cell_h = self.page_width / 2, self.page_height * 0.075
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt='Issued By: Mirko Glavan', border=1, ln=0, align='C', fill=False)

                # Make Approved Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = cell_w, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt="Approved By:", border=1, ln=0, align='L', fill=False)

                # Make Signed Box
                cell_x, cell_y = self.side_margin, cell_y + cell_h
                cell_w, cell_h = self.page_width / 3, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt='Signed:', border=1, ln=0, align='L', fill=False)

                # Make Date Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = self.page_width / 3, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt=f'File D.O.B: {self.date}', border=1, ln=0, align='C', fill=False)

                # Make Page Number Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = self.page_width / 3, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt=f'Page: T - {self.page_number} / {self.total_pages}', border=1, ln=0, align='C', fill=False)

            # Unique footer for operation pages
            elif self.operation_pages:

                # Gather Date and Page Number (done via class attribute)

                # Make Step Time Box
                cell_x, cell_y = self.side_margin, self.top_margin + self.page_height - self.page_height * 0.15
                cell_w, cell_h = self.page_width / 3, self.page_height * 0.075
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt=f'Operation Time: {round(float(textdata.operation_times[self.current_operation - 1]), 3)} sec', border=1, ln=0, align='C', fill=False)
                self.accumulated_time = round(self.accumulated_time + float(textdata.operation_times[self.current_operation - 1]), 3)

                # Make Issued Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = cell_w, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt="Issued By: Mirko Glavan", border=1, ln=0, align='C', fill=False)

                # Make Approved Box
                cell_x, cell_y = cell_x + cell_w, cell_y 
                cell_w, cell_h = cell_w, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt='Approved By:', border=1, ln=0, align='L', fill=False)

                # Make Accumulated Time Box
                cell_x, cell_y = self.side_margin, cell_y + cell_h
                cell_w, cell_h = self.page_width / 3, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt=f'Total Time: {self.accumulated_time} sec', border=1, ln=0, align='C', fill=False)

                # Make Signed Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = 2 * self.page_width / 9, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt=f'Signed:', border=1, ln=0, align='L', fill=False)

                # Make Date Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = cell_w, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 10)
                self.cell(cell_w, cell_h, txt=f'File D.O.B: {self.date}', border=1, ln=0, align='C', fill=False)

                # Make Page Number Box
                cell_x, cell_y = cell_x + cell_w, cell_y
                cell_w, cell_h = cell_w, cell_h
                self.set_xy(cell_x, cell_y)
                self.set_font('Arial', '', 12)
                self.cell(cell_w, cell_h, txt=f'Page: OP - {self.page_number} / {self.total_pages}', border=1, ln=0, align='C', fill=False)

    # Make a title page
    def title_page(self):

        # Disable Header and Footer
        self.show_header_footer = False

        # Add page
        self.add_page()

        # need to gather the HYDAC Logo and PN
        self.get_assembly_number()
        logo_image_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\AVIX-WorkInstruction Parallel\\HYDAC_LOGO.png'

        # Place the Logo at the Top
        logo_img = cv2.imread(logo_image_path)
        logo_img = cv2.cvtColor(logo_img, cv2.COLOR_BGR2RGB)

        rows, cols, channels = logo_img.shape
        aspect_ratio = cols / rows

        # dimensions are measured from the top-left of cell, from the top-left of page
        cell_w, cell_h = self.page_width, self.page_width / aspect_ratio
        cell_x, cell_y = self.side_margin, self.top_margin

        logo_img = cv2.resize(logo_img, [int(cell_w), int(cell_h)])

        self.set_xy(cell_x, cell_y)
        self.set_font('Arial', '', 48)
        self.cell(cell_w, cell_h, '', 0, 0, 'C')

        # save images to a temporary path to allow for PDF upload
        pil_img= Image.fromarray(logo_img)
        temp_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\logo_image.png'
        pil_img.save(temp_path)
        self.image(temp_path, cell_x, cell_y, cell_w, cell_h)

        # "Standard Assembly Work Instructions" Label
        cell_x, cell_y = cell_x, cell_y + cell_h + 10
        self.set_xy(cell_x, cell_y)
        cell_w, cell_h = self.page_width, self.page_height * 0.1
        self.set_font('Arial', '', 28)
        self.cell(cell_w, cell_h, txt='Standardized Assembly Work Instructions', border=0, ln=0, align='C', fill=False)
        
        # "Cooler Code: [PN]" Label
        cell_x, cell_y = cell_x, cell_y + cell_h + 15
        self.set_xy(cell_x, cell_y)
        cell_w, cell_h = self.page_width, self.page_height * 0.075
        self.set_font('Arial', '', 24)
        self.cell(cell_w, cell_h, txt=f'Cooler Code: {self.assembly_number}', border=0, ln=0, align='C', fill=False)

        # "Composed in Python by Mirko Glavan" Label
        cell_x, cell_y = cell_x, self.top_margin + self.page_height - 15
        self.set_xy(cell_x, cell_y)
        cell_w, cell_h = self.page_width, cell_h
        self.set_font('Arial', '', 18)
        self.cell(cell_w, cell_h, txt=f'This Document Was Composed in Python by Mirko Glavan', border=0, ln=0, align='C', fill=False)

        # Close the image and increment the page number
        pil_img.close()
        self.page_number += 1

    # Make a standard page for tools
    def tool_page(self):

        # Add Page - Header and Footer Automatically Applied
        self.add_page()

        # need to gather the Tool Names, and Tool Pictures
        images = imagedata.tool_images
        names = textdata.tool_names
        descriptions = 'Not Used in Template'
        total_tools = len(names)

        # make top row of table
        cell_x, cell_y = self.side_margin, self.top_margin + 37.867510624999994                                        # found from the Image Height on Header
        cell_w, cell_h = self.page_width / 3, self.page_height * 0.07
        start_y = cell_y + cell_h
        self.set_xy(cell_x, cell_y)
        self.set_font('Arial', '', 12)
        self.cell(cell_w, cell_h, txt='Tool Name', border=1, ln=0, align='C', fill=False)

        cell_x, cell_y = cell_x + cell_w, cell_y
        self.set_xy(cell_x, cell_y)
        self.cell(cell_w, cell_h, txt='Description', border=1, ln=0, align='C', fill=False)

        cell_x, cell_y = cell_x + cell_w, cell_y
        self.set_xy(cell_x, cell_y)
        self.cell(cell_w, cell_h, txt='Picture', border=1, ln=0, align='C', fill=False)

        # fill in the body of the table (to the end of the list in increments of 7)
        i = 0
        while i < 7 and self.seen_tools < total_tools:

            # define box dimensions
            row_w = self.page_width / 3
            row_h = self.page_height * 0.09
            self.set_font('Arial', '', 10)

            # name box
            cell_x, cell_y = self.side_margin, start_y + self.page_height * (0.09 * i)
            self.set_xy(cell_x, cell_y)
            self.cell(row_w, row_h, txt=f'{str(names[self.seen_tools])}', border=1, ln=0, align='C', fill=False)
            
            # description box
            cell_x, cell_y = cell_x + row_w, cell_y
            self.set_xy(cell_x, cell_y)
            self.cell(row_w, row_h, txt='', border=1, ln=0, align='C', fill=False)
            
            # picture box
            img = images[self.seen_tools]

            # proportional resize to the 0.33, 0.09 box
            rows, cols, channels = img.shape
            aspect_ratio = cols / rows

            # save the image to a spam folder locally and then to the PDF
            cell_x, cell_y = cell_x + row_w, cell_y
            self.set_xy(cell_x, cell_y)
            self.set_font('Arial', '', 48)
            self.cell(row_w, row_h, '', 1, 0, 'C')

            pil_img = Image.fromarray(img)
            temp_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\tool_image' + str(self.seen_tools) + '.png'
            pil_img.save(temp_path)

            # send the image to the assigned box without locally resizing with Cv2 to prevent blur
            if cols > row_w:

                # both the image width and height exceed the cell
                if rows > row_h:

                    # find the maximum oversize and fit to it
                    over_w = cols / row_w
                    over_h = rows / row_h
                    over_dim = [over_w, over_h]
                    oversize = max(over_dim)
                    image_w = cols / oversize
                    image_h = rows / oversize
                    self.image(temp_path, cell_x+1, cell_y+1, image_w-1, image_h-1/aspect_ratio)
                    
                # height of the image fits however width does not
                else:

                    # fit the width and proportionally fit the height
                    oversize = cols / row_w
                    image_w = cols / oversize
                    image_h = image_w / aspect_ratio
                    self.image(temp_path, cell_x+1, cell_y+1, image_w-1, image_h-1/aspect_ratio)
                    
            else:

                # width of the image fits however the height does not
                if rows > row_h:

                    # fit the height and proportionally fit the width
                    oversize = rows / row_h
                    image_h = rows / oversize
                    image_w = image_h * aspect_ratio
                    self.image(temp_path, cell_x+1, cell_y+1, image_w-1, image_h-1/aspect_ratio)

                # neither rows or colums exceed the cell
                else:
                    self.image(temp_path, cell_x+1, cell_y+1, cols-1, rows-1/aspect_ratio)

            # increment while loop
            i += 1
            self.seen_tools += 1

        # increment page and remaining counters
        self.page_number += 1
        self.remaining_tools -= 1

    # Make a standard page for an operation
    def operation_page(self):

        # Add Page - Header and Footer Automatically Applied
        self.add_page()

        # need to gather the Operation Description, Before/After Images, Operation Parts (BOM and Name-#s), and Operation Tools
        descriptions = textdata.operation_descriptions
        tools = textdata.operation_tools
        parts = textdata.operation_parts
        parts_bom = textdata.operation_bom_parts
        quantities = textdata.part_quantities

        images = imagedata.product_images

        # left column - description
        cell_x, cell_y = self.side_margin, self.top_margin + self.page_height * 0.15
        cell_w, cell_h = self.page_width / 4, self.page_height * 0.7
        self.set_xy(cell_x, cell_y)
        self.set_font('Arial', '', 10)
        self.cell(cell_w, cell_h, '', 1, 0, 'C')

        cell_x, cell_y = cell_x + 3, cell_y
        self.set_xy(cell_x, cell_y)
        text = f'\nOperation {self.current_operation} Description:\n\n' + str(descriptions[self.current_operation - 1])
        self.multi_cell(cell_w - 5, 8, text, border=0, align='L', fill=False)
        
        # middle column - before/after images
        row_w, row_h = self.page_width / 2, self.page_height * 0.7 / 2

        # fit both images to the boxes they will be enclosed in
        img_before = images[2 * (self.current_operation - 1)]
        img_after = images[2 * (self.current_operation - 1) + 1]

        # proportional resize to the 0.5, 0.35 box
        rows, cols, channels = img_before.shape                               # Because images are either 3624x1836 or 2560x1440, this greatly simplifies resizing
        aspect_ratio = cols/rows
        image_w = int(row_w)
        image_h = int(image_w / aspect_ratio)

        # save the images to a spam folder locally 
        pil_img_before = Image.fromarray(img_before)
        temp_path_before = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\BEFORE' + str(self.current_operation) + '.png'
        pil_img_before.save(temp_path_before)

        pil_img_after = Image.fromarray(img_after)
        temp_path_after = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\SynthImageDump\\AFTER' + str(self.current_operation) + '.png'
        pil_img_after.save(temp_path_after)

        # before image (index = 2i where i is the current_operation - 1)
        cell_x, cell_y = cell_x + cell_w - 3, cell_y
        self.set_xy(cell_x, cell_y)
        self.set_font('Arial', '', 12)
        self.cell(row_w, row_h, '', 1, 0, 'C')

        self.image(temp_path_before, cell_x+1, cell_y + (self.page_height*0.35- image_h)/2 +1, image_w-2, image_h-2/aspect_ratio)

        # after image (index = 2i + 1 where i is the current_operation - 1)
        cell_x, cell_y = cell_x, cell_y + row_h
        self.set_xy(cell_x, cell_y)
        self.set_font('Arial', '', 12)
        self.cell(row_w, row_h, '', 1, 0, 'C')

        self.image(temp_path_after, cell_x+1, cell_y + (self.page_height*0.35- image_h)/2 +1, image_w-2, image_h-2/aspect_ratio)

        # right column - Parts and Tools
        cell_x, cell_y = cell_x + row_w, self.top_margin + self.page_height * 0.15
        cell_w, cell_h = self.page_width / 4, self.page_height * 0.7
        self.set_xy(cell_x, cell_y)
        self.set_font('Arial', '', 10)
        self.cell(cell_w, cell_h, '', 1, 0, 'C')

        cell_x, cell_y = cell_x + 3, cell_y
        self.set_xy(cell_x, cell_y)

        op_parts = parts[self.current_operation - 1].split(',')
        op_tools = tools[self.current_operation - 1].split(',')
        op_bom = parts_bom[self.current_operation - 1].split(',')
        op_quantities = quantities[self.current_operation - 1].split(',')

        op_tools = [s.strip() for s in op_tools]

        # concatenate text for Parts and Tools
        text = f'\nParts:\n'

        for i in range(len(op_parts)):
            text = text + str(op_bom[i]) + '-' + str(op_parts[i]) + ' x' + str(op_quantities[i]) + '\n'

        text = text + '\nTools:\n'
        for name_str in op_tools:
            text = text + str(name_str) + '\n'
 
        self.multi_cell(cell_w - 5, 8, text, border=0, align='L', fill=False)
        
        # increment counters
        self.page_number += 1
        self.remaining_operations -= 1
        self.current_operation += 1

    # Finds the assembly number from the folder name
    def get_assembly_number(self):
        split_path = self.folder_path.split("\\")
        self.assembly_number = split_path[-1]

# calculate the number of operations and tools
operations = int(len(imagedata.product_images) / 2)
tools = m.ceil(len(imagedata.tool_images) / 7)

# create a PDF instance
myPDF = StandardPDF(operations_count = operations, tools_count = tools, path = folder_path)

# generate the outline on the PDF
myPDF.title_page()
myPDF.show_header_footer = True

# create the tool pages
while myPDF.remaining_tools > 0:
    myPDF.tool_page()

# create the operation pages
myPDF.tool_pages = False
myPDF.operation_pages = True

while myPDF.remaining_operations > 0:
    myPDF.operation_page()
    
# save the PDF
try:
    pdf_path = 'C:\\Users\\Bogom\\Documents\\HYDAC S24\\2597195\\myPDF.pdf'                                         # Hard Coded PDF Location 
    myPDF.output(pdf_path)
except PermissionError:
    print("This PDF is opened in another application. Close the PDF before overwriting.")
