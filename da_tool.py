#!/usr/bin/python3

import argparse
from math import nan, ceil, floor, isnan
from collections import Counter
import argparse
import sys
from itertools import chain, zip_longest
from da_classes import *
from da_utils import *
from da_custom import *
from da_graphs import *

if sys.getfilesystemencoding() == 'utf-8':
    bar_char = '█'
else:
    bar_char = 'o'

def parse_args():
    parser = argparse.ArgumentParser(description="Pass arguments to matrix creator. By default data is tabulated in a simple readable way with boundaries, if pivot flag is used, data is pivoted based on the pivot options passed")

    #Dictionary with options and info for reusing multiple times
    args_d = {'fields': [['-f', '--fields'], {'type': str,
                                              'help': "Field numbers to show in result, (numbers separated by comma or range separated by dash). Default is to show all.",
                                              'default': None,
                                              'metavar': '1,2,3,... or 1-3,5,8-10'}],
              'tocsv': [['--tocsv'], {'action': 'store_true',
                                      'help': "write output as a csv to terminal",
                                      'default': None}],
              'delim': [['-d', '--delim'], {'type': str,
                                            'help': "Delimiter to split the input fields. Default is space '%(default)s'",
                                            'default': ' ',
                                            'metavar': 'delimiter',
                                            'dest': "delim"}],
              'pipe': [['--pipe'], {'action': 'store_true',
                                    'help': "Pipe data to output with delim as space ' '"}],
              'pipewith': [['--pipewith'], {'type': str,
                                    'help': "Pipe data to output with the delim",
                                    'default': None,
                                    'metavar': 'delimiter',
                                    'dest': 'pipewith'}],
              'heading': [['--heading'], {'type': str,
                                          'help': "Custom heading to use, separate headings with comma (,). Missing ones will have colN ... N->field number", 'default': None}],
              'h1': [['-h1'], {'action': 'store_true',
                               'help': "Indicates that the first line is a heading",
                               'default': False}],
              'skip_rows': [['--skip-rows'], {'type': int,
                                              'help': 'Skip rows',
                                              'default': 0}],
              'noheading': [['--noheading'], {'action': 'store_true',
                                              'help': 'Disables printing of heading on output when used with pipe/pipewith options. Useful if the data needs to passed into sort,uniq commands',
                                              'default': False}],
              'fast': [['--fast'],
                       {'action':'store_true',
                        'help': 'Attempts to be faster in producing the ascii table output, by pre-assuming cell widths of table. Use --width to set custom cell widths.'}],
              'rich': [['--rich'],
                     {'action':'store_true',
                              'help': 'fancy table printing, only works if the rich python module is installed (Does not install by default).'}]}

    #This set is to reflect tablegroup's options so that it can run as default
    parser.add_argument('--pipe', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--tocsv', action='store_true', help=argparse.SUPPRESS, default=None)
    #Do not include list inputs here https://stackoverflow.com/questions/35898944/python-subparser-parsing-with-nargs
    parser.add_argument('--heading', type=str, help=argparse.SUPPRESS, default=None)
    
    actions = parser.add_subparsers(title="Available actions (Use -h after action for more options)", metavar='', dest='action')

    #table; options
    tablegroup = actions.add_parser(name='table', help="Tabulate the input fields",
                                    description="Pretty print the input data as tables. Columns can be chosen to print. By default, all columns are printed")
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'pipewith', 'heading', 'skip_rows', 'h1', 'notable', 'fast', 'rich']:
        tablegroup.add_argument(*args_d[i][0], **args_d[i][1])    
    tablegroup.add_argument('--transpose', action="store_true",
                            help="Transpose the table",
                            default=False)   

    #summary: options
    aggregategroup = actions.add_parser(name='summary', help="Similar to pandas dataframe describe(), gives a statistical summary of the result, All values are treated as continous data")
    for i in ['fields', 'delim', 'skip_rows', 'h1', 'heading', 'rich']:
        aggregategroup.add_argument(*args_d[i][0], **args_d[i][1])

    #hist: options
    histgroup = actions.add_parser(name='hist', help="Get the histogram of the input fields",
                                   description="If bins, size, count is provided. Bins is preferred over size and size over count. If none of them is provided, default is to use count=40")
    for i in ['fields', 'delim', 'heading', 'skip_rows', 'h1', 'notable', 'rich']:
        histgroup.add_argument(*args_d[i][0], **args_d[i][1])
    histgroup.add_argument('--min', type=int, help="the lowest of the bins. Default is the minimum of the data.", metavar='N')
    histgroup.add_argument('--max', type=int, help="the highest of the bins, highest value in set. Default is the maximum of the data.", metavar='N')
    histgroup.add_argument("--bins", type=int, nargs="+",
                           help="Specify the bins manually separated by space. They act as the upper edge of the bin. The lower edge is the previous bin or the lowest-1 value. Has to be intergers",
                           default=[])
    histgroup.add_argument("--size", type=int, help="Size of each bins.", metavar='N')
    histgroup.add_argument('--count', type=int, help="Count of histogram bins to have. Default is %(default)s.", default=20, metavar='N')
    histgroup.add_argument('--summary', action='store_true',
                           help="Add statistical summary data",
                           default=False)

    #pivot: options
    pivotgroup = actions.add_parser(name='pivot', help="Pivot the input data",
                                    description="Pivot the input data by creating row and column indices and computing the value for each using input fields.")
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'notable', 'rich', 'tocsv', 'pipe', 'pipewith']:
        pivotgroup.add_argument(*args_d[i][0], **args_d[i][1])
    pivotgroup.add_argument('-r', '--rowind', type=int, help="Position of the data that needs to be used as row index. Starts from 0",
                            metavar='N',
                            default=None)
    pivotgroup.add_argument('-c', '--columnind', type=int, help="Position of the data that needs to be used as column index. Starts from 0.", default=None, metavar='N')
    pivotgroup.add_argument('-v', '--valueind', type=int, help="Position of data that needs to be added as value to use on the cell. Starts from 0.", default=None, metavar='N')
    pivotgroup.add_argument('--aggfunc', type=str, help="Agg function to use if there are multiple values for the row x column combination. Default is %(default)s",
                            choices=['first', 'last', 'concat', 'max', 'min', 'sum', 'count', 'mean', 'median', 'stdev'],
                            default='first')
    pivotgroup.add_argument('--summary', action='store_true',
                            help="Add a summary column using the same agg function, the summary is on the resulting cells with the aggfunc applied on them.",
                            default=False)
    pivotgroup.add_argument('--summaryf', type=str,
                            help="Running summary functions on the results, use this if you want multiple summaries",
                            default=None)
    pivotgroup.add_argument('--rowsummary', action='store_true',
                            help="Only print the row summary, default is to print both column and row summaries",
                            default=False)
    pivotgroup.add_argument('--colsummary', action='store_true',
                            help="Only print the column summary, default is to print both column and row summaries",
                            default=False)

    #group: options
    groupgroup = actions.add_parser(name='group', help="Group the input data by a column and run agg functions on the grouped data",
                                    description="Group the input data by creating row and column indices and computing the value for each using input fields.")
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'notable', 'rich', 'tocsv', 'pipe', 'pipewith', 'noheading']:
        groupgroup.add_argument(*args_d[i][0], **args_d[i][1])
    groupgroup.add_argument('-r', '--rowind', nargs="+", type=int, help="Position of the data that needs to be used as row index. Starts from 0",
                            metavar='N',
                            default=None)
    groupgroup.add_argument('-v', '--valueind', nargs="+", type=int, help="Position of data that needs to be added as value to use on the cell. Starts from 0.", default=None, metavar='N')
    groupgroup.add_argument('--aggfunc', nargs="+", type=str, help="Agg function to use if there are multiple values for the row x column combination. Default is %(default)s",
                            choices=['first', 'last', 'concat', 'max', 'min', 'sum', 'count', 'mean', 'median', 'stdev'],
                            default=['count'])
    #groupgroup.add_argument('--aggfunc', action="append", help="""function to run on the field. one field and one action is supported. 
    #Format is fieldNumber:function1,function2. fieldNumber is based on the input field number, and numbering starts from 0. 
    #Available functions are {}""".format(transform_function_l), metavar="format")

    #topn: options
    topngroup = actions.add_parser(name='topn', help="Select topn results by aggfunction",
                                    description="Group the input data by creating row and column indices and computing the value for each using input fields.")
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'notable', 'rich', 'tocsv', 'pipe', 'pipewith', 'noheading']:
        topngroup.add_argument(*args_d[i][0], **args_d[i][1])
    topngroup.add_argument('-n', type=int, help="How many of topn to show",
                            metavar='N',
                            default=5)   
    topngroup.add_argument('-r', '--rowind', nargs="+", type=int, help="Position of the data that needs to be used as row index. Starts from 0",
                            metavar='N',
                            default=None)
    topngroup.add_argument('-t', '--topind', nargs="+", type=int, help="Position of the data that needs to be used as row index. Starts from 0",
                            metavar='N',
                            default=None)
    topngroup.add_argument('-v', '--valueind', nargs="+", type=int, help="Position of data that needs to be added as value to use on the cell. Starts from 0.", default=None, metavar='N')
    topngroup.add_argument('--aggfunc', nargs="+", type=str, help="Agg function to use if there are multiple values for the row x column combination. Default is %(default)s",
                            choices=['first', 'last', 'concat', 'max', 'min', 'sum', 'count', 'mean', 'median', 'stdev'],
                            default=['count'])

    #transform: options
    transform_function_l = ['add', 'divide', 'div', 'floordiv', 'subtract', 'sub',
                            'multiply', 'mul', 'gt', 'lt', 'ge', 'le', 'eq', 'mod',
                            'sample', 'concat']
    transformgroup = actions.add_parser(name='transform', help="Transform columns by running functions on them")
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'tocsv', 'pipe', 'pipewith', 'fields', 'noheading']:
        transformgroup.add_argument(*args_d[i][0], **args_d[i][1])
    transformgroup.add_argument('--function', action="append", help="""function to run on the field. one field and one action is supported. 
    Format is fieldNumber:function:arguments. fieldNumber is based on the input field number, and numbering starts from 0. 
    In-built functions are {}. Custom functions from da_custom.py can also be used""".format(transform_function_l), metavar="format")

    args = vars(parser.parse_args())
    # If no options are provided, print the help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)
    return args

