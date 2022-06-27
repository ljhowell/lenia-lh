#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Lewis Howell 20/04/22

# Imports
from Board import Board
from Kernel import Kernel
from Growth_fn import Growth_fn
from Automaton import Automaton

import argparse
import numpy as np
from matplotlib import pyplot as plt
import json

NUMERIC_ARGS = ['board_size', 'kernel_size', 'dt', 'frames', 'sigma', 'mu', 'seed']
OPTIONAL_ARGS = ['board_size', 'kernel_size', 'dt', 'frames', 'sigma', 'mu', 'seed', 'b1', 'b2', 's1', 's2']
DEMOS = {
        'demo':'./demos/orbium_unicaudatus.json',
        'orbium':'./demos/orbium_unicaudatus.json',
        'gyrorbium':'./demos/gyrorbium.json',
        'orbium2':'./demos/orbium_unicaudatus_x2_ic.json',
        'orbium3':'./demos/orbium_unicaudatus_x2_2_ic.json',
        'synorbium':'./demos/synorbium_ic.json',
        'kronium':'./demos/kronium_solidus_ic.json',
        'crucium':'./demos/crucium_arcus_ic.json',
        'scutium':'./demos/scutium_solidus_ic.json',
        'pentafolium':'./demos/pentafolium_lithos.json',
        'hopper':'./demos/hopper_ic.json',
        'inversus':'./demos/quadracircum_inversus_ic.json',
        
        'glider':'./demos/glider.json',
        'glidergun':'./demos/glider_gun.json',
        'pentadecathlon':'./demos/penta_decathlon.json',
        'spaceship':'./demos/spaceship.json',
        'diehard':'./demos/die_hard.json',
        
         }

def load_from_json(filename:str) -> dict:
    """Load parameters and board/kernel states from a .json file. Allows restoration of previous simulation states.

    Args:
        filename (str): The filename to load.

    Returns:
        dict: The state dictionary
    """
    # Deserialization
    print("Reading JSON file...")
    with open(filename, "r") as read_file:
        d_load = json.load(read_file)

        d_load["board"] = np.asarray(d_load["board"]) # Deserialise arrays
        d_load["kernel"] = np.asarray(d_load["kernel"])

        return d_load
    
def print_demos() -> None:
    """Print the list of available demos as a nicely formatted list"""
    print('Choose demos from:')
    print(json.dumps(list(DEMOS.keys()), indent=4))
    print('Usage: python Lenia.py --demo [DEMO]')
    
def simulation_from_file(args:dict) -> None:
    """Run a simulation using the board state, kernel and parmaeters read from a .json file
    Used for:
     - runnning demos (most CLI arguments ignored) 
     - running custom simuulations from pre-saved data. 

    Args:
        args (dict): Arguments from the CLI

    """
    # Running a demo
    if args['demo']:
        demo = args['demo']
        
        # Preset demos for classic modalities with random ICs
        if demo == 'conway':
            demo_conway(args)
            exit(0)
            
        if demo == 'smooth_life':
            demo_smooth_life(args)
            exit(0)
            
        if demo == 'lenia':
            demo_lenia(args)
            exit(0)
            
        # Load pre-saved species and required conditions 
        if demo not in DEMOS.keys():
            raise Exception('ERROR: {} not found in demos. Choose from {}'.format(demo, DEMOS.keys()))
    
        print('Loading {}....'.format(DEMOS[demo]))
        d_load = load_from_json(DEMOS[demo])
        d_load['board_size'] = 0 # dummy var. Doesnt matter for loading as board is pre-loaded
        
        if args['outfile'] == None: d_load['outfile'] = '{}.mp4'.format(demo) # e.g. gyrorbium.mp4
        else:  d_load['outfile'] = args['outfile']
        
        if args['frames'] == None: d_load['frames'] = 200
        else:  d_load['frames'] = args['frames']
        
        run_simulation(d_load) # run the simulation
        return(0)
        
    # Load presaved file (not demo)
    else: 
        print('Loading {}....'.format(args['infile']))
        d_load = load_from_json(args['infile'])
        d_load['board_size'] = 0 # dummy var. Doesnt matter for loading as board is pre-loaded
        
        # Overwrite file params with cli params if provided
        if args['outfile']: d_load['outfile'] = args['outfile']
        if args['dt']: d_load['dt'] = args['dt']
        if args['mu']: d_load['mu'] = args['mu']
        if args['sigma']: d_load['sigma'] = args['sigma']
        
        if args['kernel_size']: d_load['kernel_size'] = args['kernel_size']
        if args['kernel_peaks']: d_load['kernel_peaks'] = args['kernel_peaks']
        
        run_simulation(d_load) # run the simulation
        return(0)
    
