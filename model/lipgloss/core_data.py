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

# We define the Restriction, Oxide, Ingredient,and Other classes.

from functools import partial
import shelve

reset_oxides = 0
reset_ingredients = 0
reset_other = 0

class Observable:
    def __init__(self, initialValue=None):
        #self.data = initialValue
        self.callbacks = {}

    def addCallback(self, func):
        self.callbacks[func] = 1

    def delCallback(self, func):
        del self.callback[func]

    def _docallbacks(self, attribute):
        for func in self.callbacks:
             func(getattr(self, attribute))

    def set(self, attribute, value):
        setattr(self, attribute, value)
        self._docallbacks(attribute)

    def get(self, attribute):              # Is this necessary?
        return getattr(self, attribute)

    def unset(self, attribute):
        self.attribute = None

class Oxide():
    
    def __init__(self, molar_mass, flux, min_threshhold=0):
        
        'SiO2, Al2O3, B2O3, MgO, CaO, etc'
    
        Observable.__init__(self)
        self.molar_mass = molar_mass
        self.flux = flux  # Either 0 or 1 (for now).
        self.min_threshhold = min_threshhold  # Don't display this oxide if none of the selected ingredients has more than min_threshhold % wt of that oxide

def oxide_reset():

    #import default_data.oxidefile
    from .default_data import oxidefile as oxidefile

    with shelve.open(persistent_data_path+"/OxideShelf") as oxide_shelf:
        for ox in oxide_shelf:
             del oxide_shelf[ox]
        for (pos, ox) in enumerate(oxidefile.oxides):
             Oxide.order.append(ox)
             if ox in oxidefile.fluxes:
                  ox_init = Oxide(molar_mass=oxidefile.molar_mass_dict[ox], flux=1)
             else:
                  ox_init = Oxide(molar_mass=oxidefile.molar_mass_dict[ox], flux=0)
             oxide_shelf[ox] = ox_init

    Oxide.update_order()

if reset_oxides == 1:
    oxide_reset()
else:
    pass
        
class OxideData():
    
    '''Abstract class used to store a dictionary of oxides'''
    
    oxide_dict = {}

    @staticmethod
    def oxides():
        return OxideData.oxide_dict.keys()

    @staticmethod
    def set_default_oxides():
        OxideData.oxide_dict = {}
        from .default_data import oxidefile as oxidefile
        for (pos, ox) in enumerate(oxidefile.oxides):
             if ox in oxidefile.fluxes:
                  ox_init = Oxide(pos, oxidefile.molar_mass_dict[ox], 1) #ox_init = Oxide(pos, molar_mass=oxidefile.molar_mass_dict[ox], flux=1)
             else:
                  ox_init = Oxide(pos, oxidefile.molar_mass_dict[ox], 0) #ox_init = Oxide(pos, molar_mass=oxidefile.molar_mass_dict[ox], flux=0)
             OxideData.oxide_dict[ox] = ox_init

##    def __init__(self):
##        pass
        
##    def update_oxides(self, new_oxide_dict):
##	OxideData.oxide_dict = new_oxide_dict    # check that this works
##	                                         # add stuff to modify ingredient_dict, self.other_dict etc.

# Define Ingredient class.  Ingredients will be referenced by their index, a string consisting of a unique natural number.
class Ingredient(Observable):
    
    def __init__(self, name='New ingredient', notes='', analysis={}, attributes={}, glaze_calculator_ids={}):

        Observable.__init__(self)
        self.name = name
        # notes not implemented yet.
        self.notes = notes
        # analysis is a dictionary giving the weight percent of each oxide in the ingredient.
        self.analysis = analysis
        # attributes is a dictionary giving the values of each attribute of the ingredient
        self.attributes = attributes
        # glaze_calculator_ids is a dictionary with keys being strings referring to various glaze calc software,
        # and values being the corresponding index in that software that encodes the ingredient
        self.glaze_calculator_ids = glaze_calculator_ids

