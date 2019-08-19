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
# <http://www.gnu.org/licenses/>.186


# Contact: pi.mostert@gmail.com

import numpy as np
import tkinter
from tkinter import messagebox      # eliminate
from view.pretty_names import prettify   # eliminate
from functools import partial
import shelve
import copy

from .core_data import CoreData
from .recipes import restr_keys
from .two_dim_proj import two_dim_projection
#from pulp import *
from cvxopt import matrix, solvers
from cvxopt.modeling import variable, constraint, op, dot
import time

class LpRecipeProblem():

    def __init__(self, name, recipe, core_data):
        '''Set up the LP problem variables and constraints that hold for a given recipe, apart
        from the used-defined inequalities'''

        self.ingredient_dict = core_data.ingredient_dict
        self.oxide_dict = core_data.oxide_dict
        self.other_dict = core_data.other_dict
        self.ingredient_analyses = core_data.ingredient_analyses
        self.attr_dict = core_data.attr_dict
        self.current_oxides = recipe.oxides
        self.current_ingredients = recipe.ingredients
        self.current_attr = list(core_data.attr_dict.keys())  # Not worth only selecting the ones relevant to the recipe
        self.current_other = recipe.other

        if len(self.current_ingredients)==0:
            messagebox.showerror(" ", 'Select ingredients from the panel on the left.')
        elif len(self.current_oxides)==0:
            messagebox.showerror(" ", 'It appears all the ingredients in this recipe are oxide-free.')
        elif sum(self.oxide_dict[ox].flux for ox in self.current_oxides) == 0:
            messagebox.showerror(" ", 'No flux! You have to give a flux.')
        # Run tests to see if the denominators of other restrictions are identically zero?
        else:
            self.go_ahead = True

            # Create variables
            self.lp_var = {}     # a dictionary for the variables in the linear programming problem 
            self.lp_var['mole'] = variable(len(self.current_oxides), 'mole')  # a vector-valued variable
            self.lp_var['mass'] = variable(len(self.current_oxides), 'mass')  # likewise
            self.lp_var['ingredient'] = variable(len(self.current_ingredients), 'ingredients')
            if len(self.current_attr)>0:
                self.lp_var['attr'] = variable(len(self.current_attr), 'attributes')
            if len(self.current_other)>0:
                self.lp_var['other'] = variable(len(self.current_other), 'other')
            # Create variables used to normalize:
            for total in ['ingredient_total', 'fluxes_total', 'ox_mass_total', 'ox_mole_total']:
                self.lp_var[total] = variable(1, total)

            # Create relations
            self.relations = []

            # Relate masses and moles:
            molar_masses = [self.oxide_dict[ox].molar_mass for ox in self.current_oxides]  # check order
            molar_mass_diag = matrix(np.diag(molar_masses).tolist())   # check order
            self.relations.append(molar_mass_diag * self.lp_var['mole'] == self.lp_var['mass']) 

            # Relate ingredients and oxide masses
            #analysis_matrix = self._make_matrix(self.ingredient_analyses.loc[self.current_ingredients, self.current_oxides]/100)
            analysis_matrix = matrix([[(self.ingredient_analyses[i][ox]*1.0 
                                        if ox in self.ingredient_analyses[i] 
                                        else 0.0) for ox in self.current_oxides] for i in self.current_ingredients])
            self.relations.append(self.lp_var['mass'] 
                                    == analysis_matrix * self.lp_var['ingredient'])

            # Relate ingredients and other attributes.
            #attr_matrix = self._make_matrix(self.ingredient_analyses.loc[self.current_ingredients, self.other_attributes])
            attr_matrix = matrix([[(self.ingredient_dict[i].attributes[j]/100
                                    if j in self.ingredient_dict[i].attributes
                                    else 0) for j in self.current_attr] for i in self.current_ingredients])
            
            self.relations.append(self.lp_var['attr'] 
                                    == attr_matrix * self.lp_var['ingredient'])
            
            # Relate other restrictions to the variables that define them
            # Ensure that only oxides and ingredients already selected are included
            """other_matrix = matrix([[(self.other_dict[i][j]*1.0 
                                        if j in self.ingredient_analyses[i] 
                                        else 0.0) for j in self.current_other] for i in self.current_ingredients])
            """
            for i, j in enumerate(self.current_other):
                lc = self._linear_combination(self.other_dict[j].numerator_coefs)
                self.relations.append(self.lp_var['other'][i] == lc)

            # Relate normalizing variables to others
            flux_gate = matrix([self.oxide_dict[ox].flux*1. for ox in self.current_oxides])
            self.relations.append(self.lp_var['fluxes_total'] == dot(flux_gate, self.lp_var['mole']))
            self.relations.append(self.lp_var['ox_mass_total'] == sum(self.lp_var['mass']))
            self.relations.append(self.lp_var['ox_mole_total'] == sum(self.lp_var['mole']))
            self.relations.append(self.lp_var['ingredient_total'] == sum(self.lp_var['ingredient']))
        
    def _make_matrix(self, df): # convenience function. Not used currently
        return matrix(df.values().tolist())

    def _parser(self, func):
        parts = func.split('|')
        if len(parts)==2:
            group, element = parts  # group should be either mass, mole, ingredient, other or attr
            if group in ['mole', 'mass']:
                current_options = list(self.current_oxides) # Check order
            elif group=='ingredient':
                current_options = self.current_ingredients
            elif group=='other':
                current_options = self.current_other
            elif group=='attr':
                current_options = self.current_attr
            else:
                print(func, 'is an invalid variable encoding.')   
            
            if element in current_options:
                index = current_options.index(element) 
                return self.lp_var[group][index]
            else:
                return 0

        elif len(parts)==1:
            return self.lp_var[func]

        else:
            print(func, 'is an invalid variable encoding.')

    def _linear_combination(self, lc_dict):
        """ lc_dict must have keys which can be parsed, and scalar values""" 
        return sum([(1.*v)*self._parser(k) for k, v in lc_dict.items()]) 

    def calc_restrictions(self, recipe, restr_dict):  

        # First, test for obvious errors
        
        for key in recipe.restriction_keys:
            if recipe.lower_bounds[key] > recipe.upper_bounds[key]:
                res = restr_dict[key]
                messagebox.showerror(" ", 'Incompatible ' + print_res_type(res.normalization) + 'bounds on ' + prettify(res.name))
                return

        delta = 0.1**9

        selected_fluxes = recipe.fluxes()

        sum_UMF_low = sum(recipe.lower_bounds['umf_'+ox] for ox in selected_fluxes)
        if sum_UMF_low > 1 + delta:
            messagebox.showerror(" ", 'The sum of the UMF flux lower bounds is '+str(sum_UMF_low)
                                    +'. It should be at most 1. Decrease one of the lower bounds by '+str(sum_UMF_low-1)
                                    +' or more.')     #will be a problem if they're all < sum_UMF_low-1))
            return

        sum_UMF_upp = sum(recipe.upper_bounds['umf_'+ox] for ox in selected_fluxes)            
        if sum_UMF_upp < 1 - delta:
            messagebox.showerror(" ", 'The sum of the UMF flux upper bounds is '+str(sum_UMF_upp)
                                    +'. It should be at least 1. Increase one of the upper bounds by '+str(1-sum_UMF_low)
                                    +' or more.')
            return

        for t in ['mass_perc_', 'mole_perc_']:
            sum_t_low = sum(recipe.lower_bounds[t+ox] for ox in recipe.oxides)
            if sum_t_low > 100 + delta:
                messagebox.showerror(" ", 'The sum of the ' + prettify(t) + ' lower bounds is '+str(sum_t_low)
                                        +'. It should be at most 100. Decrease one of the lower bounds by '+str(sum_t_low-100)
                                        +' or more.')     #will be a problem if they're all < sum_t_low-100)
                return

            sum_t_upp = sum(recipe.upper_bounds[t+ox] for ox in recipe.oxides)
            if  sum_t_upp < 100 - delta:
                messagebox.showerror(" ", 'The sum of the ' + prettify(t) + ' upper bounds is '+str(sum_t_upp)
                                        +'. It should be at least 100. Increase one of the upper bounds by '+str(100-sum_t_upp)
                                        +' or more.') 
                return
            
        sum_ing_low = sum(recipe.lower_bounds['ingredient_'+index] for index in recipe.ingredients)
        if sum_ing_low > 100 + delta:
            messagebox.showerror(" ", 'The sum of the ingredient lower bounds is '+str(sum_ing_low)
                                    +'. It should be at most 100. Decrease one of the lower bounds by '+str(sum_ing_low-100)
                                    +' or more.')     #will be a problem if they're all < sum_ing_low-100)
            return
            
        sum_ing_upp = sum(recipe.upper_bounds['ingredient_'+index] for index in recipe.ingredients)
        if sum_ing_upp < 100 - delta:
            messagebox.showerror(" ", 'The sum of the ingredient upper bounds is '+str(sum_ing_upp)
                                    +'. It should be at least 100. Increase one of the upper bounds by '+str(100-sum_ing_upp)
                                    +' or more.')  
            return
        
        t1 = time.process_time()
        # Inequalities:
        self.inequalities = []
        #ing_low = self._make_matrix(recipe.lower_bounds['ingredients'])
        #ing_upp = self._make_matrix(recipe.upper_bounds['ingredients'])
        ing_low = matrix([recipe.lower_bounds['ingredient_'+str(i)]/100 for i in self.current_ingredients])
        ing_upp = matrix([recipe.upper_bounds['ingredient_'+str(i)]/100 for i in self.current_ingredients])
        self.inequalities.append(self.lp_var['ingredient'] >= ing_low*self.lp_var['ingredient_total'])     # ingredient lower bounds    
        self.inequalities.append(self.lp_var['ingredient'] <= ing_upp*self.lp_var['ingredient_total'])     # ingredient lower bounds
        
        #umf_lower = self._make_matrix(recipe.lower_bounds['umf'])
        #umf_upper = self._make_matrix(recipe.upper_bounds['umf'])
        umf_lower = matrix([recipe.lower_bounds['umf_'+ox] for ox in self.current_oxides])
        umf_upper = matrix([recipe.upper_bounds['umf_'+ox] for ox in self.current_oxides])
        self.inequalities.append(self.lp_var['mole'] >= umf_lower*self.lp_var['fluxes_total'])
        self.inequalities.append(self.lp_var['mole'] <= umf_upper*self.lp_var['fluxes_total'])
        #mol_perc_lower = self._make_matrix(0.01*recipe.lower_bounds['mole'])
        #mol_perc_upper = self._make_matrix(0.01*recipe.upper_bounds['mole'])
        mole_perc_lower = matrix([recipe.lower_bounds['mole_perc_'+ox]/100 for ox in self.current_oxides])
        mole_perc_upper = matrix([recipe.upper_bounds['mole_perc_'+ox]/100 for ox in self.current_oxides])
        self.inequalities.append(self.lp_var['mole'] >= mole_perc_lower*self.lp_var['ox_mole_total'])  # oxide mol % lower bounds
        self.inequalities.append(self.lp_var['mole'] <= mole_perc_upper*self.lp_var['ox_mole_total'])  # oxide mol % upper bounds
        #wt_perc_lower = self._make_matrix(0.01*recipe.lower_bounds['mass'])
        #wt_perc_upper = self._make_matrix(0.01*recipe.upper_bounds['mass'])
        mass_perc_lower = matrix([recipe.lower_bounds['mass_perc_'+ox]/100 for ox in self.current_oxides])
        mass_perc_upper = matrix([recipe.upper_bounds['mass_perc_'+ox]/100 for ox in self.current_oxides])
        self.inequalities.append(self.lp_var['mass'] >= mass_perc_lower*self.lp_var['ox_mass_total'])
        self.inequalities.append(self.lp_var['mass'] <= mass_perc_upper*self.lp_var['ox_mass_total']) 
        
        for i, j in enumerate(self.current_other):
            res = restr_dict['other_'+j]
            normalization = self._linear_combination(res.normalization)
            other_lower = recipe.lower_bounds['other_'+j]
            other_upper = recipe.upper_bounds['other_'+j]
            self.inequalities.append(self.lp_var['other'][i] >= other_lower * normalization)
            self.inequalities.append(self.lp_var['other'][i] <= other_upper * normalization) 

        # Calculate the upper and lower bounds imposed on all the variables:
        calc_bounds = {} #{-1:{}, 1:{}}   # -1 for lower bounds, 1 for upper bounds
        for key in recipe.restriction_keys:
            calc_bounds[key] = {}
            res = restr_dict[key]
            norm = self._linear_combination(res.normalization)
            normalization = (norm==1) # Normalization of the restriction in question. There's a lot of
                                      # unnecessary repetition of this step, but it seems this doesn't 
                                      # slow things down a whole lot
            opt_var = self._parser(res.objective_func)
            for eps, bound in zip([1, -1], ['lower', 'upper']):        # calculate lower and upper bounds.
                lp = op(eps*opt_var, self.relations + self.inequalities + [normalization])
                lp.solve(solver='glpk', options={'glpk':{'msg_lev':'GLP_MSG_OFF'}})
                if lp.status == 'optimal':
                    calc_bounds[key][bound] = eps*lp.objective.value()[0]
                else:
                    messagebox.showerror(" ", lp.status)
                    return 0
                    
        return calc_bounds
         #{'lower':calc_bounds[-1], 'upper':calc_bounds[1]}

    def calc_2d_projection(self, recipe, restr_dict):
        """This is designed to be run when only the x and y variables have changed; it does not
         take into account changes to upper and lower bounds."""

        if len(recipe.variables) == 2:
            x_var = restr_dict[recipe.variables['x']]
            y_var = restr_dict[recipe.variables['y']]
            x_norm = self._linear_combination(x_var.normalization)
            y_norm = self._linear_combination(y_var.normalization)

            vertices = two_dim_projection(self._parser(x_var.objective_func), 
                                          self._parser(y_var.objective_func), 
                                          x_norm, 
                                          y_norm, 
                                          self.relations + self.inequalities)
            return vertices

        else:
            print("Select two variables first")  