def demo_conway(args:dict) -> None:
    """Run a demo simulation of Conway's Game of Life using the generalised Lenia framework.
    The board is initialised as a sparse random 64x64 matrix with zero padding of size 32.
    This allows a variety of creatures to emerge under most conditions. 

    Args:
        args (dict): Arguments from the CLI
    """
    
    args['type'] = 'bosco' # boscos's rule for growth/shrinkage
    args['kernel'] = Kernel().square_kernel(3,1) # standard Moore neighbourhood
    args['dt'] = 1 # Discrete time steps
    
    if args['frames'] == None: args['frames'] = 300 
    if args['board_size'] == None: args['board_size'] = 64 
    if args['outfile'] == None: args['outfile'] = 'game_of_life.mp4' 
    
    run_simulation(args) # run the simulation
    return(0)

def demo_smooth_life(args:dict) -> None:
    """Run a demo simulation of SmoothLife using the generalised Lenia framework.
    SmoothLife generalises Conway's game of life to a continuous domain (continous states, space and time).
    For original paper see: https://arxiv.org/abs/1111.1567
    
    The board is initialised as a sparse random 64x64 matrix with zero padding of size 32.

    Args:
        args (dict): Arguments from the CLI
    """
    
    args['type'] = 'bosco'
    args['b1'] = 0.20
    args['b2'] = 0.25
    args['s1'] = 0.19
    args['s2'] = 0.33

    args['kernel'] = Kernel().square_kernel(3,1)
    args['dt'] = 0.1
    
    if args['frames'] == None: args['frames'] = 300 
    if args['board_size'] == None: args['board_size'] = 64 
    if args['outfile'] == None: args['outfile'] = 'smooth_life.mp4' 
    
    run_simulation(args)
    return(0)
    
def demo_lenia(args:dict) -> None:
    """Run a demo simulation of Lenia.
    Lenia further generalises Conway's game of life to a continuous domain (continous states, space and time, 
    smooth kernel, smooth growth function).
    For original paper see: https://arxiv.org/abs/1812.05433

    Args:
        args (dict): Arguments from the CLI
    """
    
    args['type'] = 'gaussian' # smooth growth function
    args['mu'] = 0.135
    args['sigma'] = 0.015

    args['kernel'] = Kernel().smooth_ring_kernel(16) # Guassian ring-like kernel
    args['dt'] = 0.1
    
    if args['frames'] == None: args['frames'] = 100 
    if args['board_size'] == None: args['board_size'] = 64 
    if args['outfile'] == None: args['outfile'] = 'lenia.mp4' 
    
    run_simulation(args)
    return(0)
    
