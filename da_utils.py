from math import nan, ceil, floor, isnan
import statistics as stats
from io import BytesIO #Convert image into bytes
import base64 #For image base64 code
#For running commands in shell 
import shlex 
import subprocess
from importlib import import_module
from itertools import chain
from collections import defaultdict

def check_module(module_name, install=False):
    try: 
        import_module(module_name)
    except ModuleNotFoundError:
        if install:
            curldl = subprocess.Popen('curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py -s'.split(' '))
            o = curldl.communicate()
            if o[1] != None:
                return False
            from pathlib import Path
            home = str(Path.home())
            runpip = subprocess.Popen('python3 /tmp/get-pip.py --user'.split(' '))
            o = curldl.communicate()
            if o[1] != None:
                return False
            pipinstall = subprocess.Popen("{}/.local/bin/pip3 install {}".format(home, module).split(' '))
            if o[1] != None:
                return False
            return True
        else:
            return False
    else:
        return True

def imgcat(b64):
    """To print the image on the terminal screen, works for iterm only"""
    start='\033]1337;File=inline=1:'
    b64s = b64.decode(encoding='utf-8')    
    end = '\a\n'
    img_data = start+b64s+end
    cmd = shlex.split('printf {}'.format(img_data))
    subprocess.call(cmd)
    subprocess.call('echo')

def is_empty(figure):
    """
    Return whether the figure contains no Artists (other than the default
    background patch).
    https://matplotlib.org/faq/howto_faq.html#check-whether-a-figure-is-empty
    """
    contained_artists = figure.get_children()
    return len(contained_artists) <= 1

def to_b64(fig, dpi=100):
    """
    Convert the png image file into base64 encoded data
    
    Input
    -----
    fig: Figure 
       Figure object from matplotlib.figure.Figure

    dpi: int
       Dots per inch for the image

    Output
    ------
    binary
       Base64 encoded data of the image
    """
    if is_empty(fig):
        return None
    with BytesIO() as img_io:
        fig.savefig(img_io, format='png', dpi=dpi, bbox_inches='tight')
        b64 = base64.b64encode(img_io.getvalue())
    return b64

def get_argmax():
    """Get the maximum length of arguments that can be passed to a command"""
    command = subprocess.Popen(['getconf', 'ARG_MAX'], stdout=subprocess.PIPE)
    o = command.communicate()
    return int(o[0].decode('utf-8').strip('\n'))
    
##Custom functions for transform
def f_share(data, other=None):
    total = sum(filter(None, map(convert_float, data)))
    out = []
    for i in data:
        try:
            share = round(float(i)/total, 2)
            if other=='g':
                width = 20
                barlength = int(width*share)
                share = '{:>5} |{:<{width}}'.format(str(share),"o"*barlength, width=width)
            out.append(share)
        except ValueError:
            out.append('-')
    return out

def f_cumsum(data, other=None):
    sum_tmp = 0
    out = []
    for i in data:
        sum_tmp += i        
        out.append(sum_tmp)
        print(i, sum_tmp)
    return out

## Helpful functions
def convert_float(x):
    """
    If a string can be converted into float return the float number, else return None
    """
    try:
        out = float(x)
    except ValueError:
        return None
    else:
        return out
    
def get_uniq_fields(fields):
    """
    Remove duplicate fields. Preserves the order, only the first occurence is considered.
    
    Parameters
    ----------
    fields: list
       list of items, can have repeating items

    Retruns
    -------
    list
       list of unique items
    """
    need_fields = []
    for i in fields:
        if i not in need_fields:
            need_fields.append(i)    
    return need_fields

def transpose_rows(rows):
    """
    Transpose a 2D matrix
    input:
    1 2 3
    4 5 6
    
    output:
    1 4
    2 5
    3 6

    Parameters
    ----------
    rows: list
       list of rows (list) of data
    
    Returns
    -------
    list
       list of columns (list) of data
    """
    if not rows:
        return []
    rows = list(rows)
    length = len(rows[0])
    return [list(map(lambda x:x[i], rows)) for i in range(length)]

