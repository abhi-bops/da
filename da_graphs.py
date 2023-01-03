#Importing from da_* should be from da_* import *
# so that get_daflat.py can ignore and the functions are in global scope
from da_utils import *
from da_custom import *
import os
import re
#Ignore warnings that are thrown by matplotlib/pandas
from warnings import filterwarnings
filterwarnings('ignore')

#Check if we have the necessary imports for graphing
global is_graphing
is_graphing=True
force_install=False
try:
    import pandas as pd, numpy as np, matplotlib, seaborn as sns
    from matplotlib.figure import Figure
    import matplotlib.ticker as ticker #For formatting log scales
    large = 20; med = 16; med2 = 14; small = 10
    params = {'axes.titlesize': large,
              'legend.fontsize': med,
              'axes.labelsize': med2,
              'axes.titlesize': med2,
              'xtick.labelsize': med,
              'ytick.labelsize': med,
              'figure.titlesize': large,
              'figure.facecolor':'#eceff4'}
    matplotlib.rcParams.update(params)
    matplotlib.style.use('seaborn')
    sns.set(rc=params)
    #Colors are from https://www.nordtheme.com/docs/colors-and-palettes
    calmjet = matplotlib.colors.LinearSegmentedColormap.from_list("", [ "#d8dee9","#81a1c1", "#a3be8c", "#bf616a"])
except ImportError:
    if force_install:
        pandas_check = check_module('pandas', install=True)
        matplotlib_check = check_module('matplotlib', install=True)
        seaborn_check = check_module('seaborn', install=True)
        numpy_check = check_module('seaborn', install=True)
        if pandas_check and matplotlib_check and seaborn_check and numpy_check:
            import pandas as pd, matplotlib, seaborn as sns
            from matplotlib.figure import Figure
            import matplotlib.ticker as ticker #For formatting log scales            
            is_graphing = True
    else:
        is_graphing=False