def run_simulation(d_data:dict) -> None:
    """Run and save a simulation using the generalised Lenia framework for a given set of parameters
    Parameters may include:
    - The initial values of the board
        - or board size / seed to create a board
    - The kernel 
        or kernel peaks / kernel size to create a kernel
    - The growth function type (Gaussian/Bosco) and corresponding parameters
    - The value of dT
    - The number of frames to simulate and output format

    Args:
        d_data (dict): The parameters 
    """
    
    # Kernel
    kernel_size = 16
    try:
        if d_data['kernel_size'] != None: kernel_size = int(d_data['kernel_size'])
    except: pass
    
    kernel_peaks = np.array([1])
    try:
        if d_data['kernel_peaks'] != None: kernel_peaks = np.array([float(i) for i in d_data['kernel_peaks']])
    except: pass
        
    kernel = Kernel().kernel_shell(kernel_size, peaks=kernel_peaks) # Create kernel
    try: kernel = d_data['kernel'] # use kernel provided (if exists)
    except: pass  
    
    # Growth fn
    growth_fn = Growth_fn()
    
    # If provided
    try: growth_fn.b1 = d_data['b1']
    except: pass
    try: growth_fn.b2 = d_data['b2']
    except: pass
    try: growth_fn.s1 = d_data['s1']
    except: pass
    try: growth_fn.s2 = d_data['s2']
    except: pass
    try: growth_fn.type = d_data['type']
    except: pass
    
    if d_data['mu'] != None: growth_fn.mu = d_data['mu']
    if d_data['sigma'] != None: growth_fn.sigma = d_data['sigma']
       
    # Board  
    board_size = 64
    if d_data['board_size'] != None: board_size = int(d_data['board_size'])
    
    seed = None
    try: seed = int(d_data['seed'])
    except: pass
    
    board = Board(board_size, seed=seed) # Create board
    try: 
        if type(d_data['board']) != None: 
            board.board = d_data['board'] # if provided
    except: pass

    # General simulation params
    frames = 100
    try: frames = int(d_data['frames'])
    except: pass
    
    dt = 0.1 # timestep
    if d_data['dt'] != None: dt = float(d_data['dt'])
    
    # Run the simulation and animate
    print('Running simulation... ')
    game_of_life = Automaton(board, kernel, growth_fn, dT=dt)
    game_of_life.animate(frames)
    print('Simulation complete!')

    outfile = 'output.mp4'
    try: 
        if d_data['outfile'] != None: 
            outfile = d_data['outfile']
    except: pass
    print('Saving simulation as ./outputs/{}... (may take several minutes)'.format(outfile))
    game_of_life.save_animation(outfile)
    print('Saving complete!')
    
    # Save to json
    try: 
        if d_data['json'] != None: 
            print('Saving results as ./datafiles/{}... '.format(d_data['json']))
            game_of_life.save_json(d_data['json'])
    except: pass
    
    # Save a figure showing the kernel and growth funcion 
    try:
        if d_data['verbose'] == True:
            
            game_of_life.plot_kernel_info(save=True)
            
            print('Saving final board state as ./outputs/board.png')
            plt.figure()
            plt.imshow(game_of_life.board)
            plt.savefig('./outputs/board.png')
    except: pass
    
    print('Complete! :)') # END
    return(0)
    
def validate_args(args:dict) -> dict:
    """Check the arguments provided by the user are valid. Return arguments as correct type.

    Args:
        args (dict): CLI args from user

    Returns:
        dict: Cleaned and checked args
    """
    
    # Convert numeric args to floats
    for arg in NUMERIC_ARGS:
        
        if args[arg] != None:
            try:
                args[arg] = float(args[arg])
            except ValueError:
                print('ERROR: --{} must be a numeric value'.format(arg.replace('_','-')))
                return(-1)
            if args[arg] < 0:
                print('ERROR: --{} must be greater then zero'.format(arg.replace('_','-')))
                return(-1)
    
    # Check the kernel peaks are all numeric
    if args['kernel_peaks'] != None:
        try:
            args['kernel_peaks'] = [float(i) for i in args['kernel_peaks']]
        except ValueError:
            print('ERROR: --kernel-peaks must be a numeric')
            return(-1)
        for i in args['kernel_peaks']:
            if i < 0 or i > 1:
                print('ERROR: --kernel-peaks must be between 0 and 1')
                return(-1)
 
    return args
        
