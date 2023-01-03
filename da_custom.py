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

def f_shift(data, other=-1):
    """
    Shift data by "other" units, positive is to move the column downwards (lags), negative is to move the column forwards (leads)
    """
    out = []
    data_shift = data.copy()
    if other > 0:
        for i in range(0, abs(other)):
            data_shift.pop()
            data_shift.insert(0, nan)
    else:
        for i in range(0, abs(other)):
            data_shift.pop(0)
            data_shift.append(nan)
    return data_shift

def f_lag(data, other=1):
    #Make it positive
    other=abs(other)
    return f_shift(data, other)

def f_lead(data, other=1):
    #Make it negative
    other=abs(other)
    other = -1*other
    return f_shift(data, other)

def f_diff(data, other=-1):
    """
    Diff data by "other" units, positive is to move the column downwards and diff, negative is to move the column upwards and diff
    """
    data_shift = f_shift(data, other)
    out = [l1-l2 for (l1, l2) in zip(data, data_shift)]
    return out

def f_rolling(data, other=5):
    """
    Compute SMA over periods
    """
    out = []
    window = other
    if window >= 0:
        for n, i in enumerate(data, 0):
            values = data[n:window+n]
            sma = sum(values)/window
            out.append(sma)
    if window < 0:
        for n, i in enumerate(data, 0):
            if n+window < 0:
                start=0
            else:
                start=n+window
            values = data[start:n]
            print(values)
            sma = sum(values)/window
            out.append(sma)
    return out

