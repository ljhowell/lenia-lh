#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Lewis Howell 20/04/22

import numpy as np


class Kernel(object):
    """Class for the kernel used during convolution update of each timestep of Lenia
    Create a variety of kernels:
     - Square kernel
     - (Interpolated) circle kernel
     - (Interpolated) ring kernel
     - Gaussian smoothed ring kernel
     - Multiple ring kernel
    """
    def __init__(self):
        self.kernel = self.smooth_ring_kernel(16)
        
    def square_kernel(self, 
                      outer_diameter:int, 
                      inner_diameter:int,
                      ) -> np.array:
        """Create a square kernel for Moore neighbourhood, or extended Moore neighbourhood calculation
        
        e.g. 3,1 ->
            111
            101
            111
            
        e.g. 5,3 ->
            11111
            10001
            10001
            10001
            11111

        Args:
            outer_diameter (int): The outer diameter of the kernel ones (equal to the kernel size)
            inner_diameter (int): The inner diameter of the kernel zeros

        Returns:
            np.array: The resulting kernel
        """
        # Check that both diameters are either odd or even, else kernel is asymmetric
        if not ((outer_diameter % 2 == 0) and (inner_diameter % 2 == 0) or (outer_diameter % 2 == 1) and (inner_diameter % 2 == 1)): # both even
            print('ERROR: Use both odd or both even dimensions to ensure kernel symmetry')
            return None
        if outer_diameter <= inner_diameter:
            print('ERROR: Outer diameter (= {}) must be greater than inner (= {})'.format(outer_diameter,inner_diameter))
            return None

        inner = np.pad(np.ones([inner_diameter,inner_diameter]),(outer_diameter-inner_diameter) // 2)
        outer = np.ones([outer_diameter,outer_diameter])

        return outer - inner
    
    def circular_kernel(self, 
                        diameter:int, 
                        invert:bool=False,
                        ) -> np.array:
        """Create an interpolated circle kernel. 
        Used by self.ring_kernel
        
        e.g. 5 ->
        
        01110
        11111
        11111
        11111
        01110
        
        e.g. 7 ->
        
        0011100
        0111110
        1111111
        1111111
        0111110
        0011100

        Args:
            diameter (int): The outer diameter of the kernel (equal to the kernel size)
            invert (bool, optional): Whether to inver the values. Defaults to False.

        Returns:
            np.array: The resulting kernel
        """
        

        mid = (diameter - 1) / 2
        distances = np.indices((diameter, diameter)) - np.array([mid, mid])[:, None, None]
        kernel = ((np.linalg.norm(distances, axis=0) - diameter/2) <= 0).astype(int)
        if invert:
            return np.logical_not(kernel).astype(int)
        
        return kernel

    def ring_kernel(self, 
                    outer_diameter:int, 
                    inner_diameter:int
                    ) -> np.array:
        """Create a binary, interpolated ring-like kernel. 
        Removes orthogonal bias, allowing isotropic patterns to form.

        Args:
            outer_diameter (int): The outer diameter of the kernel ones (equal to the kernel size).
            inner_diameter (int): The inner diameter of the kernel zeros.

        Returns:
            np.array: The resulting kernel
        """
        if not ((outer_diameter % 2 == 0) and (inner_diameter % 2 == 0) or (outer_diameter % 2 == 1) and (inner_diameter % 2 == 1)):
            print('ERROR: Use both odd or both even dimensions to ensure kernel symmetry')
            return None

        inner = np.pad(self.circular_kernel(inner_diameter),(outer_diameter-inner_diameter) // 2)
        outer = self.circular_kernel(outer_diameter)

        return outer - inner
    
    def smooth_ring_kernel(self, 
                           diameter:int, 
                           mu:float=0.5, 
                           sigma:float=0.15
                           ) -> np.array:
        """Generate a smooth ring kernel by applying a bell-shaped (Gaussian) function to the kernel.
        Used by kernel_shell

        Args:
            diameter (int): The outer diameter of the kernel ones (equal to the kernel size).
            mu (float, optional): The mean value for Gaussian smoothing. Defaults to 0.5.
            sigma (float, optional): The stdev value for Gaussian smoothing. Defaults to 0.15.

        Returns:
            np.array: The resulting kernel
        """
        R = (diameter / 2) + 1 # radius
        gaussian = lambda x, m, s: np.exp(-( (x-m)**2 / (2*s**2) ))
        D = np.linalg.norm(np.asarray(np.ogrid[-R:R-1, -R:R-1]) + 1) / R
        
        return (D<1) * gaussian(D, mu, sigma)
    
    def kernel_shell(self, 
                     diameter:int, 
                     peaks:np.array(float)=np.array([1/2, 2/3, 1]), 
                     mu:float=0.5, 
                     sigma:float=0.15, 
                     a:float=4.0
                     ) -> np.array:
        """Extend the kernal to multiple smooth rings ('shells').
        The number of shells can be changed by changing the number of items in 'peaks'.
        Shells are created equidistantly from the centre to the diameter.
        This allows the evolution of more interesting and diverse creatures.

        Args:
            diameter (int): The outer diameter of the kernel ones (equal to the kernel size).
            peaks (np.array, optional): The amplitude of the peaks for the shells, from inner to outer. 
                Defaults to np.array([1/2, 2/3, 1]).
            mu (float, optional): The mean value for Gaussian smoothing. Defaults to 0.5.
            sigma (float, optional): The stdev value for Gaussian smoothing. Defaults to 0.15.
            a (float, optional): The pre-factor for gaussian smoothing. Defaults to 4.0.

        Returns:
            np.array: The resulting kernel
        """
        R = int(diameter / 2) + 1
        D = np.linalg.norm(np.asarray(np.ogrid[-R:R-1, -R:R-1]) + 1) / R
        k = len(peaks)
        kr = k * D

        peak = peaks[np.minimum(np.floor(kr).astype(int), k-1)]
        gaussian = lambda x, m, s: a*np.exp(-( (x-m)**2 / (2*s**2) ))

        return (D<1) * gaussian(kr % 1, mu, sigma) * peak