def handle_args(args:dict) -> None:
    """The main execution sequence. Run siumlations and exit.

    Args:
        args (dict): CLI arguments from user
    """
    print_welcome() # Welcome message
    
    args = validate_args(args) # Clean args
    if args == -1:
        exit(-1)
        
    elif args['list_demos']: # List the available demos
        print_demos()
        exit(0)
        
    elif args['demo']: # Run a demo
        simulation_from_file(args)
        exit(0)
        
    elif args['conway']: # Run conway demo
        demo_conway(args)
        exit(0)
        
    elif args['smooth_life']: # Run smoothlife demo
        demo_smooth_life(args)
        exit(0)
        
    elif args['lenia']: # Run lenia demo
        demo_lenia(args)
        exit(0)
        
    elif args['infile']: # Run simulation from file
        simulation_from_file(args)
        exit(0)
    
    else: # Run simulation as defined by cli args
        run_simulation(args)
        exit(0)
        
def print_welcome() -> None:
    """Print a welcome message"""
    
    print('''
-------------------------------------------------------------------------------------------
  _                _          _____ _____ _______ 
 | |              (_)        / ____|  __ \__   __|
 | |     ___ _ __  _  __ _  | (___ | |  | | | |   
 | |    / _ \ '_ \| |/ _` |  \___ \| |  | | | |   
 | |___|  __/ | | | | (_| |  ____) | |__| | | |   
 |______\___|_| |_|_|\__,_| |_____/|_____/  |_|  
 
 Welcome to the Lenia Species Discovery Tool.
 Developed by Lewis Howell for COMP5400M Bio-Inspired Computing - Assessment 2 :)
 See https://arxiv.org/abs/1812.05433 for the original 2018 paper from the creators of Lenia
 
 For help use python Lenia.py -h
 -------------------------------------------------------------------------------------------
 Demos: 
 python3 Lenia.py --list-demos
 python3 Lenia.py --demo [DEMO]

 Evolve new species: 
    python3 Lenia.py -b 16 -k 16 -t 0.1 -m 0.135 -s 0.015 -x 10 -n 200

 or change conditions to see how species change:
    python3 Lenia.py -i ./datafiles/double_orbium.json -o destroyed_orbium.gif -m 0.11
-------------------------------------------------------------------------------------------
          ''')
    
if __name__ == '__main__':
    
    # Agrument handling
    parser = argparse.ArgumentParser(description="Lenia cellular automata - developed by Lewis Howell for COMP5400M Bio-Inspired Computing - Assessment 2",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument("--conway", action="store_true", help="Demo Conway's game of Life with random ICs")
    parser.add_argument("--smooth-life", action="store_true", help="Demo SmoothLife with random ICs")
    parser.add_argument("--lenia", action="store_true", help="Demo Lenia with random ICs")
    parser.add_argument("--demo", help="simulate a pre-saved demo. To list the options use --list-demos", 
                        nargs='?', const='demo', type=str)
    parser.add_argument("--list-demos", action="store_true", help="Show the demo options and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    
    #strings
    parser.add_argument("-c", "--config", help="path to config file")
    parser.add_argument("-i", "--infile", help="path to source file (.json) if using pre-saved data")
    parser.add_argument("-o", "--outfile", help="path to destination file (.gif or .mp4)")
    parser.add_argument("-j", "--json", help="path to store results .json")
    
    # numeric
    parser.add_argument("-b", "--board-size", help="board size")
    parser.add_argument("-k", "--kernel-size", help="kernel size")
    parser.add_argument("-p", "--kernel-peaks", nargs='+', help="kernel peaks") # list
    parser.add_argument("-m", "--mu", help="gaussian mean for kernel (mu)")
    parser.add_argument("-s", "--sigma", help="gaussian stdev for kernel (sigma)")
    parser.add_argument("-t", "--dt", help="timestep (0-1)")
    parser.add_argument("-n", "--frames", help="number of frames to simulate")
    parser.add_argument("-x", "--seed", help="the seed for random number generation")
    
    args = parser.parse_args()
    config = vars(args)
    
    handle_args(config) # Run main sequence
    