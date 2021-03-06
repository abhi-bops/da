import argparse
from math import nan, ceil, floor, isnan
from collections import Counter
import argparse
import sys
from itertools import chain, zip_longest
from da_classes import *
from da_utils import *
from da_custom import *

g_format='kind:x:y:hue:split_interval:is_ts:subplots'
g_ex='bar:1:0:2:10:False:False --> Plot a bar chart(kind), with x-axis as column 1(x), y-axis from column 0(x), and group data by column2(hue). Split the graphs such that each graph has 10 values(split_interval) in x-axis, x-axis is not of time format(is_ts=False), Plot all data in 1 chart(subplots=False)'

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
                                            'default': None,
                                            'metavar': 'delimiter',
                                            'dest': "delim"}],
              'pipe': [['--pipe'], {'action': 'store_true',
                                    'help': "Pipe data to output"}],
              'heading': [['--heading'], {'type': str,
                                          'help': "Custom heading to use, separate headings with comma (,). Missing ones will have colN ... N->field number", 'default': None}],
              'h1': [['-h1'], {'action': 'store_true',
                               'help': "Indicates that the first line is a heading",
                               'default': False}],
              'graph': [['--graph'], {'type': str,
                                      'help': "Graph the data (experimental), information is of format - {}. ex: {}. If format is not passed, a default format is assumed".format(g_format, g_ex),
                                      'metavar': 'GRAPH_OPTION_FORMAT',
                                      'default': False,
                                      'nargs': '?'
                                      }],
              'noheading': [['--noheading'], {'action': 'store_true',
                                              'help': 'Disables printing of heading on output when used with pipe/tocsv options. Useful if the data needs to passed into sort,uniq command',
                                              'default': False}],
              'notable': [['--notable'], {'action': 'store_true',
                                              'help': 'Disables printing of data on output. Useful if the tograph is used and the data is not needed.',
                                              'default': False}],
              'fast': [['--fast'],
                       {'action':'store_true',
                        'help': 'Attempts to be faster in producing the ascii table output, by pre-assuming cell widths of table. Use --width to set custom cell widths.'}],
              'rich': [['--rich'],
                     {'action':'store_true',
                              'help': 'fancy table printing, only works if the rich python module is installed (Does not install by default).'}]}
    #Set of common options to all
    commongroup = parser.add_argument_group("Common options")
    commongroup.add_argument('-h1', action='store_true', help="Indicates that the first line is a heading", default=False,
                             dest="com_h1")
    commongroup.add_argument('-d', '--delim', type=str, help="Delimiter to split the input fields. Default is space '%(default)s'",
                             default=' ',
                             metavar='delimiter',
                             dest="com_delim")
    commongroup.add_argument(*args_d['fields'][0], **args_d['fields'][1])
    commongroup.add_argument('--fast', action='store_true',
                             help='Attempts to be faster in producing the ascii table output, by pre-assuming cell widths of table. Use --width to set custom cell widths.')

    #This set is to reflect tablegroup's options so that it can run as default
    parser.add_argument('--pipe', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--tocsv', action='store_true', help=argparse.SUPPRESS, default=None)
    parser.add_argument('--graph', type=str, help=argparse.SUPPRESS)
    #Do not include list inputs here https://stackoverflow.com/questions/35898944/python-subparser-parsing-with-nargs
    parser.add_argument('--heading', type=str, help=argparse.SUPPRESS, default=None)
    
    actions = parser.add_subparsers(title="Available actions (Use -h after action for more options)", metavar='', dest='action')

    #table; options
    tablegroup = actions.add_parser(name='table', help="Tabulate the input fields (Default)",
                                    description="Pretty print the input data as tables. Columns can be chosen to print. By default, all columns are printed")
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'heading', 'h1', 'noheading', 'notable', 'graph', 'fast', 'rich']:
        tablegroup.add_argument(*args_d[i][0], **args_d[i][1])        

    #summary: options
    aggregategroup = actions.add_parser(name='summary', help="Similar to pandas dataframe describe(), gives a statistical summary of the result, All values are treated as continous data")
    for i in ['delim', 'h1', 'heading', 'rich']:
        aggregategroup.add_argument(*args_d[i][0], **args_d[i][1])

    #hist: options
    histgroup = actions.add_parser(name='hist', help="Get the histogram of the input fields",
                                   description="If bins, size, count is provided. Bins is preferred over size and size over count. If none of them is provided, default is to use count=40")
    for i in ['fields', 'delim', 'heading', 'h1', 'notable', 'rich', 'graph']:
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
    for i in ['delim', 'heading', 'h1', 'notable', 'rich', 'graph', 'tocsv', 'pipe']:
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
    
    #transform: options
    transform_function_l = ['add', 'divide', 'div', 'floordiv', 'subtract', 'sub',
                            'multiply', 'mul', 'gt', 'lt', 'ge', 'le', 'eq', 'mod',
                            'dummy', 'sample']
    transformgroup = actions.add_parser(name='transform', help="Transform columns by running functions on them")
    for i in ['delim', 'heading', 'h1', 'noheading', 'tocsv', 'pipe', 'fields']:
        transformgroup.add_argument(*args_d[i][0], **args_d[i][1])
    transformgroup.add_argument('--function', action="append", help="function to run on the field. 1 field and one1 action is supported. Format is fieldNumber:function:arguments. Available functions are {}. Custom functions can also be used from eda_custom_functions.py".format(transform_function_l), metavar="format")

    args = vars(parser.parse_args())
    # If no options are provided, print the help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)
    return args


