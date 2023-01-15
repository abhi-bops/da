#!/usr/bin/python3

#Python inbuilt functions
from math import isnan
from collections import Counter
import sys
from itertools import chain, combinations
import logging
#The classes which make the script work
from da_classes import *
#Commonly used functions
from da_utils import *
#Custom functions
from da_custom import *
#from da_graphs import * (Disabling this to speed up the script)
from da_classes import *
#Arguments are described here
from da_help import parse_args

#Logging settings
logger = logging.getLogger('da_tool')
logger.setLevel(logging.DEBUG)

#Character for CLI bar graphs
if sys.getfilesystemencoding() == 'utf-8':
    bar_char = '█'
else:
    bar_char = 'o'

if __name__=='__main__':

    #Input arguments
    args = parse_args()
    skip_rows = args.get('skip_rows')
    h1 = args.get('h1') 
    delim = args.get('delim') 
    heading = args.get('heading') 
    #If heading is provided, it will be comma separated, split at commas
    if heading:
        heading = heading.split(',')

    #Ouptut fields
    noheading = args.get('noheading')
    fast = args.get('fast')
    rich = args.get('rich')
    tocsv = args.get('tocsv') 
    #Check if delims for output are passed
    pipewith = args.get('pipewith') #There will be a delimter here
    pipe = args.get('pipe') #A True or False (delim=space)
    #Assign the right delim, pipewith delim is preferred over ' '
    if pipewith:
        pipe = pipewith
    #if pipe option is passed
    elif pipe:
        pipe = ' '
    #If pipe or pipewith is not passed, don't pipe the output
    else:
        pipe = False

    #Action to do
    action = args.get('action') 
    #Hist fields
    minv = args.get('minv')
    maxv = args.get('maxv')
    bins = args.get('bins')
    size = args.get('size')
    count = args.get('count')
    summary = args.get('summary')
    
    #Pivot fields
    rowind = args.get('rowind')
    columnind = args.get('columnind')
    valueind = args.get('valueind')
    aggfunc = args.get('aggfunc')
    summary = args.get('summary')
    summaryf = args.get('summaryf')
    rowsummary = args.get('rowsummary')
    colsummary = args.get('colsummary')

    #topn fields
    topind = args.get('topind')
    n = args.get('n')

    #Transform fields
    function = args.get('function')

    #Sort fields
    sort_key = args.get('sort_key')
    reverse = args.get('desc')

    #Filter fields
    pattern = args.get('pattern')
    tag = args.get('tag')

    #Handle fields
    ##Common fields, prefer action's option first otherwise use the common option
    fields = args.get('fields')

    #Handle field format input
    if fields != None:
        fields = get_fields(fields)
    #Getting the fields based on the actions
    if action == 'pivot':
        #If all the indices are not given, it is likely a standard sort | uniq -c result
        if columnind == None and rowind == None and valueind == None:
            rowind=1
            columnind=2
            valueind=0
        fields = list([rowind, columnind, valueind])
    #Add the row and value index to the fields
    if action == "group":
        fields = list([*rowind, *valueind])
    if action == "topn":
        fields = list([*rowind, *topind, *valueind])
    if action == 'transform':
        #Parse the transform function string
        # each --function param is a item in t_list
        t_list = get_transform_req(function)
        #f1->field numnber to start the operation on 
        f1 = chain.from_iterable([f['fields'] for f in t_list])
        #f2->if the param is a field, get the field numner
        f2 = [f['params'] for f in t_list if f['is_field']]
        #Get the fields that are used in the transform
        f_fields = list(set(chain(f1, f2)))
        #If fields is passed, append it to that that
        if fields:
            fields = fields + f_fields
        #else fields = the transform fields
        else:
            fields = f_fields

    #If there were none, use the special empty list
    if fields == None:
        fields = []
    fields = get_uniq_fields(fields)

    #Creating the table object
    #handle pivot separately, rest is default Table object
    if action == 'pivot':
        #Only change rowsummary/colsummary, when it is different, use xor to check that
        if rowsummary ^ colsummary:
            rowsummary = rowsummary
            colsummary = colsummary
        #otherwise both are true
        else:
            rowsummary = True
            colsummary = True
        T = Table(src='-', delim=delim, fields=fields, h1=h1,
                  row_k=rowind, col_k=columnind,
                  val_k=valueind, f=aggfunc, summary=summary,
                  heading=heading, summaryf=summaryf, rowsummary=rowsummary,
                  colsummary=colsummary, skip_rows=skip_rows, action=action)
    elif action == 'group':
        T = Table(src='-', delim=delim, fields=fields, h1=h1,
                  row_k=rowind, val_k=valueind, f=aggfunc, 
                  heading=heading, skip_rows=skip_rows, action=action)
    elif action == 'topn':
        T = Table(src='-', delim=delim, fields=fields, h1=h1,
                  row_k=rowind, val_k=valueind, f=aggfunc, 
                  heading=heading, top_k=topind, n=n, skip_rows=skip_rows, action=action)
    else:
        T = Table(src='-', delim=delim, fields=fields, h1=h1, 
                  heading=heading, skip_rows=skip_rows, action=action)

    #Actions to do
    #grouping
    if action == 'group':
        T.group()
        if fast:
            print(T.fast_ascii_table())
        elif rich:
            out = rich_print_table(T.data, T.heading)
            print(out)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        else:
            print(T.to_ascii_table())
    
    #Finding Top n
    if action == 'topn':
        T.get_topn()
        if fast:
            print(T.fast_ascii_table())
        elif rich:
            out = rich_print_table(T.data, T.heading)           
            print(out)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        else:
            print(T.to_ascii_table())

    #Pivoting
    if action == 'pivot':
        T.pivot()
        if fast:
            print(T.fast_ascii_table())
        elif rich:
            out = rich_print_table(T.data, T.heading)
            print(out)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        else:
            print(T.to_ascii_table())

    #Transposing
    if action == 'transpose':
        T = T.transpose()
        if pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif fast:
            #Handle BrokenPipeError
            # https://stackoverflow.com/a/26738736
            try:
                print(T.fast_ascii_table(), flush=True)
            except (BrokenPipeError):
                pass
            sys.stderr.close()
        else:
            if rich:
                out = rich_print_table(T.data, T.heading)
                print(out)
                if out == None:
                    print(T.to_ascii_table(), flush=True)
            else:
                print(T.to_ascii_table(), flush=True)    
    
    #Simple ASCII Table
    if not action or action == 'table':
        if pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif fast:
            #Handle BrokenPipeError
            # https://stackoverflow.com/a/26738736
            try:
                print(T.fast_ascii_table(), flush=True)
            except (BrokenPipeError):
                pass
            sys.stderr.close()
        else:
            if rich:
                out = rich_print_table(T.data, T.heading)
                print(out)
                if out == None:
                    print(T.to_ascii_table(), flush=True)
            else:
                print(T.to_ascii_table(), flush=True)        

    #Summarising
    if action == 'summary':
        data = T.get_fields(fields)
        result = []
        summary_data_continous = {'heading': [], 'data': []}
        summary_data_categorical = {'heading': [], 'data': []}
        for k, v in data.items():
            C = Column(data=v[1], name=v[0])
            dtype, data = C.summary()
            Csum = transpose_rows(data)
            if not Csum:
                continue
            if dtype == 'continous':
                summary_data_continous['heading'] = ['field'] + Csum[0]
                summary_data_continous['data'].append([C.name] + Csum[1])
            else:
                summary_data_categorical['heading'] = ['field'] + Csum[0]
                summary_data_categorical['data'].append([C.name] + Csum[1])                
        if summary_data_continous['data']:
            Tsum = Table(data=summary_data_continous['data'],
                         heading=summary_data_continous['heading'])
            if rich:
                print(rich_print_table(summary_data_continous['data'],
                                   summary_data_continous['heading']))
            else:
                print(Tsum.to_ascii_table(repeat_heading=30))
        if summary_data_categorical['data']:
            Tsum = Table(data=summary_data_categorical['data'],
                         heading=summary_data_categorical['heading'])
            if rich:
                print(rich_print_table(summary_data_categorical['data'],
                                   summary_data_categorical['heading']))
            else:
                print(Tsum.to_ascii_table(repeat_heading=30))
        
    #Transforming
    if action == 'transform':
        pTable = T.get_fields(fields)
        tTable = ColumnTable(name='Transformed')
        for pk, pv in pTable.items():
            pCol = Column(pv[1], name=pv[0], categorical=True)
            tTable.add(pCol)
        #Each item in t_list is the parsed transform string of --function input
        # which defines the actions to follow 
        for t in t_list:
            #Not needed: Get the column name, or use dummy name created by the function-name and (a,b) 
            #name = t.get('alias', '{}({},{})'.format(t['func'],
            #                                         'a', 'b'))

            #If param is a number, use it, if it's a field, get the Column object of that field
            if t['is_field']:
                t['params'] = Column(pTable[t['params']][1], name=pTable[t['params']][0])
            else:
                t['params'] = t['params']
            # Hack to check if it is a categorical column
            #Check if 'params' can be converted into float
            categorical = False
            if not t['is_field']:            
                try:
                    #If it can be, then its likely a numerical column
                    params = float(t['params'])
                except ValueError:
                    #Else its intended to be a categorical column
                    params = t['params']
                    categorical = True
            else:
                params = t['params']
            #Get the data for the fields where transform needs to be applied
            # and create a column object, name it using alias key
            if isinstance(t['params'], (Column)):
                param_name = t['params'].name
            else:
                param_name = t['params']
            #If column name is not defined, create one of the format func(a,b)
            # a is field/col name
            # b can be param of field/col name
            if t['alias'] == '':
                t['alias'] = '{}({},{})'.format(t['func'],
                                                 pTable[t['fields'][0]][0],
                                                 param_name)
            #Create the column
            #pTable(fieldN) -> gets the data
            # fieldN is the field on which we start the transformation
            tCol = Column(pTable[t['fields'][0]][1],
                          name=t['alias'],
                          categorical=categorical)
            #Apply transform to the column
            tCol.apply_transform(t['func'],
                                 params)
            #If there is a chain function, follow the same process as above one-after-another
            if t['chain']:
                for c in t['chain']:
                    #If param is a number, use it, if it's a field, get the Column object of that field
                    if c['is_field']:
                        c['params'] = Column(pTable[c['params']][1])
                    else:
                        c['params'] = c['params']
                    tCol.apply_transform(c['func'], c['params'])
            #Add the transformed columns into the table
            tTable.add(tCol)
        #output formatting
        if pipe:
            tTable.pipe(disable_heading=noheading, delim=pipe)
        elif tocsv:
            tTable.tocsv(disable_heading=noheading)
        else:
            print(tTable.to_ascii_table(), flush=True)

    #Histogram
    if action == 'hist':
        #Gather all arguments, passing it as **kwargs to functions
        kwargs = {'minv': minv, 'maxv': maxv, 'count': count,
                  'bin_size': size, 'bins': bins}
        #Get only the data from the fields
        Tdata = T.get_fields(fields)
        asciigraph = True
        #k->field number; v -> [column_name, [values]]
        for Ck, Cv in Tdata.items():
            #The column name
            name = Cv[0]
            C = Column(data=Cv[1], name=name)
            data = list(filter(lambda x: not isnan(x), C.data))
            heading=['bins', 'count', 'share%', 'cumshare%']
            #Categorical columns will return nan, so data is [], so we will use counter
            if not data:
                #Initialise a list to collect the rows
                hist_table = []
                counter = Counter(Cv[1])
                cumshare = 0
                for k, v in counter.items():
                    share = round(int(v)/len(Cv[1])*100,2)
                    cumshare += share
                    row = [k, v, share, cumshare]
                    if asciigraph:
                        width = 20
                        barlength = int((width*share)/100)
                        bar = bar_char*barlength + ' '*(width-barlength)
                        row.append(bar)
                    hist_table.append(row)
            else:
                hist_table = []
                total_count = len(data)
                bin_d = get_hist(data, **kwargs)
                if not bin_d:
                    continue
                #Start is taken as the minimum bin-1
                i_old=sorted(bin_d)[0]-1
                field_len = max([len(str(k)) for k in bin_d.keys()])*2 + 3
                hist_table = []
                cumshare = 0
                for i in sorted(bin_d.keys()):
                    bin_s = "({}-{}]".format(i_old, i)
                    share = round(bin_d[i]*100/total_count)
                    cumshare += share
                    row = [bin_s, bin_d[i], share, cumshare]
                    if asciigraph:
                        width = 20
                        barlength = int((width*share)/100)
                        bar = bar_char*barlength + ' '*(width-barlength)
                        row.append(bar)
                    hist_table.append(row)
                    i_old = i
            title = "Histogram of {}".format(name)
            if asciigraph:
                heading.append("histogram")
            if rich:
                print(rich_print_table(data=hist_table, heading=heading, title=title, justify={0: 'left', 4: 'left'}))
            else:
                print(title)
                #Print the table
                hT = Table(data=hist_table, heading=heading)
                print(hT.to_ascii_table())

    #Filtering rows
    if action == 'filter':
        T.filterrows(pattern, tag=tag)
        if fast:
            print(T.fast_ascii_table())
        elif rich:
            out = rich_print_table(T.data, T.heading)
            print(out)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        else:
            print(T.to_ascii_table(), flush=True)  
    
    #Sorting rows by column
    if action == 'sort':
        T.sort(key=sort_key, reverse=reverse) 
        if fast:
            print(T.fast_ascii_table())
        elif rich:
            out = rich_print_table(T.data, T.heading)
            print(out)
        elif tocsv:
            T.tocsv(disable_heading=noheading)
        elif pipe:
            T.pipe(disable_heading=noheading, delim=pipe)
        else:
            print(T.to_ascii_table(), flush=True) 

    if action == 'corr':
        #Get only the data from the fields
        Tdata = T.get_fields(fields)
        cor_d = defaultdict(dict)
        for i in combinations(fields, 2):
            x = i[0]
            y = i[1]
            x_heading = Tdata.get(x)[0]
            y_heading = Tdata.get(y)[0]
            cor_d[x_heading][x_heading] = 1
            cor_d[y_heading][y_heading] = 1
            Cx = Column(Tdata[x][1])
            Cy = Column(Tdata[y][1])
            cor_d[x_heading][y_heading] = round(correlation(Cx, Cy), 3)
            cor_d[y_heading][x_heading] = cor_d[x_heading][y_heading]
        print(cor_d)
        heading = cor_d.keys()
        for i in heading:
            print('\t{}'.format(i), end='')
        print()
        for i in heading:
            print('{}\t'.format(i), end='')
            for j in heading:
                print('{}\t'.format(cor_d[i][j]), end='')
            print()