def ingredient_reset():
    import ingredientfile
        
    with shelve.open(persistent_data_path+"/IngredientShelf") as ingredient_shelf:
        for index in ingredient_shelf:
            del ingredient_shelf[index]

        temp_order_list = []
        for (pos, ing) in enumerate(ingredientfile.ingredient_names):

            temp_order_list.append(str(pos))

            ing_init = Ingredient(name=ing, analysis=dict([(ox, ingredientfile.ingredient_analyses[ing][ox]) \
                                                                   for ox in OxideData.oxides() if ox in ingredientfile.ingredient_analyses[ing]]),\
                                  attributes = {})

            for attr in []: #attr_dict:
                try:
                    ing_init.attributes[attr] = ingredientfile.ingredient_analyses[ing][attr]
                except:
                    pass
            
            ingredient_shelf[str(pos)] = ing_init

    Ingredient.order = temp_order_list
    Ingredient.update_order()

if reset_ingredients == 1:
    ingredient_reset()
else:
    pass

# Define Other class:
class Other(Observable):
    
    def __init__(self, name, numerator_coefs, normalization, def_low, def_upp, dec_pt):
        """SiO2:Al2O3, LOI, cost, total clay, etc"""
           
        self.name = name
        
        # numerator_coefs is a dictionary with keys of the form mass_ox, mole_ox, ingredient_i,
        # and values real numbers that are the coefficients in the linear combination of basic
        # variables that define the numerator.
        self.numerator_coefs = numerator_coefs
        
        # For now, normalization is just a text string of the form 'self.lp_var[...]'.
        self.normalization = normalization
        
        self.def_low = def_low
        
        self.def_upp = def_upp
        
        self.dec_pt = dec_pt

def get_ing_comp(ingredient_dict):
    """returns a dict whoses keys are ingredient indices, and values are dicts 
     with keys oxides, and values weight percentages. May change this to a pandas 
     dataframe at some point"""
    ingredient_analyses = {}
    for key in ingredient_dict:
        ingredient_analyses[key] = ingredient_dict[key].analysis
    return ingredient_analyses

