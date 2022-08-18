import fileinput
from math import nan, ceil, floor, isnan
from itertools import tee, starmap, repeat
import statistics as stats
from collections import defaultdict, Counter
#Ignore warnings that are thrown by matplotlib/pandas
from warnings import filterwarnings
filterwarnings('ignore')
import re
from da_utils import *
import os

#Check if we have the necessary imports for graphing
global is_graphing
is_graphing=True
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
        if pandas_check and matplotlib_check and seaborn_check and numpy:
            import pandas as pd, matplotlib, seaborn as sns
            from matplotlib.figure import Figure
            import matplotlib.ticker as ticker #For formatting log scales            
            is_graphing = True
    else:
        is_graphing=False

global missing_char
missing_char = '-'

class Graph(object):
    def __init__(self, data, heading=None, **kwargs):
        #Parse the graphing options, pop everything that is not graph specific
        # Remaing ones are passed to graphs, expecting them to be graph specific
        self.x = int(kwargs.pop('x', 0)) #column for x-axis
        self.y = kwargs.pop('y', [1])
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
    
class Table(object):
    columns = []
    def __init__(self, src=None, delim=' ', heading=None, data=None,
                 max_fields=0, h1=False, fields=None,
                 missing_char='-'):
        self.delim = delim
        self.h1 = h1
        #if 1st line is not heading, use the heading provided, default is []
        if heading:
            self.heading = heading
        else:
            self.heading = []
        self.max_fields = max_fields
        self.missing_char = '-'
        #Check if fields are passed, we only need to filter data from those
        if isinstance(fields, str):
            self.fields = list(map(lambda x:int(x.strip()), fields.split(',')))
        else:
            self.fields = fields
        #If source is stdin or file
        if src == '-':
            self.src = '-'
            self.build_table_from_source()
        #Data is a list of lists; each row is a list; and in each row-list, the column items are in list
        else:
            self.data = data
            #Compute how many columns is needed
            if not self.max_fields:
                self.max_fields = max([len(i) for i in data])
            #Also fill the self.fields list
            self.fields = self.fields or list(range(self.max_fields))
            #If heading is give use it
            if h1:
                self.heading = self.data.pop(0)
        #Fill the headings, if there are some missing
        self.fill_heading()
        self.data, self.data_for_get_fields = tee(self.data, 2)
        #Keep a field index map of input and output
        self.field_map = dict(zip(self.fields, range(self.max_fields)))

    def add_row(self, row):
        self.data.append(row)
            
    def build_table_from_source(self):
        #Read the source
        self.src_data = self.get_input()
        #If the first line is heading, pop it out
        if self.h1:
            self.heading = next(self.src_data)
        #Otherwise check if heading is populated by user input
        elif self.heading == []:
            #If not use the fields numbers as hint for heading
            self.heading = ['col'+str(i) for i in self.fields]
        lines_for_max, lines_for_impute = tee(self.src_data, 2)
        #Compute max fields, needed for imputation of data
        if not self.max_fields:
            self.max_fields = max([len(i) for i in lines_for_max])
        #Impute missing data with missing_char
        self.data = self.impute_missing(lines_for_impute)
    
    def __repr__(self):
        return 'Table: delim="{}", heading={}, fields={}'.format(self.delim, self.heading, self.fields)
    
    def get_input(self):
        """Read data from src, with delim to split fields"""
        #For each line got from input
        for line in fileinput.input(self.src):
            #Strip the trailing newline character
            line = line.strip('\n')
            #Remove any leading spaces and split by the delim
            info = line.strip().split(self.delim)
            #If fields param is passed, Select only those fields
            if self.fields:
                #Using dict and enumerate to access fields by numbers
                filter_info = dict(enumerate(info))
                #If field exists give the result, else return None
                # This should also preserve the order of fields
                info = [filter_info.get(f) for f in self.fields]
            #If an empty string
            if not info or info == ['']:
                continue
            #Generate field list
            yield info

    def add_to_column(self, ):
        pass
    
    def impute_missing(self, lines):
        """Impute missing values on the dataset"""
        #Iterate over each line, find if the total fields in that line < max_fields
        # If it is, imput with the char field
        for line in lines:
            if len(line) < self.max_fields:
                need_fields = self.max_fields - len(line)
                line += [self.missing_char]*need_fields
            #Replace None values and ''
            #Strip any spaces within the column elements
            line = [i.strip() if i else self.missing_char for i in line]
            yield line

    def get_max_fieldlen(self):
        """Get the number of intended columns"""
        return self.max_fields

    def fill_heading(self):
        """Ensure heading for the expected columns have names, by choice or padding"""
        #If it is under or equal, pad it
        if len(self.heading)<=self.max_fields:
            #Pad heading if there is not enough
            self.heading += ['col{}'.format(i) for i in range(len(self.heading), self.max_fields)]
        #if it's over, trim it
        else:
            self.heading=self.heading[:self.max_fields]

    def get_fields(self, fieldN=None):
        """Return field name and data"""
        #If no fields is passed to get_fields
        if not fieldN:
            #Check if we have fields populated from object
            if self.fields:
                fieldN = self.fields
            #Otherwise generate a list using the max_fields
            else:
                fieldN = list(range(self.max_fields))
        field_data = []
        #self.fields is the field numbers of the input used to build the table
        #fieldN is the requested fields from (mapped to the input and not the table)
        #Mask generates a on-off list to filter only the fieldN data
        #ind_mask = [1 if i in fieldN else 0 for i in self.fields]
        field_d = {k: [self.heading[n], []] for n, k in enumerate(fieldN)}
        for row in self.data_for_get_fields:
            for n, k in enumerate(fieldN):
                field_d[k][1].append(row[n])
        #data = list(chain([list(compress(self.heading, ind_mask))],
        #[map(lambda x: list(compress(x, ind_mask)), self.data)]))
        return field_d

    def fast_ascii_table(self, heading_border=True, summary=False,
                         cell_width=15, repeat_heading=40):
        row_counter = 0
        row_f = ('{:<' + str(cell_width) + '} | ')*self.max_fields
        heading_f = row_f.format(*self.heading)
        print(heading_f)
        #If a heading border is needed
        #-1 is to accomodate for space after the last border
        heading_border = (len(heading_f)-1)*"-"
        print(heading_border)
        for i in self.data:
            row_counter += 1
            if row_counter%repeat_heading == 0:
                print(heading_border)
                print(heading_f)
                print(heading_border)                        
            print(row_f.format(*i), flush=True)

    def to_ascii_table(self, heading_border=True, summary=0, repeat_heading=40):
        """Convert heading and data into a fancy table"""
        row_counter = 0
        rows = list(self.data)
        if not rows:
            return None
        result = ''
        all_lines = [self.heading] + rows
        rowf_d = {}
        for n in range(len(self.heading)):
            #For each line
            # Convert the nth element in each line to string
            # Get the length of that element
            # Find the maximum length of the nth element among all the lines
            # Convert it to string format
            rowf_d[n] = str(max([len(str(i[n])) for i in all_lines]))
        row_f = '{:<' + rowf_d[0] + '} | '
        row_f += ''.join(['{:>' + rowf_d[v] +'} | ' for v in range(1, len(self.heading))])
        heading_f = row_f.format(*self.heading)
        result += heading_f + '\n'
        #If a heading border is needed
        if heading_border:
            #-1 is to accomodate for space after the last border
            heading_border = (len(heading_f)-1)*"-"
            result += heading_border + '\n'
        # Print until the penultimate row, the last few rows can be summary
        remaining_rows = 1+summary
        summary_rows = len(rows) - summary
        for i in rows[:summary_rows]:
            row_counter += 1
            if row_counter%repeat_heading == 0:
                 result += heading_border + '\n'
                 result += heading_f + '\n'
                 result += heading_border + '\n'
            result += row_f.format(*i)
            result += '\n'
        #If summary is needed, print a border
        if summary > 0:
            #-1 is to accomodate for space after the last border
            summary_border = (len(heading_f)-1)*"="
            result += summary_border+'\n'
        #Now pring the summary_rows
        for i in rows[summary_rows:]:
            result += row_f.format(*i)+'\n'
        return result

    def pipe(self, delim=' ', disable_heading=False):
        """Pipe result to stdut, with fields separated by delim"""
        #Print the heading first
        if not disable_heading:
            print(delim.join(self.heading))
        #Print the data next
        for line in self.data:
            print(delim.join(map(lambda x:str(x), line)), flush=True) 

    def tocsv(self):
        self.pipe(delim=',')

    def sort(self):
        pass

    def filterrows(self):
        pass