def f_aggfunc(data, aggfunc, need_sort=False):
    """
    Define functions to run on a list.
    Available: first, last, concat, max, min, sum, count, 
               mean, average, avg, median, p50, pN (N is any interger (0->100),
               stddev
    Any other agg function returns a None

    Parameters
    ----------
    data: list
       list of items

    aggfunc: str
       function to run, if function is not in the list, it returns None

    need_sort: Bool
       Some of the operations expect data to be sorted, this option can be used if needed.

    Returns
    -------
    Single element (int/str/float)
       Runs the aggregation function and retursn the result
    """
    #If there is no value, return None
    if not data or data == [''] or data == []:
        return None
    if aggfunc == 'first':
        return data[0]
    if aggfunc == 'last':
        return data[-1]
    if aggfunc == 'concat':
        return ' '.join(data)
    #Handle aggfunc is None, return the first data point
    if not aggfunc:
        return data[0]
    #For numerical functions convert data into float
    data = list(filter(lambda x:x is not nan, map(convert_float, data)))
    #Remove the None
    data = list(filter(None, data))
    #Sort the data if it was needed
    if need_sort:
        data = sorted(data)
    if not data:
        return None
    if aggfunc == 'max':
        return max(data)
    if aggfunc == 'min':
        return min(data)
    if aggfunc == 'sum':
        return round(sum(data), 2)
    if aggfunc == 'count':
        return len(data)
    if aggfunc in ('mean', 'average', 'avg'):
        return round(sum(data)/len(data), 2)
    if aggfunc in ('median', 'p50'):
        return stats.median(data)
    if aggfunc.startswith('p'):
        p = int(aggfunc[1:])/100
        return data[int(p*len(data))]
    if aggfunc in ('stddev'):
        return round(stats.pstdev(data), 2)
    #If no matches return None
    return None

def get_transform_req(t_input):
    #formatting pattern for the transform request
    t_format = 'fieldN:func:params|chain_func:params2=alias'
    #fieldN -> field number on which the transformation will be done
    #function:params -> first pass transformation and parameters to the function
    #|chain_func:params -> second pass transformation and parameters to the function.
    #                      can be multiple functions separated by "|"
    #=alias -> column name to use
    
    #Append transform actions in order into the list
    t_list = []
    #t_input is a list of transform requests in the format t_format
    # translate that into a list of dictionaries with options abd values as key-value pairs
    for t_req in t_input:
        t_req, sep, t_alias = t_req.partition('=')
        t_req, sep, t_chain = t_req.partition('|')
        chain_l = []        
        if t_chain:
            sep = '|'
            chain_fmt = 'func:params'
            while sep:
                chain_1, sep, chain_2 = t_chain.partition('|')
                chain_d = dict(zip_longest(chain_fmt.split(':'), chain_1.split(':')))
                #The params option can be a field value, or a constant.
                if chain_d['params'].startswith('f'):
                    chain_d['params'] = int(chain_d['params'][1:])
                    chain_d['is_field']= True
                else:
                    chain_d['params'] = float(chain_d['params'])
                    chain_d['is_field'] = False
                chain_l.append(chain_d)
                t_chain = chain_2
        t_options = dict(enumerate(t_req.split(':')))
        #Check for each option and ensure it has a default value
        fields = [int(t_options.get(0, '0').strip('f'))]
        func = t_options.get(1, None)
        params = t_options.get(2, '1')        #The last option can be a field value, or a constant.
        if params.startswith('f'):
            params = int(params[1:])
            is_field= True
        else:
            #params = float(params)
            is_field = False
        t_list.append({'fields': fields, 'func': func, 'params': params, 'is_field': is_field, 'alias': t_alias, 'chain': chain_l})
    return t_list

def get_fields(fields):
    """
    function to parse the input field format and return all the fields that was requested
    If numbers are separated by '-'; get the range of input
    if separated by ','; get the numbers
    """
    #Extract field numbers and clean
    field_l = filter(None, map(lambda x:x.strip(), fields.split(',')))
    all_fields = []
    for f in field_l:
        if '-' in f:
            start, _, end = f.partition('-')
            all_fields += list(range(int(start), int(end)+1))
        elif f:
            all_fields.append(int(f))
    return all_fields

#Histogram related functions
def create_if_not_exists(d, i, t=None):
    """
    Create a key `i` in dictionary `d` with the value `t`, if `i` does not exist.
    """
    if not d.get(i):
        if t == None:
            t = []
        d[i] = t
        
def round_to_factor(number, factor):
    """Find the nearest multiple of factor <= number"""
    return int(number/factor)*factor

