from da_utils import *
from math import nan, isnan
from datetime import datetime
from itertools import starmap
import csv

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
    fcolA:f_normalise:fcolB; compute for each colA: colA/total(colA)

    Compute share of each value of the column over the sum of values in the column
    """
    #Ignore invalid data (i.e data that cannot converted into float)
    valid_data = filter(lambda x:x != None, map(convert_float, data))
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

def f_normalise(data, other=None):
    """
    fcolA:f_normalise:fcolB; compute colA/(colB+colA)
    """
    #Ignore invalid data (i.e data that cannot converted into float)
    valid_data = list(filter(lambda x:x != None, map(convert_float, data)))
    valid_other_data = filter(lambda x:x != None, map(convert_float, other.data))
    total =  list(starmap(lambda a,b:a+b, zip(valid_data, valid_other_data)))
    return list(starmap(lambda a,b: round(a*1.0/b, 4), zip(valid_data, total)))

def f_round(data, other=2):
    """
    fcolA:f_round:number; compute round(fcolA, number)
    """
    valid_data = list(filter(lambda x:x != None, map(convert_float, data)))
    try:
        other = int(other)
    except ValueError:
        return data
    return list(map(lambda x:round(x, other), data))

def f_cumsum(data, other=None):
    """ 
    fcolA:f_cumsum; for each row in colA: sum of previous colA values + current row

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
    fcolA:f_formatunixtime:string

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
    f1:f_shift:number 

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

def f_sma(data, other=5):
    """
    Compute SMA over periods
    """
    out = []
    window = other
    if isinstance(window, str):
        window = 5
    #Make data as float
    data = list(filter(lambda x:x != None, map(convert_float, data)))
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

def f_csvmap(data, other=None):
    """
    f1:f_csvmap:csv_file

    csv_file format has to be key,value
    key being the data from f1
    value will be in the result
    since it uses a dictionary to get key,value pair, only the last match will take effect
    if there is no match, an empty string will be used
    """
    info = dict(enumerate(other.split(',')))
    #Get csv file name
    csv_file = info[0]
    #Get key for mapping or use 0
    key = int(info.get(1, 0))
    #Get value for mapping or use 1
    value = int(info.get(2, 1))
    csv_data = {}
    with open(csv_file, 'r') as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            csv_data[row[key]] = row[value]
    return [csv_data.get(i, '') for i in data]

def f_filemap(data, other=None):
    """
    f1:f_filemap:file

    file format has to be key value     
    key being the data from f1
    value will be in the result
    since it uses a dictionary to get key,value pair, only the last match will take effect
    if there is no match, an empty string will be used
    """
    file_data = {}
    info = dict(enumerate(other.split(',')))
    #Get csv file name
    filemap = info[0]
    #Get key for mapping or use 0
    key = int(info.get(1, 0))
    #Get value for mapping or use 1
    value = int(info.get(2, 1))
    with open(filemap, 'r') as file:
        reader = file.readlines()
        for row in reader:
            row = row.strip('\n').split(' ')
            file_data[row[key]] = row[value]
    return [file_data.get(i, '') for i in data]

def f_tag(data, other=None):
    """
    "f1:f_tag:value1,tag1;value2,tag2;..."
    """
    tag_d = {}
    print(data, other)
    for i in other.split(';'):
        info = dict(enumerate(map(lambda x:x.strip(), i.split(','))))
        print(info)
        tag_d[info.get(0)] = info.get(1, '-')
    print(tag_d)
    return [tag_d.get(i, '-') for i in data]

