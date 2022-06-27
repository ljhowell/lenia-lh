#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Lewis Howell 20/04/22

import numpy as np

class Growth_fn(object):
    """Class for the growth function which is used to update the board based on the neighbourhood sum.
    This replaces the traditional conditional update used in Conway's game of life and can be generalised to any
    continous function. 
    
    f(x,y,t+1) = g(k*f(x,y,t))
    
    where g is the growth function
    k is the update kernel 
    f(x,y,t) is the board state at time t
    N.b. The operator * is the convolution operator 
    
    It consists of growth and shrink parts, which act on the neighbourhood sum to update the board at each timestep.
    """
    def __init__(self):
        
        # Values for Bosco's update rule
        self.b1 = 2*0.125
        self.b2 = 4*0.125
        self.s1 = 3*0.125
        self.s2 = 4*0.125
        
        # Values for Gaussian update rule
        self.mu = 0.135
        self.sigma = 0.015
        
        # Use Gaussian by default (Lenia)
        self.type = 'gaussian'
        if self.type == 'gaussian':
            self.growth_fn = self.growth_gaussian
        elif self.type == 'bosco':
            self.growth_fn = self.growth_bosco
    
    def growth_conway(self, U:np.array) -> np.array:
        """Conditinal update rule for Conway's game of life
        b1..b2 is birth range, s1..s2 is stable range (outside s1..s2 is the shrink range) 

        Args:
            U (np.array): The neighbourhood sum 

        Returns:
            np.array: The updated board at time t = t+1
        """
        return 0 + (U==3) - ((U<2)|(U>3))
    
    def growth_bosco(self, U:np.array) -> np.array:
        """Bosco's rule update for an extended Moore neighbourhood

        Args:
            U (np.array): The neighbourhood sum 

        Returns:
            np.array: The updated board at time t = t+1
        """
        return 0 + ((U>=self.b1)&(U<self.b2)) - ((U<self.s1)|(U>=self.s2))
    
    def growth_gaussian(self, U:np.array) -> np.array:
        """Use a smooth Gaussian growth function to update the board, based on the neighbourhood sum.
        This is the function used by Lenia to achive smooth, fluid-like patterns.

        Args:
            U (np.array): The neighbourhood sum 

        Returns:
            np.array: The updated board at time t = t+1
        """
        gaussian = lambda x, m, s: np.exp(-( (x-m)**2 / (2*s**2) ))
        return gaussian(U, self.mu, self.sigma)*2-1