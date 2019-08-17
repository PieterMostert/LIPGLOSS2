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

import tkinter.messagebox
from numbers import Number

from .dragmanager import *
from .main_window import MainWindow
from .vert_scrolled_frame import VerticalScrolledFrame
from .pretty_names import prettify

class DisplayIngredient:
    """A class used to display the line corresponding to an ingredient in the ingredient editor"""
    def __init__(self, index, core_data, frame):
        ing = core_data.ingredient_dict[index]
        self.delete_button =  ttk.Button(master=frame, text='X', width=2) #, command = partial(delete_ingredient_fn, index))
        self.name_entry = Entry(master=frame, width=20)
        self.name_entry.insert(0, ing.name)
        ox_comp = ing.analysis
        self.oxide_entry = {}
        
        for ox in core_data.oxide_dict:
            # Use this entry widget to input the percent weight of the oxide that the ingredient contains.
            self.oxide_entry[ox] = Entry(master=frame,  width=5)  
            self.oxide_entry[ox].delete(0, END)
            if ox in ox_comp:
                self.oxide_entry[ox].insert(0, ox_comp[ox])
            else:
                pass

        self.attr_entry = {}
        for i, attr in core_data.attr_dict.items(): 
            self.attr_entry[i] = Entry(master=frame, width=5)
        for i, value in ing.attributes.items():
            self.attr_entry[i].insert(0, value)

    def display(self, pos, order):
        self.delete_button.grid(row=pos, column=0)
        self.name_entry.grid(row=pos, column=1, padx=3, pady=3)

        c = 3
        for i, ox in enumerate(order["oxides"]):
            self.oxide_entry[ox].grid(row=pos, column=c+i, padx=3, pady=1)

        c = 100
        for i, attr in enumerate(order["attributes"]): 
            self.attr_entry[attr].grid(row=pos, column=c+i, padx=3, pady=3)

    def delete(self):
        for widget in [self.delete_button, self.name_entry] + list(self.oxide_entry.values()) + list(self.attr_entry.values()):
            widget.destroy()

class IngredientEditor(MainWindow):
    """Window that lets users enter / delete ingredients, edit oxide compositions and other attributes, and rearrange \\
       the order in which ingredients are displayed"""

    def __init__(self, core_data, order, reorder_ingredients):
        self.toplevel = Toplevel()
        self.toplevel.title("Ingredient Editor")

        self.ingredient_editor_headings = Frame(self.toplevel)
        self.ingredient_editor_headings.pack()
        self.i_e_scrollframe = VerticalScrolledFrame(self.toplevel)
        self.i_e_scrollframe.frame_height = 500
        self.i_e_scrollframe.pack()
        ingredient_editor_buttons = Frame(self.toplevel)
        ingredient_editor_buttons.pack()

        # Place the headings on the ingredient_editor. There is some not-entirely-successful fiddling involved to try
        # to get the headings to match up with their respective columns:
        Label(master=self.ingredient_editor_headings, text='', width=5).grid(row=0, column=0)  # Blank label above the delete buttons
        Label(master=self.ingredient_editor_headings, text='', width=5).grid(row=0, column=1)  # Blank label above the delete buttons
        Label(master=self.ingredient_editor_headings, text='    Ingredient', width=20).grid(row=0, column=2)

        Label(master=self.ingredient_editor_headings, text='', width=5).grid(row=0, column=299)  # Blank label above the scrollbar
        Label(master=self.ingredient_editor_headings, text='', width=5).grid(row=0, column=300)  # Blank label above the scrollbar

        c = 3
        for i, ox in enumerate(order["oxides"]):
            Label(master=self.ingredient_editor_headings, text=prettify(ox), width=5).grid(row=0, column=c+i)

        c = 100
        for i, attr in enumerate(order["attributes"]): 
            Label(master=self.ingredient_editor_headings, text=core_data.attr_dict[attr], width=5).grid(row=0, column=c+i)

        # Create drag manager for ingredient rows:
        self.ing_dnd = DragManager(reorder_ingredients)
        
        # Create and display the rows:
        self.display_ingredients = {}
        for r, i in enumerate(order["ingredients"]):
            self.display_ingredients[i] = DisplayIngredient(i, core_data, self.i_e_scrollframe.interior)
            self.display_ingredients[i].display(r, order)    
            self.ing_dnd.add_dragable(self.display_ingredients[i].name_entry)    # This lets you drag the row corresponding to an ingredient by right-clicking on its name   
                
        # This label is hack to make sure that when a new ingredient is added, you don't have to scroll down to see it:
        Label(master=self.i_e_scrollframe.interior).grid(row=9000) 

        self.new_ingr_button = ttk.Button(ingredient_editor_buttons, text='New ingredient', width=20)
        self.new_ingr_button.pack(side='left')   
        self.update_button = ttk.Button(ingredient_editor_buttons, text='Update', width=20)
        self.update_button.pack(side='right')

        self.i_e_scrollframe.interior.focus_force()

    def new_ingredient(self, i, core_data, order):
        self.display_ingredients[i] = DisplayIngredient(i, core_data, self.i_e_scrollframe.interior) 
        self.display_ingredients[i].display(int(i), order)
        self.ing_dnd.add_dragable(self.display_ingredients[i].name_entry)    # This lets you drag the row corresponding to an ingredient by right-clicking on its name