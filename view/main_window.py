# LIPGLOSS - Graphical user interface for constructing glaze recipes
# Copyright (C) 2017 Pieter Mostert

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# version 3 along with this program (see LICENCE.txt).  If not, see
# <http://www.gnu.org/licenses/>.

# Contact: pi.mostert@gmail.com

import tkinter as tk
from tkinter import ttk
from functools import partial

try:
    from .vert_scrolled_frame import VerticalScrolledFrame
    from .pretty_names import prettify, pretty_entry_type
    from .polyplot import *
except ImportError:
    from vert_scrolled_frame import VerticalScrolledFrame
    from pretty_names import prettify
    from polyplot import *

import tkinter.messagebox

def edit_oxides():
    pass

def edit_other_restrictions():
    pass

def restriction_settings():
    pass

class MainWindow:

    def __init__(self):
        self.root = Tk()
        self.root.title("LIPGLOSS2")  # LInear Programming GLaze Oxide Software System. Terrible acronym, though it also happens to be a song by Pulp.
                
        # Create the outer content frames
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Create self.menubar
        self.menubar = Menu(self.root)

        # Create the selection window
        self.selection_window = ttk.Frame(self.root, padding=(5, 5, 12, 12), borderwidth = 2, relief = 'solid') #shows list of ingredients and other possible restrictions

        # Create the ingredient selection window
        self.ingredient_selection_window = ttk.Frame(self.selection_window, padding=(5, 5, 5, 5)) # shows list of ingredients
        select_ing_label = Label(self.ingredient_selection_window, text='Select ingredients', font = ('Helvetica',10))  # Heading

        # Create the other selection window
        self.other_selection_window = ttk.Frame(self.selection_window, padding=(5, 5, 5, 5)) # shows list of other restrictions
        select_other_label = Label(self.other_selection_window, text='Select other restrictions', font = ('Helvetica',10))  # Heading
            
        # Create the main window for entering and displaying restrictions
        main_frame = ttk.Frame(self.root, padding=(5, 5, 12, 0))
        main_frame['borderwidth'] = 2
        main_frame['relief'] = 'solid'

        self.recipe_name_frame = ttk.Frame(main_frame, padding=(5, 5, 12, 12)) # window for displaying the current recipe's name
        restriction_frame = ttk.Frame(main_frame, padding=(5, 5, 12, 12)) # window for entering restrictions
        self.restriction_sf = VerticalScrolledFrame(restriction_frame)
        self.restriction_sf.frame_height = 500
        Label(master=self.restriction_sf.interior).grid(row=9000) # A hack to make sure that when a new 'other restriction' is added,
                                                              # you don't have to scroll down to see it.
        calc_frame = ttk.Frame(main_frame, padding=(15, 5, 10, 5))      # window holding the Calc button
        message_frame = ttk.Frame(main_frame, padding=(15, 5, 10, 5))   # window displaying messages. At the moment, this isn't used

        proj_frame = ttk.Frame(self.root, padding=(15, 5, 10, 5))            # window holding canvas displaying the 2-d projection

        proj_heading = ttk.Frame(proj_frame, padding=(5, 5, 5, 15))
        variable_info = ttk.Frame(proj_frame)
        self.proj_canvas = Canvas(proj_frame, width=450, height=450, bg='white', borderwidth=1, relief='solid')

        self.x_lab = Label(variable_info, text='x variable: Click left restriction name to select')
        self.y_lab = Label(variable_info, text='y variable: Click right restriction name to select')

        self.options_menu = Menu(self.menubar, tearoff=0)

        self.ingredient_vsf = VerticalScrolledFrame(self.ingredient_selection_window)
        self.ingredient_vsf.frame_height = 350

        self.other_vsf = VerticalScrolledFrame(self.other_selection_window)
        self.other_vsf.frame_height = 200

        # GRID REMAINING WIDGETS

        # grid selection window
        self.selection_window.pack(side='left',fill=Y)
        self.ingredient_selection_window.grid(column = 0, row = 1, sticky = 'n')
        self.other_selection_window.grid(column = 0, row = 2, sticky = 'n')

        # grid the selection labels
        for label in [select_ing_label, select_other_label]:
            label.grid(column=0, row=0, columnspan=2)

        # grid the vertical scrolled frames containing the ingredients and other restrictions
        self.ingredient_vsf.grid()
        self.other_vsf.grid()

        # grid main frame
        main_frame.pack(side='left', fill='y')
        self.recipe_name_frame.grid(row = 0)
        restriction_frame.grid(row = 10)
        self.restriction_sf.pack()

        # grid recipe name
        self.recipe_name = StringVar()
        Entry(self.recipe_name_frame, textvariable=self.recipe_name, font=("Helvetica 12 italic")).grid()  # displays the name of the current recipe

     
        # grid oxide part of restriction frame
        oxide_heading_frame = ttk.Frame(self.restriction_sf.interior)
        oxide_heading_frame.grid(row=0, column=0, columnspan=7)
        Label(oxide_heading_frame, text='Oxides', font=('Helvetica', 12)).grid(column=0, row=0, columnspan=3)

        # grid ingredient part of restriction frame
        ingredient_heading_frame = ttk.Frame(self.restriction_sf.interior)
        ingredient_heading_frame.grid(row = 100, column = 0, columnspan = 7)
        Label(ingredient_heading_frame, text = 'Ingredients', font = ('Helvetica', 12)).grid()

        # grid other part of restriction frame
        other_heading_frame = ttk.Frame(self.restriction_sf.interior)
        other_heading_frame.grid(row = 1000, column = 0, columnspan = 7)
        Label(other_heading_frame, text = 'Other Restrictions', font = ('Helvetica', 12)).grid()

        # grid calc frame
        calc_frame.grid(row = 1)

        # grid message frame. At the moment, this isn't used
        message_frame.grid(row = 3)

        # grid 2d projection frame
        proj_frame.pack(side='right', fill='y') #grid(column = 1, row = 1, rowspan=1000, sticky = 'nw')
        proj_heading.grid(row=0)
        Label(proj_heading, text='2-dimensional projection', font = ('Helvetica', 12)).grid()
        variable_info.grid(row=1, sticky=W)
        self.proj_canvas.grid(row=2)
        self.x_lab.grid(row=0, sticky=W)
        self.y_lab.grid(row=1, sticky=W)

        # Create menus
        self.file_menu = Menu(self.menubar, tearoff=0)    
        self.menubar.add_cascade(label="File", menu=self.file_menu)        
        self.menubar.add_cascade(label="Options", menu=self.options_menu)
        self.root.config(menu=self.menubar)

        # Create and grid the percent/unity radio buttons:
        self.entry_type = StringVar()  # Make this an observable
        
        self.unity_radio_button = Radiobutton(oxide_heading_frame, text="UMF", variable=self.entry_type, value='umf_')
                                         #command=partial(update_oxide_entry_type, current_recipe, 'umf_'))
        self.unity_radio_button.grid(column=0, row=1)

        self.percent_wt_radio_button = Radiobutton(oxide_heading_frame, text="% weight", variable=self.entry_type, value='mass_perc_')
                                              #command=partial(update_oxide_entry_type, current_recipe, 'mass_perc_'))
        self.percent_wt_radio_button.grid(column=1, row=1)

        self.percent_mol_radio_button = Radiobutton(oxide_heading_frame, text="% mol", variable=self.entry_type, value='mole_perc_')
                                               #command=partial(update_oxide_entry_type, current_recipe, 'mole_perc_'))
        self.percent_mol_radio_button.grid(column=2, row=1)

        self.unity_radio_button.select()

        # Create and grid calc button:
        self.calc_button = ttk.Button(main_frame, text='Calculate restrictions')
        self.calc_button.grid()

        self.ingredient_select_button = {}
        self.other_select_button = {}
        self.recipe_menu = None

class RecipeMenu:
    """A window that lets users select which recipe to open"""
    
    def __init__(self):

        self.recipe_selector = Toplevel()
        self.recipe_selector.title("Recipe Selector")

        self.r_s_scrollframe = VerticalScrolledFrame(self.recipe_selector)
        self.r_s_scrollframe.frame_height = 200
        self.r_s_scrollframe.grid(row=0)
##        recipe_selector_buttons = Frame(self.recipe_selector)
##        recipe_selector_buttons.grid(row=1)
        self.name_buttons = {}
        self.delete_buttons = {}

        Label(master=self.r_s_scrollframe.interior, text='Name', width=35).grid(row=0, column=0)  
        Label(master=self.r_s_scrollframe.interior, text='Delete', width=5).grid(row=0, column=1)

    def delete_recipe(self, i):
        self.name_buttons[i].destroy()
        self.delete_buttons[i].destroy()
"""
    def display_calc_bounds(self, calc_value):  # Do we use this?
        for eps in ['lower', 'upper']:
            self.calc_bounds[eps].config(text=('%.' + str(self.dec_pt) + 'f') % self.calc_value[eps])
"""