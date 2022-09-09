from da_utils import *
from math import nan
from datetime import datetime

def f_dummyfunctionfortransform(data, param):
    """
    Name is: f_*
    data is a list of values
    parameter is an element, if no parameter is passed, 
     - it will default to '' (an empty string)
     - don't use params that start with "f" - this will get treated as field (fN)

    Define functions here that can be used in transform command
    """
    out = [str(i) + str(param) for i in data]
    print(out)
    return out

##Custom functions for transform
def f_share(data, other=None):
    """
    Compute share of each value of the column over the sum of values in the column
    """
    #Ignore invalid data (i.e data that cannot converted into float)
    valid_data = filter(None, map(convert_float, data))
    total = sum([i for i in valid_data if not isnan(i)])
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
    """
    Compute cumulative sum at each row-value of the column
    """
    sum_tmp = 0
    out = []
    for i in data:
        #Attempt convert into float, otherwise make it nan (not-a-number)
        try:
            i = float(i)
        except ValueError:
            i = nan
        #If not-a-number, 
        if isnan(i):
            out.append(nan)
            continue
        sum_tmp += i        
        out.append(sum_tmp)
    return out

def f_formatunixtime(data, other="%H:%M:%S"):
    """
    Format unix timestamp into format specified in other. It is passed directly into strftime method. 
    """
    #Handling the default param option of empty string ''
    if other == '':
        other="%H:%M:%S"
    out = []
    for i in data:
        print(i)
        print(other)
        #Try to convert it to float value, if it is not - use as is
        try:
            i = float(i)
        except ValueError:
            out.append(i)
            continue
        #If it's a float value, convert to date object
        date = datetime.utcfromtimestamp(i)
        o = date.strftime(other)
        out.append(o)
    return out
