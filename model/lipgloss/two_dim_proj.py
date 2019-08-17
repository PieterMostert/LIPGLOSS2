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

#from pulp import *
from cvxopt import matrix, solvers
from cvxopt.modeling import variable, constraint, op, dot

k = 50  # number of sample points to take in the case where the denominators are different
#solver = GLPK(msg=0)
#solver = PULP_CBC_CMD()

def is_zero(func):
        """Checks if a cvxopt.modelling.function instance is zero.
        Need to check if this works for non-affine functions"""
        if not func._islinear():
                return False
        elif sum([abs(func._linear._coeff[v][0]) for v in func.variables()]):
                return False
        else:
                return True

def two_dim_projection(var0, var1, norm0, norm1, constraints):  
    """
    Calculates the image I of the feasible region determined by contraints, under the map to R^2
    given by the pair of functions (var0/norm0, var1/norm1). Here constraints is a list of
    homogeneous cvxopt.modeling.constraint instances, and var0, var1, norm0 and norm1 are linear 
    cvxopt.modeling.function or cvxopt.modeling.variable instances, all of which are one-dimensional.

    If norm0 = norm1, then I is a polygon, and the function returns a list of its
    vertices. Otherwise, I is a region bounded by a finite number of edges which are either
    line segments, or subsets of hyperbolas. In this case, the function approximates the 
    boundary as consisting of line segments, and returns a list of consective endpoints of 
    these line segments.
    """
    #stop_messages = {'glpk':{'msg_lev':'GLP_MSG_OFF'}}
    initial_vertices = []

    # Start by finding two distinct points on the 2 dimensional projection of the feasible
    # region. This assumes the region is bounded.
    for eps in [1, -1]:
        lp = op(eps * var0, constraints + [norm0==1])
        lp.solve(solver='glpk', options={'glpk':{'msg_lev':'GLP_MSG_OFF'}})
        if lp.status == 'optimal':
            initial_vertices.append([var0.value()[0], var1.value()[0]]) 
        else:
            messagebox.showerror(" ", lp.status)
            return 
        
    
    if is_zero(norm0 - norm1):   # Order is disregarded when deciding equality

        constraints.append(norm0==1)

        # Find remaining points:
        vertices_post = []
        
        for edge in ['top', 'bottom']:
            vertices_pre = []
            vertices_pre += initial_vertices
            
            count = 0    # delete once sure the algorithm always terminates
            
            while len(vertices_pre) > 1 and count <100:
                count += 1
                v0 = vertices_pre[0]
                v1 = vertices_pre[1]

                if v0 == v1:
                    print('points coincide')
                    return   # Change this
                
                v = [v1[0] - v0[0], v1[1] - v0[1]]
                d = abs(v[0]) + abs(v[1]) + 1
                #print(d)
                s = - v[1]/d*var0 + v[0]/d*var1
                lp = op(s, constraints)
                lp.solve(solver='glpk', options={'glpk':{'msg_lev':'GLP_MSG_OFF'}})
                v2 = [var0.value()[0], var1.value()[0]]

                if abs(lp.objective.value()[0] + (v[1]*v0[0] - v[0]*v0[1])/d) < 0.1**5:   # Look into what error bounds cvxopt uses
                    vertices_pre.remove(v0)                     
                    vertices_post.append(v0)                 
                else:
                    vertices_pre.insert(1,v2)

            if count==100:
                print('Error: count overflowed')
           
            initial_vertices.reverse()  # After the 'top' part of the for loop, we switch the order of the vertices to get ready for the 'bottom' part

        #print(vertices_post)
        return vertices_post
    
    else:  # if norm0 and norm1 are different
        vertices = {-1:[], 1:[]}
        a = initial_vertices[0][0]   # min value of var0/norm0
        b = initial_vertices[1][0]   # max value of var0/norm0
        width = b - a - 0.0002
        if width < 0:
            x = (a + b) / 2

            for eps in [-1,1]:
                lp = op(eps * var1, constraints + [norm1 == 1, var0 == x * norm0])
                lp.solve(solver='glpk', options={'glpk':{'msg_lev':'GLP_MSG_OFF'}})
                vertices[eps].append([x, var1.value()[0]])
        else:
            d = width / k
            for i in range(k + 1):
                x = 0.0001 + a + d * i
                for eps in [-1,1]:
                    lp = op(eps * var1, constraints + [norm1 == 1, var0 == x * norm0])
                    lp.solve(solver='glpk', options={'glpk':{'msg_lev':'GLP_MSG_OFF'}})
                    vertices[eps].append([x, var1.value()[0]])  
            vertices[-1].reverse()

        
        #print(vertices[1] + vertices[-1])
        return vertices[1] + vertices[-1]

#LpProblem.two_dim_projection = two_dim_projection  # Add the method two_dim_projection to the LpProblem class.


            
