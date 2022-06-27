#Imports
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.animation
import scipy.signal
import os.path
import os
from json import JSONEncoder
import json


import warnings
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning) 

from Board import Board
from Kernel import Kernel
from Growth_fn import Growth_fn

MAX_FRAMES = 3000
OUTPUT_PATH = './outputs'
DATA_PATH = './datafiles'
DEMO_PATH = './demos'

class NumpyArrayEncoder(JSONEncoder):
    """Custom instace of JSONEncoder.
    Incorporates automatic serialisation of numpy arrays. 
    Used to save/load the board and kernel states.  
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)
        
class Automaton(Growth_fn):
    """Class for running, animating, loading and saving cellular automata.
    Used in all siumlations for Lenia and Conways's game of life.

    """
    def __init__(self, 
                 board:object, 
                 kernel:object, 
                 growth_fn:object, 
                 dT:float=0.1, 
                 cmap:str='viridis'
                 ):
        """
        Args:
            board (object): Instance of Board(). Stores current state of the field
            kernel (object): Instance of Kernel(). The kernel used to calculate the neighbourhood sum
            growth_fn (object): Instance of Growth_fn(). The growth function used to compute the update on the neighbourhood sum
            dT (float, optional): The timestep used. As dT tends to zero, time approaches continuum. Defaults to 0.1.
            cmap (str, optional): The colourmap used for plotting. Defaults to 'viridis'.
        """
        
        # Local parameters 
        self.cmap = cmap
        self.dT = dT
        
        # Kernel paramaters
        self.kernel = kernel 
        self.normalise_kernel() # Normalise the kernel 
        
        # Growth function parameters
        self.b1 = growth_fn.b1
        self.b2 = growth_fn.b2
        self.s1 = growth_fn.s1
        self.s2 = growth_fn.s2
        self.mu = growth_fn.mu
        self.sigma = growth_fn.sigma
        self.type = growth_fn.type
        if self.type == 'gaussian':
            self.growth = self.growth_gaussian
        elif self.type == 'bosco':
            self.growth = self.growth_bosco
        
        # The board state
        self.board = board.board
        self.board_shape = self.board.shape
        self.fig, self.img = self.show_board() # Frames of animation
        
        self.anim = None # Store the animation
    
    def normalise_kernel(self) -> np.array:
        """Normalise the kernel such the values sum to 1. 
        This makes generalisations much easier and ensures that the range of the neighbourhood sums is independent 
        of the kernel used. 
        Ensures the values of the growth function are robust to rescaling of the board/kernel. 

        Returns:
            np.array: The resulting normlised kernel
        """
        kernel_norm = self.kernel / (1*np.sum(self.kernel))
        self.norm_factor = 1/ (1*np.sum(self.kernel))
        self.kernel = kernel_norm 
        return kernel_norm
      
    def show_board(self, 
                   display:bool=False,
                   ):
        """Create figure to display the board. 
        Used to animate each frame during the simulation.

        Args:
            display (bool, optional): Show the figure

        Returns:
            tuple(plt.figure, plt.imshow): Figure and axes items for the board at timestate t.
        """
        dpi = 50 # Using a higher dpi will result in higher quality graphics but will significantly affect computation

        self.fig = plt.figure(figsize=(10*np.shape(self.board)[1]/dpi, 10*np.shape(self.board)[0]/dpi), dpi=dpi)

        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        
        self.img = ax.imshow(self.board, cmap=self.cmap, interpolation='none', aspect=1, vmin=0) #  vmax=vmax
        
        if display:
            plt.show()
        else: # Do not show intermediate figures when creating animations (very slow)
            plt.close()

        return self.fig, self.img

    def update_rule_default(self, 
                            neighbours:np.array
                            ) -> np.array:
        """Update the board using the classic rules from Conway's game of life:
        
        https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life
        Any live cell with fewer than two live neighbours dies, as if by underpopulation.
        Any live cell with two or three live neighbours lives on to the next generation.
        Any live cell with more than three live neighbours dies, as if by overpopulation.
        Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.

        Args:
            neighbours (np.array): The neighbourhood sums U(x,y)

        Returns:
            np.array: The updated board f(x,y,t+1) at time t+1 
        """
        r1 = (neighbours == 3) # 3 neighbours -> lives
        r2 = np.logical_and(self.board, (neighbours == 2)) # 2 neighbours and alive -> lives
        r3 = np.logical_or(r1,r2).astype(int) # all other -> dead
        return r3
    
    def update_convolutional(self) -> np.array:
        """Update the board state using the convolution method to calculate the neighbourhood sum
        
        f(x,y,t+1) = g(k*f(x,y,t))
        
        where         
        f(x,y,t) is the state at time t
        k is the kernel (e.g. Extended Moore neighbourhood)
        g is the growth function
        n.b. the operator '*' represents the convolution operator
        
        Returns:
            np.array: The updated board f(x,y,t+1)
        """
        
        # Calculate the neighbourhood sum by convolution with the kernel.
        # Use periodic boundary conditions to 'wrap' the grid in the x and y dimensions
        neighbours = scipy.signal.convolve2d(self.board, self.kernel, mode='same', boundary='wrap')
        
        # Update the board as per the growth function and timestep dT, clipping values to the range 0..1
        self.board = np.clip(self.board + self.dT * self.growth(neighbours), 0, 1)
        
        return self.board
        
    
    def animate_step(self, i:int) -> plt.imshow:
        """Update the board and perform a single timestep of animation.
        Used by 'animate' to update and render the board after each iteration, returns the relevent frame. 

        Args:
            i (int): Dummy variable for animation. Represents the frame number

        Returns:
            plt.axes.imshow: The rendered image of the board at the next timestep
        """
        
        self.update_convolutional() # update the board
        self.img.set_array(self.board) # render the updated state 
        return self.img,
    
    def animate(self, 
                frames:int, 
                interval:float=50, 
                blit=True,
                ):
        """The main input point for creating a cellular automata animation. 
        Simulates and renders the cellular automata as a matplotlib.animation.FuncAnimation.
        This can then be saved using ffmpeg.

        Args:
            frames (int): The number of frames/timesteps to simulate.
            interval (float, optional): The time between frames in milliseconds. Defaults to 50.
            blit (bool, optional): Whether to use blitting to render the images. This improves the performace
                    by reducing the amount of unnecessary pixel updates. Defaults to False.
                    https://matplotlib.org/3.5.0/tutorials/advanced/blitting.html
        """
        # Animate Lenia
        self.anim = matplotlib.animation.FuncAnimation(self.fig, self.animate_step, 
                                                frames=frames, interval=interval, save_count=MAX_FRAMES, blit=blit)
        
    def save_animation(self, 
                       filename:str,
                       ):
        """Save a matplotlib.animation.FuncAnimation using ffmpeg/PIL.
        
        Saves in ./outputs by default
        Supported file types:
         - .mp4
         - .gif
         
        The file type is inferred from the filename extension

        Args:
            filename (str): The filename (with extension) to save

        """
        if not self.anim:
            raise Exception('ERROR: Run animation before attempting to save')
            return 
        
        fmt = os.path.splitext(filename)[1] # isolate the file extension
        
        try: # make outputs folder if not already exists
            os.makedirs(OUTPUT_PATH)
        except FileExistsError:
            # directory already exists
            pass

        if fmt == '.gif':
            f = os.path.join(OUTPUT_PATH, filename) 
            writer = matplotlib.animation.PillowWriter(fps=30) 
            self.anim.save(f, writer=writer)
        elif fmt == '.mp4':
            f = os.path.join(OUTPUT_PATH, filename) 
            writer = matplotlib.animation.FFMpegWriter(fps=30) 
            self.anim.save(f, writer=writer)
        else:
            raise Exception('ERROR: Unknown save format. Must be .gif or .mp4')

    def save_json(self, 
                  filename:str,
                  ) -> dict:
        """Create a state dictionary which holds the current values of the board, kernel, growth function parameters
        and native parameters. Save as a .json file 
        
        Allows restoration of a board state at a later time. Used to store species/interesting results.
        Files are stored in ./datafiles by default.
        
        Args:
            filename (str): The filename (including extension). 

        Returns:
            dict: The state dict used to create the .json file. 
        """
        
        fmt = os.path.splitext(filename)[1]
        
        try: # make outputs folder if not already exists
            os.makedirs(DATA_PATH)
        except FileExistsError: # directory already exists
            pass
        
        if not fmt == '.json':
            raise Exception('ERROR: Must save as .json')
            
        d_save = {}

        d_save['dt'] = self.dT
        d_save['cmap'] = self.cmap

        d_save['type'] = self.type
        d_save['s1'] = self.s1
        d_save['s2'] = self.s2
        d_save['b1'] = self.b1
        d_save['b2'] = self.b2
        d_save['mu'] = self.mu
        d_save['sigma'] = self.sigma

        d_save['board'] = self.board
        d_save['kernel'] = self.kernel

        with open(os.path.join(DATA_PATH, filename), 'w') as fp: 
            json.dump(d_save, fp, cls=NumpyArrayEncoder) # Automatic serialization of numpy arrays

        return(d_save)

    def plot_kernel_info(self,
                         cmap:str='viridis', 
                         bar:bool=False,
                         save:str=None,
                         ) -> None:
        """Display the kernel, kernel cross-section, and growth function as a matplotlib figure.

        Args:
            kernel (np.array): The kernel to plot
            growth_fn (object): The growth function used to update the board state
            cmap (str, optional): The colourmap to use for plotting. Defaults to 'viridis'.
                                (https://matplotlib.org/stable/tutorials/colors/colormaps.html)
            bar (bool, optional): Plot the kernel x-section as a bar or line plot. Defaults to False.
            save (str, optional): Save the figure
        """
        
        k_xsection = self.kernel[self.kernel.shape[0] // 2, :]
        k_sum = np.sum(self.kernel)
        
        fig, ax = plt.subplots(1, 3, figsize=(14,2), gridspec_kw={'width_ratios': [1,1,2]})
        
        # Show kernel as heatmap
        ax[0].imshow(self.kernel, cmap=cmap, vmin=0)
        ax[0].title.set_text('Kernel')
        
        # Show kernel cross-section
        ax[1].title.set_text('Kernel Cross-section')
        if bar==True:
            ax[1].bar(range(0,len(k_xsection)), k_xsection, width=1)
        else:
            ax[1].plot(k_xsection)
        
        # Growth function
        ax[2].title.set_text('Growth Function')
        x = np.linspace(0, k_sum, 1000)
        ax[2].plot(x, self.growth(x))
        
        if save:
            print('Saving kernel and growth function info to', os.path.join(OUTPUT_PATH, 'kernel_info'))
            plt.savefig(os.path.join(OUTPUT_PATH, 'kernel_info.png') )