class ColumnTable(Table):
    """
    A object with multiple columns as its members
    """
    def __init__(self, data=[], name='Table', heading=[]):
        self.name = name
        self.cdata = data
        self.heading = heading
        self.data = []

    def add(self, data=[], cname='col'):
        if not isinstance(data, Column):
            data = Column(data)
        self.cdata.append(data.data)
        self.heading.append(data.name or cname)
        self.size = data.size

    def cols_to_rows(self):
        self.data = zip(*self.cdata)

    def to_ascii_table(self):
        if not self.data:
            self.cols_to_rows()
        return super().to_ascii_table()

    def tocsv(self, disable_heading=False):
        if not self.data:
            self.cols_to_rows()
        return super().pipe(delim=',', disable_heading=disable_heading)

    def pipe(self, delim=' ', disable_heading=False):
        if not self.data:
            self.cols_to_rows()
        return super().pipe(disable_heading=disable_heading)

    def __repr__(self):
        return 'ColumnTable: heading={}, name={}'.format(self.heading, self.name)
        
class Column(object):
    def __init__(self, data=None, name='Col', dtype=float, categorical=False):
        """
        Initialise the data necessary to create a column object

        data: list input of column data
        """
        #Set up the column with data from name
        self.name = name
        #Since Table usually passes generators, Convert into list since we will be reusing the data
        self.data = list(data)
        if categorical:
            self.categorical=True
        else:
            self.categorical=False
            #Keep a copy for categorical
            self.data_as_categorical = self.data
            #convert into float, so that imputation is easier            
            self.data = [self.astype(i, float) for i in self.data]
        self.size = len(self.data)
        self.agg_data = {}
        #For in-built functions
        self.fmap = {'add': self.__add__,
                     'divide': self.__div__,
                     'div': self.__div__,
                     'floordiv': self.__floordiv__,
                     'subtract': self.__sub__,
                     'sub': self.__sub__,
                     'multiply': self.__mul__,
                     'mul': self.__mul__,
                     'gt': self.__gt__,
                     'lt': self.__lt__,
                     'ge': self.__ge__,
                     'le': self.__le__,
                     'eq': self.__eq__,
                     'mod': self.__mod__,
                     'sample': self.f_sample,
                     'dummy': self.f_dummy
        }

    def set_column_name(self, name):
        self.name = name

    def __repr__(self):
        return "Column='{}', size={}".format(self.name, self.size)
    
    def __len__(self):
        return self.size

    def get_operand(self, operand):
        if isinstance(operand, Column):
            return operand.data
        elif isinstance(operand, list):
            return operand
        else:
            return list(repeat(operand, self.size))

    def apply_transform(self, f, other):
        """
        f -> function to run
        other -> params to pass into the function
        """
        if f:
            self.data = self.data
        #Hack for subtract_from        
        if f == 'subtract_from':
            self.data = self.__neg__()
            f = 'subtract'
        #If the function is in a list of known internal functions
        if f in self.fmap:
            self.data = list(self.fmap[f](other))
        #If it's not a defined function internally
        else:
            #If function is defined under the global namespace, eval the function
            if f in globals():
                f = eval(f)
                self.data = f(self.data, other)
            else:
                #Otherwise just let the user know
                print("{} does not exist".format(f))

    def transform(self, f, other):
        #Create a mapping for function and data to apply on
        # a-> is the data input
        # b-> parameter for the function to use on a
        return starmap(lambda a,b:f(a,b) if (a and b)!=None else nan, zip(self.data,
                                                                          self.get_operand(other)))

    def astype(self, x, f):
        try:
            o = f(x)
            #Address cases where string like 12e123131 creates a inf value
            if o == float('inf'):
                return nan
            else:
                return o
        except (TypeError, ValueError): return nan

    def __add__(self, other):
        return self.transform(lambda a,b: a+b, other)

    def __sub__(self, other):
        return self.transform(lambda a,b: a-b, other)

    def __mul__(self, other):
        return self.transform(lambda a,b: a*b, other)

    def __div__(self, other):
        return self.transform(lambda a,b: a/b, other)

    def __floordiv__(self, other):
        return self.transform(lambda a,b: a//b, other)

    def __mod__(self, other):
        return self.transform(lambda a,b: a%b, other)

    def f_sample(self, other):
        return self.transform(lambda a,b: a-(a%b), other)

    def __neg__(self):
        return self.__mul__(-1)

    def __eq__(self, other):
        return self.transform(lambda a,b: 1 if a==b else 0, other)

    def __lt__(self, other):
        return self.transform(lambda a,b: 1 if a<b else 0, other)

    def __gt__(self, other):
        return self.transform(lambda a,b: 1 if a>b else 0, other)

    def __le__(self, other):
        return self.transform(lambda a,b: 1 if a<=b else 0, other)

    def __ge__(self, other):
        return self.transform(lambda a,b: 1 if a<=b else 0, other)

    def __ne__(self, other):
        return self.transform(lambda a,b: 1 if a!=b else 0, other)

    def __iter__(self):
        return iter(self.data)

    def f_dummy(self, other):
        """Return the param value for every data"""
        return self.transform(lambda a,b: b, other)

    def filter_nans(self, data):
        #equality fails
        #https://towardsdatascience.com/navigating-the-hell-of-nans-in-python-71b12558895b
        return filter(lambda x:x is not nan, data)

    def aggregate(self, f):
        """Aggregate functions"""
        if not self.data:
            self.agg_data[f] = None
            return
        if f == 'first': self.agg_data[f] = self.data[0]
        if f == 'last': self.agg_data[f] = self.data[-1]
        if f == 'max': self.agg_data[f] = max(self.data)
        if f == 'min': self.agg_data[f] = min(self.data)
        if f == 'sum':  self.agg_data[f] = sum(self.data)
        if f == 'count': self.agg_data[f] = len(self.data)
        if f in ('mean', 'average', 'avg'): self.agg_data[f] = round(self.data, 2)
        if f in ('median', 'p50'): self.agg_data[f] = stats.median(self.data)
        if f in ('stdev'): self.agg_data[f] = round(stats.pstdev(self.data), 2)

    def summary(self):
        result = []
        #Filter out nans for handling continous data
        data_no_nans = sorted(self.filter_nans(self.data))
        size = len(data_no_nans)
        dtype = None
        if size > 0:
            dtype = 'continous'
            #The necessary summary data
            result.append(['count', size])
            result.append(['min', min(data_no_nans)])
            result.append(['max', max(data_no_nans)])
            result.append(['mean', round(sum(data_no_nans)/size, 2)])
            result.append(['stddev', round(stats.pstdev(data_no_nans), 2)])
            pct = [5, 25, 50, 75, 90, 95, 99]
            for p in filter(lambda x:x<=100 and x>=0, pct):
                #Compute the index for the percentile
                # Reduce by 1 because of the 0 indexing
                # using ceil to find the value when it's not an integer
                ind = ceil((p*size)/100)
                #Add boundaries on the result to range from 0->highest index
                ind = max(0, min(ind, size-1))
                result.append(['{}p'.format(p), data_no_nans[ind]])
        else:
            dtype = 'categorical'
            size = len(self.data_as_categorical)
            Ctr = Counter(self.data_as_categorical)
            result.append(['unique', len(Ctr.keys())])
            result.append(['count', size])
            cumsum = 0
            topN = []
            for x in Ctr.most_common()[:5]:
                cumsum += x[1]*100/size
                topN.append(round(cumsum, 2))
            topN += ['-']*(5-len(topN))
            for n, i in enumerate(topN, 1):
                result.append(['top{}'.format(n), '{}'.format(i)])
            result.append(['most', Ctr.most_common()[0][0]])
            result.append(['least', Ctr.most_common()[-1][0]])

        return dtype, result
    
class Pivot(Table):
    def __init__(self, row_k=1, col_k=2, val_k=None, f=None, summary=False,
                 src=None, delim=' ', heading=None, data=None,
                 max_fields=0, h1=False, fields=None,
                 missing_char='-', summaryf=None, rowsummary=True, colsummary=True):
        """
        - Get the necessary arguments for Pivot table, rest are passed as kwargs for Table
        - The defaults are set in line with the results of the commong output of 
        `sort | uniq -c` ; 
        - count is the first field, so it is value
        - row is the second field, because it is usually the time stamp
        - column is the third field, because it is the next key
        """
        self.row_k = row_k
        self.col_k = col_k
        self.rowsummary = rowsummary
        self.colsummary = colsummary
        #If val_k is passed we will need to use that column
        if val_k != None:
            self.val_k = val_k
        #Otherwise we need to use some statistical summary
        else:
            pass
        self.aggfunc = f
        self.summary = summary
        self.summaryfunc = []
        if summary:
            self.summaryfunc = [self.aggfunc]
        if summaryf:
            self.summaryfunc += summaryf
        self.summarydata = {'row':{'heading':[], 'data':[]},
                            'col':{'heading':[], 'data':[]}}
        #Get the function initialised with the super init
        super().__init__(src, delim, heading, data,
                         max_fields, h1, fields,
                         missing_char)

    def pivot2(self):
        """Pivot2 is for grouping and summarising data for row ind key using data from valueind.
        It does not need colind
        """
        rp = 0
        cp = 1
        vp = 2
        pivot_d = defaultdict(list)
        row_v = set()
        for d in self.data:
            #Get the row index, if it's None, use nan
            row_v.add(d[rp] or nan)
            #Get the values in a list for each rowindex, colindex, if it's None use 0
            pivot_d[d[rp]].append(d[vp] or 0)
        #Making row_v into a list and sort it
        row_v = sorted(list(row_v))
        pivot_data = []
        for row in row_v:
            cells = []
            for f in self.summaryfunc:
                cell = f_aggfunc(pivot_d[row], f, need_sort=True) or self.missing_char
                cells.append(cell)
            pivot_data.append([row] + cells)
        self.heading = ['({})'.format(self.heading[self.val_k])]
        self.heading += self.summaryfunc
        self.data = pivot_data
        self.pivotdata = pivot_data

    def pivot(self):
        """Pivot on row index and column index with an aggregation function applied on value index"""
        rp = 0 #row pointer as the result will be got from the table in the order r, c, v
        cp = 1
        vp = 2
        row_v = set()
        col_v = set()
        #Pivot_d
        # 'Row1' : { 'Col1': [value_list], 'Col2': [value_list] },
        # 'Row2' : { 'Col1': [value_list], 'Col2': ... }
        pivot_d = defaultdict(dict)
        for d in self.data:
            #Get the row index, if it's None, use nan
            row_v.add(d[rp] or nan)
            #Get the column index, if it's None, use nan
            col_v.add(d[cp] or nan)
            #Get the values in a list for each rowindex, colindex, if it's None use 0
            if not pivot_d[d[rp]].get(d[cp]):
                pivot_d[d[rp]][d[cp]] = []
            pivot_d[d[rp]][d[cp]].append(d[vp] or 0)
        #Making col_v into a list and sort it
        col_v = sorted(list(col_v))
        row_v = sorted(list(row_v))
        #heading item for output made from pivot_heading and columns
        pivot_data = []
        for row in row_v:
            col_r = []
            for col in col_v:
                data = sorted(pivot_d[row].get(col, []))
                cell = f_aggfunc(data, self.aggfunc) or self.missing_char
                col_r.append(cell)
            pivot_data.append([row, *col_r])
        self.data = pivot_data
        self.pivotdata = pivot_data
        #If summary is needed, running on the resulting pivot table
        #Rest heading, Construct pivot heading using the parent Table's heading
        self.row_v = row_v
        self.col_v = col_v
        self.heading = ['{}({})'.format(self.aggfunc, self.heading[self.val_k])]
        self.heading += self.col_v
        self.pivotheading = self.heading
        #Reset max_fields
        self.max_fields = len(self.heading)        
        summary_data = pivot_data.copy()
        summary_heading = self.heading.copy()
        for func in self.summaryfunc:
            self.add_summary(summary_data, summary_heading, func,
                             rowsummary=self.rowsummary, colsummary=self.colsummary)
            self.data[-1] += ['*']*len(self.summaryfunc)

    def add_summary(self, summary_data, summary_heading, func,
                    rowsummary=True,
                    colsummary=True):
        """Add a summary column for the resulting pivot table.
        2 options, summarise the pivoted table's rows and/or summarise the pivoted
        table's columns"""
        if rowsummary:
            self.summarydata['row']['heading'].append(':RSummary({}):'.format(func))
            self.heading.append(':RSummary({}):'.format(func))        
            #Summary for each row_index, using the pivot result
            # row[1:]->First row is index
            for n, row in enumerate(summary_data):
                #To list as the f_aggfunc for first/last cannot handle filter
                # If result is None, use missing char
                data = list(filter(lambda x:x!=self.missing_char,
                                     row[1:]))
                result = f_aggfunc(data, func, need_sort=True)
                if result == None:
                    result = self.missing_char
                sum_row = result
                self.data[n].append(sum_row)
                self.summarydata['row']['data'].append(sum_row)

        if colsummary:
            self.summarydata['col']['heading'].append(':CSummary({}):'.format(func))
            sum_col=[':CSummary({}):'.format(func)]
            #Summary for each col_index, using the pivot result
            # Appended to the table
            # The last value will be a summary of the summaries of the row index
            for n, col in enumerate(summary_heading[1:], start=1):
            #To list as the f_aggfunc for first/last cannot handle filter
            # If result is none, use missing_char
                data=list(filter(lambda x:x!=self.missing_char,
                                 [i[n] for i in summary_data]))
                result = f_aggfunc(data, func, need_sort=True)
                #If result is None, replace it with missing_char
                if result == None:
                    result = self.missing_char
                sum_col.append(result)
            self.data.append(sum_col)
            self.summarydata['col']['data'].append(sum_col)

    def __repr__(self):
        return 'Pivot: delim="{}", heading={}, fields={}, aggfunc={}'.format(self.delim, self.heading, self.fields, self.aggfunc)

    def to_ascii_table(self):
        #Intialise summary_rows as 0
        summary_rows = 0
        #If we have column key, that means, we are using the proper pivot
        # get the summary rows as the length of the summary function list
        # AND colsummary is TRUE
        if self.col_k and self.colsummary:
            summary_rows = len(self.summaryfunc)
        return super().to_ascii_table(heading_border=True,
                                      summary=summary_rows)

    def get_pivotdata(self):
        return {'data': self.pivotdata, 'heading': self.pivotheading}

    def get_summarydata(self):
        return self.summarydata