if __name__=='__main__':
    #Get all the arguments
    args = parse_args()
    ##Common fields, prefer action's option first otherwise use the common option
    fields = args.get('fields') or args.get('com_fields')
    h1 = args.get('h1') or args.get('com_h1')
    delim = args.get('delim') or args.get('com_delim')
    #If --graph is not used, it will have the default False
    # If only the --graph is used, it will have None
    # If --graph 'g_options' , it will be a string
    tograph = args.get('graph')
    if tograph != False:
        #Return g_options if passed otherwise true (if g_options is None)
        tograph = tograph or True
    tocsv = args.get('tocsv') or args.get('com_tocsv')
    pipe = args.get('pipe') or args.get('com_pipe')
    rich = args.get('rich') or args.get('com_rich')
    heading = args.get('heading') or args.get('com_heading')
    #If heading is provided, it will be comma separated, split at commas
    if heading:
        heading = heading.split(',')
    noheading = args.get('noheading') or args.get('com_noheading')
    notable = args.get('notable') or args.get('com_notable')

    #Action to do
    action = args.get('action') 
    #Table fields
    fast = args.get('fast')
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
    
    #Transform fields
    function = args.get('function')

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
    if action == 'transform':
        t_list = get_transform_req(function)
        f1 = chain.from_iterable([f['fields'] for f in t_list])
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

    #Handle graphing related steps
    # If tograph is False, then the option was not selected
    # If action is hist, no need to do anything, hist has it's own g_options setup
    g_options = {}
    if tograph != False and action!='hist':
        if isinstance(tograph, (str)):
            g_options = dict(zip_longest(g_format.split(':'), tograph.split(':')))
            g_options['y'] = list(map(int, g_options['y'].split(','))) #columns for values to plot
            g_options['x'] = int(g_options['x'])
            for i in ['is_ts', 'subplots']:
                if g_options[i] == 'True':
                    g_options[i] = True
                else:
                    g_options[i] = False

    #Creating the table object
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
                  colsummary=colsummary)
    else:
        T = Table(src='-', delim=delim, fields=fields, h1=h1, heading=heading)

    #Actions to do
    #Pivoting
    if action == 'pivot':
        #If only column ind is not given, it is pivot and summary for each row combination, so use pivot2
        if not columnind:
            T.pivot2()
        #Else standard pivoting using pivot
        else:
            T.pivot()
        if not notable:
            if fast:
                print(T.fast_ascii_table())
            elif rich:
                out = rich_print_table(T.data, T.heading)
                print(out)
            else:
                print(T.to_ascii_table())
        #Get pivotdata for graphing, no summaries
        output = T.get_pivotdata()
        #If graphing is requested
        if tograph:
            is_ts = False
            if g_options:
                is_ts = g_options['is_ts'] 
            y = range(1, len(output['data'][0]))
            title = "Heatmap of pivot result"
            g_options = {'kind': 'heatmap', 'x': 0, 'y': y,
                         'split_interval': 50,
                         'is_ts': is_ts, 'subplots': False, 'title': title}
            g=Graph(data=output['data'], heading=output['heading'], **g_options)
            graphs = g.plot()
            for fig in graphs:
                imgcat(fig)

    #Simple ASCII Table
    if not action or action == 'table':
        if not notable:
            if pipe:
                T.pipe(disable_heading=noheading)
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
        if tograph:
            title = "Graph"
            x = g_options.get('x', 0)
            y = g_options.get('y', [1])
            fields = [x, *y]
            data = T.get_fields(fields)
            df_data = {v[0]:v[1] for _, v in data.items()}
            if not g_options:
                g_options = {'kind': 'line', 'x': 0, 'y': [1],
                             'split_interval': -1, 'is_ts': False,
                             'subplots': False, 'title': title}
            #If scatter plot disable splitting
            if g_options['kind'] == 'scatter':
                g_options['split_interval'] = -1
            g=Graph(data=df_data, **g_options)
            graphs = g.plot()
            for fig in graphs:
                imgcat(fig)

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
        for t in t_list:
            #Get the column name, or use dummy name
            name = t.get('alias', '{}({},{})'.format(t['func'],
                                                     'a', 'b'))
            #If param is a number, use it, if it's a field, get the Column object of that field
            t['params'] = t['params'] if not t['is_field'] else Column(pTable[t['fields'][0]][1], name=pTable[t['fields'][0]][0])
            #Hack to check if it is a categorical column
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
            if t['alias'] == '':
                t['alias'] = '{}({},{})'.format(t['func'],
                                                 pTable[t['fields'][0]][0],
                                                 param_name)
            tCol = Column(pTable[t['fields'][0]][1],
                          name=t['alias'],
                          categorical=categorical)
            #Apply transform
            tCol.apply_transform(t['func'],
                                 params)
            #If there is a chain function, follow the same process as above one-after-another
            if t['chain']:
                for c in t['chain']:
                    c['params'] = c['params'] if not c['is_field'] else Column(pTable[c['fields'][0]][1])
                    tCol.apply_transform(c['func'], c['params'])
            tTable.add(tCol)
        if pipe:
            tTable.pipe(disable_heading=noheading)
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
            heading=['bins', 'count', 'share%']
            #Categorical columns will return nan, so data is [], so we will use counter
            if not data:
                #Initialise a list to collect the rows
                hist_table = []
                counter = Counter(Cv[1])
                for k, v in counter.items():
                    share = round(int(v)/len(Cv[1])*100,2)
                    row = [k, v, share]
                    if asciigraph:
                        width = 20
                        barlength = int((width*share)/100)
                        bar = bar_char*barlength + ' '*(width-barlength)
                        row.append(bar)
                    hist_table.append(row)
            else:
                hist_table = []
                total_count = len(data)
                bin_d = get_result(data, **kwargs)
                if not bin_d:
                    continue
                #Start is taken as the minimum bin-1
                i_old=sorted(bin_d)[0]-1
                field_len = max([len(str(k)) for k in bin_d.keys()])*2 + 3
                hist_table = []
                for i in sorted(bin_d.keys()):
                    bin_s = "({}-{}]".format(i_old, i)
                    share = round(bin_d[i]*100/total_count)
                    row = [bin_s, bin_d[i], share]
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
                    print(rich_print_table(data=hist_table, heading=heading, title=title, justify={0: 'left', 3: 'left'}))
                else:
                    print(title)
                    #Print the table
                    hT = Table(data=hist_table, heading=heading)
                    print(hT.to_ascii_table())
            #If graphing is requested
            if tograph:
                output = {'heading': heading, 'data': hist_table}
                g_options = {'kind': 'bar', 'x': '0', 'y': '1', 'subplots': True, 'split_interval': -1, 'vert': False, 'title': title}
                g=Graph(data=hist_table, heading=heading, **g_options)
                graphs = g.plot()
                for fig in graphs:
                    imgcat(fig)


                    
                