class CoreData(OxideData):
    '''Class used to store the dictionaries of ingredients and 'other' restrictions, as well as
       the dictionary of attributes ingredients may have'''
    
    def __init__(self):
        self.ingredient_dict = {}
        self.ingredient_analyses = {}    # Could do without this  
        self.other_dict = {}
        self.attr_dict = {}
        self.default_lower_bounds = {}
        self.default_upper_bounds = {}

    def restr_keys(self):
        """generates a list of all possible restriction keys"""
        return [t+ox for t in ['umf_', 'mass_perc_', 'mole_perc_'] for ox in self.oxide_dict]+\
           ['ingredient_'+i for i in self.ingredient_dict]+\
           ['other_'+ot for ot in self.other_dict]

    def associated_oxides(self, ingredients):
        """The set of all oxides that occur in at least one of the ingredients with index in the list or dictionary ingredients,
        which is a list of ingredient indices, or a dictionary whose keys are ingredient indices"""
        assoc_oxides = set()
        for i in ingredients:
            assoc_oxides = assoc_oxides.union(set(self.ingredient_analyses[i]))  # May not be the most efficient way to do this
        return assoc_oxides
    
    def add_ingredient(self, ing, default_low = 0, default_upp = 100):
        """Adds ingredient ing to the ingredient dictionary. The index is determined automatically"""
        m = max([int(j) for j in self.ingredient_dict]) + 1
        i = str(m)
        self.ingredient_dict[i] = ing
        self.ingredient_analyses[i] = ing.analysis
        self.default_lower_bounds['ingredient_'+i] = default_low
        self.default_upper_bounds['ingredient_'+i] = default_upp

    def remove_ingredient(self, i):
        del self.ingredient_dict[i]
        del self.ingredient_analyses[i]
        del self.default_lower_bounds['ingredient_'+i]
        del self.default_upper_bounds['ingredient_'+i]

    def add_other_restriction(self, ot):
        """Adds other restriction ot to the other restriction dictionary.
           The index is determined automatically"""
        m = max([int(j) for j in self.other_dict]) + 1
        i = str(m)
        self.other_dict[i] = ot
        self.default_lower_bounds['other_'+i] = ot.def_low
        self.default_upper_bounds['other_'+i] = ot.def_upp

    def remove_other_restriction(self, i):
        del self.other_dict[i]
        del self.default_lower_bounds['other_'+i]
        del self.default_upper_bounds['other_'+i]

    def set_default_data(self):
             
        self.attr_dict = {'0': 'LOI', '2': 'Clay', '1': 'Cost'}

        self.ingredient_dict = {}
        from .default_data import ingredientfile as ingredientfile
        for pos, ing in enumerate(ingredientfile.ingredient_names):
            ox_comp = dict([(ox, ingredientfile.ingredient_analyses[ing][ox]) \
                            for ox in self.oxides() if ox in ingredientfile.ingredient_analyses[ing]])
            ing_init = Ingredient(name=ing, analysis=ox_comp, attributes={})
            for attr in self.attr_dict:
                try:
                    ing_init.attributes[attr] = ingredientfile.ingredient_analyses[ing][attr]
                except:
                    pass  
            self.ingredient_dict[str(pos)] = ing_init
        self.ingredient_analyses = get_ing_comp(self.ingredient_dict) 

        self.other_dict = {}
        self.other_dict['0'] = Other('SiO2_Al2O3', {'mole_SiO2':1}, {'mole_Al2O3': 1}, 3, 18, 2)   # Using 'SiO2:Al2O3' gives an error
        self.other_dict['1'] = Other('KNaO UMF', {'mole_K2O':1, 'mole_Na2O':1}, {'fluxes_total': 1}, 0, 1, 3)
        self.other_dict['2'] = Other('KNaO % mol', {'mole_K2O':1, 'mole_Na2O':1}, {'ox_mole_total': 0.01}, 0, 100, 2)
        self.other_dict['3'] = Other('RO UMF', {'mole_MgO':1, 'mole_CaO':1, 'mole_BaO':1, 'mole_SrO':1}, {'fluxes_total': 1}, 0, 1, 3)
        self.other_dict['4'] = Other('Total clay', {'attr_2': 1}, {'ingredient_total': 0.01}, 0, 100, 1)
        self.other_dict['5'] = Other('LOI', {'attr_0': 1}, {'ingredient_total': 0.01}, 0, 100, 1)
        self.other_dict['6'] = Other('cost', {'attr_1': 1}, {'ingredient_total': 0.01}, 0, 100, 1)

        self.default_lower_bounds = {}
        self.default_upper_bounds = {}
        for key in self.restr_keys():
            self.default_lower_bounds[key] = 0
            self.default_upper_bounds[key] = 100

        #with the exception of the following:
        self.default_upper_bounds['umf_Al2O3'] = 10
        for ox in ['B2O3', 'MgO', 'CaO', 'Na2O', 'K2O', 'ZnO', 'Fe2O3', 'TiO2', 'P2O5', 'ZrO2']:
            self.default_upper_bounds['umf_'+ox] = 1
        self.default_lower_bounds['other_0'] = 1

    def set_default_default_bounds(self):
        self.default_lower_bounds = {}
        self.default_upper_bounds = {}
        for key in self.restr_keys():
            self.default_lower_bounds[key] = 0
            self.default_upper_bounds[key] = 100

        #with the exception of the following:
        self.default_upper_bounds['umf_Al2O3'] = 10
        for ox in ['B2O3', 'MgO', 'CaO', 'SrO', 'BaO', 'Na2O', 'K2O', 'ZnO', 'Fe2O3', 'TiO2', 'P2O5']:
            self.default_upper_bounds['umf_'+ox] = 1
        self.default_lower_bounds['other_0'] = 1