def create_bins(bin_min, bin_max, bin_size=10, bin_count=0, round_value=1):
    """
    Create bins for histogram.
    
    Parameters
    ----------
    bin_min: int
        Start of the bin

    bin_max: int
        Final value of the bin

    bin_size: int
        Size of each bin

    bin_count: int
        Number of bins needed

    round_value: int
        Precision of bins

    Returns
    -------
    list
       list of bin values that can be used to bucket data
    """
    #Keeping the min-bin and max-bin boundaries as integers, for readability
    #Since bin_size is also an integer, all bin boundaries will be integers
    if bin_count > 0:
        bin_size = floor((bin_max - bin_min)/bin_count)
    #starting bin should be floor of the decimal passed
    bin_now = floor(bin_min)
    bins = []
    while True: 
        if bin_now >= bin_max: 
            bin_now = bin_max 
            #bins.append(round_to_factor(bin_now, round_value))
            #Last bin should be the ceil of max
            bins.append(ceil(bin_now))
            break 
        else:
            bins.append(bin_now)
            #bins.append(round_to_factor(bin_now, round_value))
            bin_now += bin_size
    return bins

def get_result(data, minv=None, maxv=None, count=20, bin_size=None, bins=[]):
    """
    Create histogram bins
    """
    #Sort the data
    data.sort()
    #min data point for binning
    bin_min = minv or data[0]
    #Max data point for binning
    bin_max = maxv or data[-1]
    #Computation of histogram boundaries, precdence bins > size > count
    #1. bins -> list of values to act as right end of bins
    #2. size -> compute bins based on size of individual bin
    #3. count -> compute bins based on count of bins needed (fallback)
    if bins:
        bins.sort()
        bin_max = bins[-1]
        bin_min = bins[0]
    elif bin_size:
        bins = create_bins(bin_min=bin_min,
                           bin_max=bin_max,
                           bin_size=bin_size)
    else:
        bin_count = count
        if bin_count > (bin_max-bin_min):
            bin_count = bin_max-bin_min
        bins = create_bins(bin_min=bin_min,
                           bin_max=bin_max,
                           bin_count=bin_count)
    if data[-1] > bin_max:
        bins = bins + [data[-1]]
    counter = 0
    bin_d = {}
    for i in data:
        create_if_not_exists(bin_d, bins[counter], 0)
        #X->i (inclusive)
        if i <= bins[counter]: 
            bin_d[bins[counter]] += 1 
        else: 
            found = False
            while found == False:
                counter += 1
                create_if_not_exists(bin_d, bins[counter], 0)
                if i <= bins[counter]:
                    bin_d[bins[counter]] += 1
                    found = True
    i_old = bin_min-1
    return bin_d

def rich_print_table(data, heading, repeat_heading=50, title=None, table_out=False, justify={0: 'left'}):
    rich_check = check_module('rich', install=False)
    if rich_check:
        from rich.console import Console
        from rich.table import Table
        from rich import box
    else:
        return None
    table = Table(title=title, box=box.DOUBLE_EDGE)
    for n, h in enumerate(heading):
        table.add_column(str(h), justify=justify.get(n, 'right'), header_style='bold green',
                         overflow='fold', no_wrap=False)
    row_counter = 0
    for d in data:
        d = map(str, d)
        row_counter += 1
        if row_counter%repeat_heading == 0:
            table.add_row(*d, end_section=True )
            table.add_row(*heading, end_section=True, style="bold green")
        else:
            table.add_row(*d)
    if table_out:
        return table
    console = Console()
    with console.capture() as capture:
            console.print(table)
    str_output = capture.get()
    return str_output

    
def rich_print_layout(rows, columns, data_l):
    rich_check = check_module('rich', install=False)
    if rich_check:
        from rich.layout import Layout
        from rich import print
        from rich.console import Console
    else:
        return None
    layout = Layout()
    row_layout = []
    col_layout = defaultdict(list)
    for r in range(rows):
        row_layout.append(Layout(name="r{}".format(r)))
        for c in range(columns):
            col_layout['r{}'.format(r)].append(Layout(name="c{}{}".format(r, c)))
    layout.split(*row_layout)
    for i in range(len(row_layout)):
        layout['r{}'.format(i)].split(*col_layout['r{}'.format(i)], direction='horizontal')
    col_layout_l = list(chain.from_iterable([v for v in col_layout.values()]))
    for n, d in enumerate(data_l):
        table = rich_print_table(d['data'], d['heading'])
        col_layout_l[n].update(table)
    console = Console()
    with console.capture() as capture:
            console.print(layout)
    str_output = capture.get()
    print(str_output)

    
    return layout
        

