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

import time
import copy
from .core_data import Observable, CoreData

def print_res_type(normalization):   # Used to display error message
    if normalization == "self.lp_var['fluxes_total']":
        prt = 'UMF '
    elif normalization == "self.lp_var['ox_mass_total']":
        prt = '% weight '
    elif normalization == "self.lp_var['ox_mole_total']":
        prt = '% molar '
    else:
        prt = ''
    return prt

def restr_keys(oxides, ingredients, other):
    return [t+ox for t in ['umf_', 'mass_perc_', 'mole_perc_'] for ox in oxides]+\
           ['ingredient_'+i for i in ingredients]+\
           ['other_'+ot for ot in other]

class Recipe(Observable):
    """This is actually a set of bounds on a collection of ingredients, together with bounds on the oxides present, \\
    and possibly bounds on other quantities"""

    def __init__(self, name, pos, oxides, ingredients, other, lower_bounds, upper_bounds, entry_type, variables = {}):
        
        Observable.__init__(self)
        self.name = name
        self.pos = pos   # position in list of recipes to choose
        self.ingredients = ingredients        # List of ingredient indices
        self.other = other                    # List of other indices
        self.oxides = oxides
        self.lower_bounds = lower_bounds      # A dictionary whose keys are the entries in self.restriction_keys
        self.upper_bounds = upper_bounds      # Ditto
        self.entry_type = entry_type          # Should be one of 'umf_', 'mass_perc_' or 'mole_perc_'
        self.variables = variables            # A dictionary whose keys are a subset of the set {'x','y'}, and whose values
                                              # are restriction keys.
        self.restriction_keys = None
        self.update_restriction_keys()
        #run checks to see if oxides are still the associated oxides, in case the ingredient compositions have changed

    def update_restriction_keys(self):
        self.restriction_keys = restr_keys(self.oxides, self.ingredients, self.other)
        
    def fluxes(self):    # Is this used anywhere?
        return [ox for ox in self.oxides if CoreData.oxide_dict[ox].flux > 0]

    def add_ingredient(self, core_data, i):
        if i in self.ingredients:
            print(core_data.ingredient_dict[i].name + ' already occurs in recipe')
        else:
            self.ingredients.append(i) 
            self.oxides = self.oxides.union(set(core_data.ingredient_analyses[i]))
            self.update_restriction_keys()       # Could just make the changes by hand
            for key in self.restriction_keys:
                if key not in self.lower_bounds:
                    self.lower_bounds[key] = core_data.default_lower_bounds[key]
                    self.upper_bounds[key] = core_data.default_upper_bounds[key] 

    def remove_ingredient(self, core_data, i):
        if i in self.ingredients:
            self.ingredients.remove(i)
            self.oxides = core_data.associated_oxides(self.ingredients)
            old_res_keys = self.restriction_keys
            self.update_restriction_keys()
            for key in old_res_keys:
                if key not in self.restriction_keys:
                    del self.lower_bounds[key]
                    del self.upper_bounds[key]
            var = copy.copy(self.variables)
            for t in var:
                if (var[t] in old_res_keys) and (var[t] not in self.restriction_keys):
                    del self.variables[t]
        else:
            print(core_data.ingredient_dict[i].name + ' not in recipe')

    def add_other(self, core_data, index):
        if index in self.other:
            print(core_data.other_dict[index].name + ' already occurs in recipe')
        else:
            self.other.append(index)
            ot = 'other_'+index
            self.restriction_keys.append(ot)
            self.lower_bounds[ot] = core_data.default_lower_bounds[ot]
            self.upper_bounds[ot] = core_data.default_upper_bounds[ot] 

    def remove_other_restriction(self, core_data, i):
        if i in self.other:
            self.other.remove(i)
            ot = 'other_'+i
            self.restriction_keys.remove(ot)
            del self.lower_bounds[ot]
            del self.upper_bounds[ot]
            var = copy.copy(self.variables)
            for t in var:
                if var[t] == ot:
                    del self.variables[t]
        else:
            print(core_data.other_dict[i].name + ' not in recipe')

    def update_bounds(self, core_data):      # To be used when ingredient compositions have changed. Could also be used in add_ingredient and remove_ingredient above
        for key in self.restriction_keys:
            if key not in self.lower_bounds:
                self.lower_bounds[key] = core_data.default_lower_bounds[key]
                self.upper_bounds[key] = core_data.default_upper_bounds[key]
        old_res_keys = copy.copy(list(self.lower_bounds.keys()))
        for key in old_res_keys:
            if key not in self.restriction_keys:
                del self.lower_bounds[key]
                del self.upper_bounds[key]    
        
    def update_oxides(self, core_data):   # to be run whenever the ingredients are changed
        old_oxides = copy.copy(self.oxides)
        ass_oxides = core_data.associated_oxides(self.ingredients)
        var = copy.copy(self.variables)
        complement = self.oxides - ass_oxides
        for ox in complement:
            for t in ['umf_', 'mass_perc_', 'mole_perc_']:
                key = t + ox
                del self.lower_bounds[key]
                del self.upper_bounds[key]
        for v, key in var.items():
            if (key[0] == 'u' and key[4:] in complement) or (key[0] == 'm' and key[10:] in complement):
                del self.variables[v]
        for ox in ass_oxides - old_oxides:
            for t in ['umf_', 'mass_perc_', 'mole_perc_']:
                key = t + ox
                self.lower_bounds[key] = core_data.default_lower_bounds[key]
                self.upper_bounds[key] = core_data.default_upper_bounds[key]
        self.oxides = ass_oxides
        self.update_restriction_keys()

    def update_core_data(self, core_data):
        pass     

    def convert_to_recipe(self):
        # Assumes calc_restrictions has been run
        converted_recipe={}
        s = 0   # sum of averages
        for index in self.ingredients:
            cb = restr_dict['ingredient_'+index].calc_bounds
            avg = (float(cb[1]['text']) + float(cb[-1]['text'])) / 2    
            converted_recipe[index] =  avg
            s += avg
        s *= 0.01
        for index in self.ingredients:
            converted_recipe[index] /= s    # rescale so that percentages add up to 100.
        return converted_recipe     # may want to round to one decimal place.

##    @staticmethod
##    def get_default_recipe():
##        """Define default recipe, in the case where class definitions have changed, or when things have just generally gotten messy"""
##        lb = {} 
##        ub = {} 
##        
##        for ox in ['SiO2', 'Al2O3', 'B2O3', 'MgO', 'CaO', 'Na2O', 'K2O', 'ZnO', 'Fe2O3', 'TiO2', 'P2O5']:
##            for t in ['umf_', 'mass_perc_', 'mole_perc_']:
##                lb[t+ox] = 0
##                ub[t+ox] = 100
##        ub['umf_Al2O3'] = 10
##        for ox in ['B2O3', 'MgO', 'CaO', 'Na2O', 'K2O', 'ZnO', 'Fe2O3', 'TiO2', 'P2O5']:
##            ub['umf_'+ox] = 1
##            
##        for i in range(15):
##            lb['ingredient_'+str(i)] = 0
##            ub['ingredient_'+str(i)] = 100
##            
##        return Recipe('Default Recipe Bounds', 0, [str(i) for i in range(3)], [], lb, ub, 'umf_')
##
