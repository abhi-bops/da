import argparse
import sys

class dotdict(dict):
    """dot.notation access to dictionary attributes
    https://stackoverflow.com/a/23689767
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

desc = dotdict()
desc['main'] = """
Suite of actions to work on tabular data. Intended to be a single python script using the default
libraries as much as possible.

Includes "actions" to perform on the tabular data. Each action is associated with it's set of 
options to facilitate it's working. Also includes general options to parse interpret the incoming data
"""

desc['table'] = """
Pretty print the input data as tables. Columns can be chosen to print. By default, all columns 
are printed.
"""

desc['hist'] = """
Creates Histogram out of the input fields
"""

desc['pivot'] = """
Pivot the input data by creating row and column indices and computing the value for each using input fields.
"""

desc ['group'] = """
Group columns (got from -r) and apply the aggregate functions (got from --aagfunc) on the data from columns (got from -v)
"""

desc ['topn'] = """
Find the top N (limted by -n) items (from -t column) for a group (from -r column) 
based on the data (from values in -v column) by applying the aggregation function (using --aggfunc)
"""

def parse_args():
    parser = argparse.ArgumentParser(description=desc.main)

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
                                    description=desc.table)
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'pipewith', 'heading', 'skip_rows', 'h1', 'fast', 'rich', 'noheading']:
        tablegroup.add_argument(*args_d[i][0], **args_d[i][1])    
    
    #transpose: options
    transposegroup = actions.add_parser(name='transpose', help="Transpose rows into columns")
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'pipewith', 'heading', 'skip_rows', 'h1', 'fast', 'rich', 'noheading']:
        transposegroup.add_argument(*args_d[i][0], **args_d[i][1]) 

    #filter: options
    filtergroup = actions.add_parser(name='filter', help="Filter rows from table based on condition")
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'pipewith', 'heading', 'skip_rows', 'h1', 'fast', 'rich', 'noheading']:
        filtergroup.add_argument(*args_d[i][0], **args_d[i][1]) 
    filtergroup.add_argument('-p', '--pattern', type=str, help="Pattern to use to filter")
    filtergroup.add_argument('--tag', action="store_true", help="Tag the row under column 'filtered' instead of filtering it out", default=False)

    #sort: options
    sortgroup = actions.add_parser(name='sort', help="Sort table by column fields")
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'pipewith', 'heading', 'skip_rows', 'h1', 'fast', 'rich', 'noheading']:
        sortgroup.add_argument(*args_d[i][0], **args_d[i][1]) 
    sortgroup.add_argument('-k', '--sort-key', type=int, nargs='+', 
                            help='Choose the field numbers to sort by. Multiple field numbers can be give. L->R preference',
                            default=[0])
    sortgroup.add_argument('--desc', action='store_true', 
                            help='Sort by descending order. Default is ascending',
                            default=False)

    #Correlation opions
    corrgroup = actions.add_parser(name='corr', help="Sort table by column fields")
    for i in ['fields', 'tocsv', 'delim', 'pipe', 'pipewith', 'heading', 'skip_rows', 'h1', 'fast', 'rich', 'noheading']:
        corrgroup.add_argument(*args_d[i][0], **args_d[i][1])  

    #summary: options
    aggregategroup = actions.add_parser(name='summary', help="Similar to pandas dataframe describe(), gives a statistical summary of the result, All values are treated as continous data")
    for i in ['fields', 'delim', 'skip_rows', 'h1', 'heading', 'rich', 'noheading']:
        aggregategroup.add_argument(*args_d[i][0], **args_d[i][1])

    #hist: options
    histgroup = actions.add_parser(name='hist', help="Get the histogram of the input fields",
                                   description=desc.hist)
    for i in ['fields', 'delim', 'heading', 'skip_rows', 'h1', 'rich']:
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
                                    description=desc.pivot)
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'rich', 'tocsv', 'pipe', 'pipewith']:
        pivotgroup.add_argument(*args_d[i][0], **args_d[i][1])
    pivotgroup.add_argument('-r', '--rowind', type=int, help="Position of the data that needs to be used as row index. Starts from 0",
                            metavar='N',
                            default=None)
    pivotgroup.add_argument('-c', '--columnind', type=int, help="Position of the data that needs to be used as column index. Starts from 0.", default=None, metavar='N')
    pivotgroup.add_argument('-v', '--valueind', type=int, help="Position of data that needs to be added as value to use on the cell. Starts from 0.", default=None, metavar='N')
    pivotgroup.add_argument('--aggfunc', type=str, nargs='+', help="Agg function to use if there are multiple values for the row x column combination. Default is %(default)s",
                            choices=['first', 'last', 'concat', 'max', 'min', 'sum', 'count', 'mean', 'median', 'stdev'],
                            default=['first'])
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
                                    description=desc.group)
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'rich', 'tocsv', 'pipe', 'pipewith', 'noheading']:
        groupgroup.add_argument(*args_d[i][0], **args_d[i][1])
    groupgroup.add_argument('-r', '--rowind', nargs="+", type=int, help="Position of the data that needs to be used as row index. Starts from 0",
                            metavar='N',
                            default=[0])
    groupgroup.add_argument('-v', '--valueind', nargs="+", type=int, help="Position of data that needs to be added as value to use on the cell. Starts from 0.", default=[1], metavar='N')
    groupgroup.add_argument('--aggfunc', nargs="+", type=str, help="Agg function to use if there are multiple values for the row x column combination. Default is %(default)s",
                            choices=['first', 'last', 'concat', 'max', 'min', 'sum', 'count', 'mean', 'median', 'stdev'],
                            default=['count'])
    #groupgroup.add_argument('--aggfunc', action="append", help="""function to run on the field. one field and one action is supported. 
    #Format is fieldNumber:function1,function2. fieldNumber is based on the input field number, and numbering starts from 0. 
    #Available functions are {}""".format(transform_function_l), metavar="format")

    #topn: options
    topngroup = actions.add_parser(name='topn', help="Find topN values",
                                    description=desc.topn)
    for i in ['delim', 'heading', 'skip_rows', 'h1', 'rich', 'tocsv', 'pipe', 'pipewith', 'noheading']:
        topngroup.add_argument(*args_d[i][0], **args_d[i][1])
    topngroup.add_argument('-n', type=int, help="How many of topn to show",
                            metavar='N',
                            default=5)   
    topngroup.add_argument('-r', '--rowind', nargs="+", type=int, help="Column to use for grouping data. Indexing starts from 0",
                            metavar='N',
                            default=None)
    topngroup.add_argument('-t', '--topind', nargs="+", type=int, help="Column from which top items are selected. Indexing starts from 0",
                            metavar='N',
                            default=None)
    topngroup.add_argument('-v', '--valueind', nargs="+", type=int, help="Values to use to compute top of '-t' for each group from '-r'. Indexing starts from 0", default=None, metavar='N')
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