if __name__=='__main__':
    #Get all the arguments
    args = parse_args()
    skip_rows = args.get('skip_rows')
    h1 = args.get('h1') 
    delim = args.get('delim') 
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
    rich = args.get('rich')
    heading = args.get('heading') 
    #If heading is provided, it will be comma separated, split at commas
    if heading:
        heading = heading.split(',')
    noheading = args.get('noheading')
    notable = args.get('notable')

    #Action to do
    action = args.get('action') 
    #Table fields
    fast = args.get('fast')
    transpose = args.get('transpose')
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

    #Handle fields
    ##Common fields, prefer action's option first otherwise use the common option
    fields = args.get('fields')

    #Handle field format input
    if fields:
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
        if summaryf:
            summaryf = [f.strip() for f in summaryf.split(',')]
        #Only change rowsummary/colsummary, when it is different, use xor to check that
        if rowsummary ^ colsummary:
            rowsummary = rowsummary
            colsummary = colsummary
        #otherwise both are true
        else:
            rowsummary = True
            colsummary = True
        T = Pivot(src='-', delim=delim, fields=fields, h1=h1,
                  row_k=rowind, col_k=columnind,
                  val_k=valueind, f=aggfunc, summary=summary,
                  heading=heading, summaryf=summaryf, rowsummary=rowsummary,
                  colsummary=colsummary, skip_rows=skip_rows)
    elif action == 'group':
        T = Group(src='-', delim=delim, fields=fields, h1=h1,
                  row_k=rowind, val_k=valueind, f=aggfunc, 
                  heading=heading, skip_rows=skip_rows)
    elif action == 'topn':
        T = Topn(src='-', delim=delim, fields=fields, h1=h1,
                  row_k=rowind, val_k=valueind, f=aggfunc, 
                  heading=heading, top_k=topind, n=n, skip_rows=skip_rows)
    else:
        T = Table(src='-', delim=delim, fields=fields, h1=h1, heading=heading, skip_rows=skip_rows)

    #Actions to do
    if action == 'group':
        T.group()
        if not notable:
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

    if action == 'topn':
        T.get_topn()
        if not notable:
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
        if not notable:
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

    #Simple ASCII Table
    if not action or action == 'table':
        if transpose:
            T = T.transpose()
        if not notable:
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
            print(tTable.to_ascii_table())

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
            if not notable:
                if rich:
                    print(rich_print_table(data=hist_table, heading=heading, title=title, justify={0: 'left', 4: 'left'}))
                else:
                    print(title)
                    #Print the table
                    hT = Table(data=hist_table, heading=heading)
                    print(hT.to_ascii_table())


                    
                
