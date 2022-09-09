from da_utils import *
from math import nan

def dummyfunctionfortransform(data, param):
    """
    data is a list of values
    parameter is an element

    Define functions here that can be used in transform command
    """
    out = [str(i) + str(param) for i in data]
    print(out)
    return out

##Custom functions for transform
def share(data, other=None):
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

def cumsum(data, other=None):
    """
    Compute cumulative sum at each row-value of the column
    """
    sum_tmp = 0
    out = []
    for i in data:
        if isnan(i):
            out.append(nan)
            continue
        sum_tmp += i        
        out.append(sum_tmp)
    return out