class Graph(object):
    def __init__(self, data, heading=None, **kwargs):
        #Parse the graphing options, pop everything that is not graph specific
        # Remaing ones are passed to graphs, expecting them to be graph specific
        self.x = int(kwargs.pop('x', 0)) #column for x-axis
        self.y = kwargs.pop('y', [1])
        #If y is not a list, convert into a list and make it an integer
        if type(self.y) != list:
            self.y = [int(self.y)]
        #self.hue = kwargs.pop('hue', None) #column to use to distinguish multiple series
        self.hue = None
        self.is_ts = kwargs.pop('is_ts', False) #If axis is a timestamp
        self.kind = kwargs.pop('kind', 'bar') #Graph type
        self.aggfunc = kwargs.pop('aggfunc', 'mean') #If multiple values for a combination of x, hue is present. Use this to aggregate 
        self.split_interval = int(kwargs.pop('split_interval', 50) or 50) #To split the graphs, so that it does not hit the bash arg_max limits
        self.subplots = kwargs.pop('subplots', True)
        self.title = kwargs.pop('title', 'Graph')
        self.missing_char = kwargs.pop('missing_char', '-')
        terminalcols = os.get_terminal_size()[0]
        self.dpi = terminalcols - 20
        #If data is a dict, set heading to None
        self.data = data
        if isinstance(data, (dict)):
            self.heading = None
        else:
            self.heading = heading
        self.data_prep()
        self.handle_timeindex()
        self.get_canvas()

    def data_prep(self):
        #Create the dataframe
        df = pd.DataFrame(data=self.data, columns=self.heading)
        self.shape = df.shape
        #If the graph is not 'scatter' and x is given > 0, then treat x as index
        if self.kind != 'scatter' and self.x>=0:
            #Get the index column out
            index = df.columns[self.x]
            df.index = df[index]
            #Select only the y columns
            df = df.iloc[:, self.y]
        #Change all missing_char to nan
        df.replace(self.missing_char, nan, inplace=True)
        #Change datatypes of values to float, so that plotting functions can treat them as numbers
        self.df = df.astype('float')

    def handle_timeindex(self):
        #Handling timeindexes
        #If we need to treat the index as a time value
        if self.is_ts == True:
            # If the 10 characters are integers AND optionally can include "." and any numerical characters
            # This matches unix timestamp as seconds AND also as seconds.milliseconds            
            if re.fullmatch('[0-9]{10}(\.[0-9]+)?', self.df.index[0]):
                self.df.index = pd.to_datetime(self.df.index, unit='s', errors='coerce')
            #Otherwise let pandas try it
            else:
                self.df.index = pd.to_datetime(self.df.index, infer_datetime_format=True, errors='coerce')
            #Indicate the rows that were dropped
            unmatched = self.df[self.df.index == 'Nat']
            if len(unmatched) > 0:
                print("Unmatched data that was dropped for plotting, items={}".format(len(unmatched)))
            self.df = self.df[~(self.df.index == 'NaT')]

    def get_canvas(self):
        #Plotting, need to use optional time units if needed
        #Define a figure class
        self.w = min(30, max(15, self.shape[0]/10))
        #If subplots is True is used, accomodate for each subplot
        # for box, pandas can handle side-by-side plots, so no need
        self.h = 6*len(self.y) if self.subplots and self.kind != 'box' else 6
        #Swap if it's barh
        if self.kind == 'barh': 
            self.w, self.h = self.h, self.w
            #Somehow if the graph is bigger than this, shell breaks due to a large argument list,
            # 18 was got by trial and error method - maybe can change based on elements in graph
            self.h = max(18, self.h)
        elif self.kind == 'heatmap':
            self.w = 20
            self.h = 6

    def to_b64(self, fig, dpi=100):
        out = to_b64(fig, dpi)
        return out

    def get_max(self):
        return self.df.max().max()

    def get_min(self):
        return self.df.min().max()

    #Formatting for the x-axis/time axis
    def format_x(self, x, pos=None):
        if self.is_ts == True:
            #If index is a timeindex format it show HH:MM:SS            
            return self.df.index[int(x)].strftime('%H:%M:%S')
        else:
            return self.df.index[int(x)]
        
    def plot(self, **kwargs):
        """
        Plot the graphs
        """
        graphs = []
        #Plot 50 indexes graph, if there are too many, this eases viewing, and we do not run into bash's arg_max limitations
        start=0
        end=0
        self.min_val = self.get_max()
        self.max_val = self.get_min()
        argmax = get_argmax()        
        #Plot until we run out of rows / columns
        if self.shape[0] > self.shape[1]:
            limit = self.shape[0]            
            limit_type = 'rows'
        else:
            limit = self.shape[1]
            limit_type = 'columns'
        #Split large data sets into small ones at index for graphing
        # If no split is given, disable splitting
        if self.split_interval == -1:
            interval = limit #Set splitting to the max of shape
        else:
            #If split is requested set interval to that 
            interval = min(self.split_interval, limit)
        counter = 0  #counter to limit iterations, in case any bug pops up (not the number of graphs)
        counter_limit = 20
        while limit > end and counter <= counter_limit:
            counter += 1
            if limit_type == 'columns':
                split_df = self.df.iloc[:,start:end+interval]
            else:
                split_df = self.df.iloc[start:end+interval,:]
            fig = Figure(figsize=(self.w, self.h))
            ax = fig.subplots()
            if self.kind == 'heatmap':
                annot = False
                if self.shape[1] < 1000:
                    annot = True
                if self.is_ts:
                    split_df = split_df.T
                sns.heatmap(split_df,
                            ax=ax, annot=True, fmt='2g', cmap=calmjet, linewidths=.1, linecolor="#DDDDDD",
                            vmax=self.max_val, vmin=self.min_val)
                ax.tick_params(axis='x', labelrotation=90)
                ax.tick_params(axis='y', labelrotation=0)
                if self.is_ts:
                    ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.format_x))
            elif self.kind=='line':
                split_df.plot(ax=ax,
                              logx=False,
                              subplots=self.subplots,
                              kind=self.kind,
                              **kwargs)
                ax.tick_params(axis='x', labelrotation=90)
                ax.tick_params(axis='y', labelrotation=0)
            elif self.kind == 'scatter':
                split_df.plot(ax=ax,
                              subplots=self.subplots,
                              kind=self.kind,
                              x=self.x,
                              y=self.y[0])
            else:
                split_df.plot(ax=ax,
                              logx=False,
                              subplots=self.subplots,
                              kind=self.kind,
                              **kwargs)
                ax.tick_params(axis='x', labelrotation=90)
                ax.tick_params(axis='y', labelrotation=0)
            ax.set_title(self.title)                
            fig.set_tight_layout(tight=True)
            b64 = self.to_b64(fig, self.dpi)
            fig.clear()
            #If splitting is allowed, split the dataset
            if self.split_interval != -1 and len(b64) > argmax:
                if interval <= 5:
                    return []
                interval = max(5, interval - 10)
                start=0
                end=0
                continue
            graphs.append(b64)
            #Push start to new position
            start = end+interval
            #Push end to a new position
            end = end+interval
        return graphs