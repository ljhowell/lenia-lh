#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Lewis Howell 20/04/22

import numpy as np
import scipy.sparse
import Kernel


class Board(object):
    """Class for the cellular automata board. Holds the state values at each timestep.
    Initialise boards with different initial conditions:
        - Ones
        - Zeros
        - Random values
        - Sparse random values 
        - Gaussian distributed conditions
        - Radially-symmetric conditions
    """
    def __init__(self, 
                 grid_size:int=16, 
                 seed:int=None):
        """_summary_

        Args:
            grid_size (int): The size of the array used to store the values for the cellular automata
            seed (int, optional): The random seed used during board creation. Set the seed to obtain reproducible
            reults with random boards. Defaults to None.
            
        """
        self.grid_size = grid_size
        self.density = 0.5 # Sparsity
        self.initialisation_type='sparse'
        self.pad = 32
        
        self.seed = seed
    
        self.board = self.intialise_board()
        
    def intialise_board(self) -> np.array:
        """Create an array used to store the values for the cellular automata.

        Returns:
            np.array: The intitialised board at t=0
        """
        np.random.seed(self.seed)
        if self.initialisation_type == 'zeros': 
            self.board = np.zeros([self.grid_size, self.grid_size])

        elif self.initialisation_type == 'ones': 
            self.board = np.ones([self.grid_size, self.grid_size])
            
        elif self.initialisation_type == 'random': 
            self.board = np.random.rand(self.grid_size, self.grid_size)
            
        elif self.initialisation_type == 'sparse': 
            self.board = scipy.sparse.random(self.grid_size, self.grid_size, density=self.density).A
            
        elif self.initialisation_type == 'gaussian':
            R = self.grid_size/2
            self.board = np.linalg.norm(np.asarray(np.ogrid[-R:R-1, -R:R-1]) + 1) / R
            
        elif self.initialisation_type == 'ring':
            self.board = Kernel().smooth_ring_kernel(32)
        
        if self.pad:
            self.board = np.pad(self.board, self.pad)
            
        return self.board  