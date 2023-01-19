import fileinput
from math import nan, ceil, inf
from itertools import tee, starmap, repeat, groupby
from re import L
import statistics as stats
from collections import defaultdict, Counter
from copy import deepcopy
#Importing from da_* should be from da_* import *
# so that get_daflat.py can ignore and the functions are in global scope
from da_utils import *
from da_custom import *
from operator import itemgetter

class Table(object):
    #Define the basic arguments needed for table
    # Use kwargs for the rest
    def __init__(self, src=None, delim=' ', heading=None, data=None,
                 h1=False, fields=None, action=None,
                 missing_char='-', skip_rows=0,
                 **kwargs):
        #expand kwargs
        args = dict(kwargs)
        self.action = action
        self.args = args
        #Input field delimiter
        self.delim = delim
        #To Skip rows
        self.skip_rows = skip_rows
        #Use a flag to track if first line is heading
        self.h1 = h1
        #if 1st line is not heading, use the heading provided, default is []
        if heading:
            self.heading = heading
        else:
            self.heading = []
        #Create a max_fields field to limit the data 
        # start with 0 and then populate later in get_input
        self.max_fields = 0 
        #Character will be used to impute missing data
        self.missing_char = missing_char
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
            self.build_table_from_data(data)
        self.data, self.data_for_get_fields = tee(self.data, 2)
        #Keep a field index map of input and output
        self.field_map = dict(zip(self.fields, range(self.max_fields)))

    def add_row(self, row):
        self.data.append(row)

    def build_table_from_data(self, data):
        self.data = []
        for info in data[self.skip_rows:]:
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
            #Impute missing data with missing_char
            info = [i if i else self.missing_char for i in info]
            self.data.append(info)
        #If the first line is heading, pop it out
        if self.h1:
            self.heading = self.data.pop(0)
        #Otherwise check if heading is populated by user input
        elif self.heading == []:
            #If not use the fields numbers as hint for heading
            self.heading = ['col'+str(i) for i in self.fields]
        #Compute max fields, needed for imputation of data
        if not self.max_fields:
            self.max_fields = max([len(i) for i in self.data])
        #Also fill the self.fields list
        self.fields = self.fields or list(range(self.max_fields))
            
    def build_table_from_source(self):
        #Read the source
        self.src_data = self.get_input()
        #Skip rows
        for i in range(0, self.skip_rows):
            next(self.src_data)            
        #If the first line is heading, pop it out
        if self.h1:
            self.heading = next(self.src_data)
        #Impute missing data with missing_char
        self.data = self.impute_missing(self.src_data)
        
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
            self.max_fields = max(len(info), self.max_fields)
            if self.fields:
                #Using dict and enumerate to access fields by numbers
                filter_info = dict(enumerate(info))
                #If field exists give the result, else return None
                # This should also preserve the order of fields
                info = list(filter(lambda x:x!=None, 
                                   [filter_info.get(f, None) for f in self.fields]))
            #If an empty string
            if not info or info == ['']:
                continue
            #Generate field list
            yield info

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
        """Return field name and data. Gets the input as columnar data.
        Dictionary 
        {field_number0: [heading_name, [row1, row2]],
         field_number1: ...}
        """
        #If no fields is passed to get_fields
        if fieldN == [] or fieldN == None:
            #Check if we have fields populated from object
            if self.fields:
                fieldN = self.fields
            #Otherwise generate a list using the max_fields
            else:
                fieldN = list(range(self.max_fields))
        #If fieldN is passed, make sure it is within limits
        else:
            fieldN = list(filter(lambda x:x <= self.max_fields, self.fields))
        #self.fields is the field numbers of the input used to build the table
        #fieldN is the requested fields from (mapped to the input and not the table)
        #field_d = {field-number: [ heading, [data]], field-number: [h, [data]], ...}        
        field_d = {k: [self.heading[n], []] for n, k in enumerate(fieldN)}
        #populate data for field_d
        #for row in self.data_for_get_fields:
        for row in self.data:
            for n, k in enumerate(fieldN):
                field_d[k][1].append(row[n])
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
        if self.action == "pivot":
            #Intialise summary_rows as 0
            summary_rows = 0
            #If we have column key, that means, we are using the proper pivot
            # get the summary rows as the length of the summary function list
            # AND colsummary is TRUE
            if self.col_k and self.colsummary:
                summary_rows = len(self.summaryfunc)
            heading_border=True
            summary = summary_rows            
        row_counter = 0
        rows = list(self.data)
        #If heading was not yet populated, populate it now
        if not self.heading:
            self.fill_heading()
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

    def tocsv(self, disable_heading=False):
        self.pipe(delim=',')

    def sort(self, key=None, reverse=True):
        if key == None:
            key = [0]
        self.data = sorted(self.data, key=itemgetter(*key), reverse=reverse)

    def filterfunc(self, pattern):
        """
        format:
         F1 AND F2 AND F3 ...
         where F1 is 
          fN operator operand
        
        Operand1: Has to be of the format fN, where N is a number and indicates field number. (zero-indexed)
        Operand2: If wrapped under quotes (double/single), interpreted as string and only string operators are applied.
          If not wrapped under quoted, interpreted as floating point numbers and numerical operations are applied
        Numerical operators:
         ==, !=, >=, <=, >, <
        String operators:
         == - include rows with string op2 (case sensitive)
         != - exclude rows with string op2 (case sensitive)
        """
        function_l = []
        #Split the filter checks by "AND"
        for i in pattern.split('AND'):
            i = i.strip()
            action = [a.strip() for a in i.split()]
            op1 = int(action[0][1:])
            opr = action[1]
            op2 = action[2]
            #Check if the second operand is string or number
            # Use quotes around the operand to check this
            if op2[0] in ("'", '"') and op2[-1] in ("'", '"'):
                op2_type = 'string'
            else:
                op2_type = 'float'
            #numerical oerations
            if op2_type == 'float':
                if opr in ('>', '<', '==', '!=', '<=', '>='):
                    function_l.append('float(data[{}]) {} {}'.format(op1, opr, op2))
            #String operations
            elif op2_type == 'string':
                if opr == '===':
                    opr_use = '=='                    
                    function_l.append('data[{}] {} {}'.format(op1, opr_use, op2))
                elif opr == '!==':
                    opr_use = '!='                    
                    function_l.append('data[{}] {} {}'.format(op1, opr_use, op2))
                elif opr in ('=='):
                    opr_use = '=='
                    function_l.append('data[{}].casefold() {} {}.casefold()'.format(op1, opr_use, op2))
                elif opr in ('!='):
                    opr_use = '!='
                    function_l.append('data[{}].casefold() {} {}.casefold()'.format(op1, opr_use, op2))
        return function_l

    def filtermap(self, data):
        conditions_true = 0
        #Cycle through each check
        for i in self.function_l:
            #Check if it evaluates to False
            if not eval(i):
                #If it is False, skip checking other checks (chained AND is implemented)
                conditions_true = False
                continue
            else:
                #check returns True, mark it as true, move to next check
                conditions_true = True
        #If tagging is needed the rows needs to be retained
        # and additional column needs to be added
        #Else return only the row which passes all checks
        if self.tag == True:
            #If conditions_true remained True, 
            if conditions_true and conditions_true !=0:
                return data + [self.pass_tag]
            else:
                return data + [self.fail_tag]
        else:
            # And if tagging is not needed, return the row 
            # and If conditions_true remained True, then only return the row
            if conditions_true and conditions_true !=0:
                return data
            # else return None
            else:
                return None

    def filterrows(self, pattern, tag=False):
        self.tag = tag
        self.pass_tag = 'Yes'
        self.fail_tag = 'No'
        self.tag_heading = 'tagged'
        self.function_l = self.filterfunc(pattern)
        filter_results = list(filter(lambda x:x!=None, map(self.filtermap, self.data)))
        self.data = filter_results
        #if tagging is enabled, add the heading 'tagged'
        if self.tag == True:
            self.heading += [self.tag_heading]

    def transpose(self):
        """
        Convert rows to columns
        """
        self.action = 'transpose'
        data = transpose_rows(list(self.data))
        T = Table(data=data[1:], heading=data[0], max_fields=0)
        return T

    def GROUP(self):
        self.action = 'group'
        row_k = self.args['row_k']
        val_k = self.args['val_k']
        if row_k == None:
            self.row_k = [1]
        else:
            self.row_k = row_k
        #If val_k is passed we will need to use that column
        if val_k != None:
            self.val_k = val_k
        #Otherwise we need to use some statistical summary
        else:
            pass
        self.aggfunc = self.args['f']

    def TOPN(self):
        self.action = 'topn'
        #Run GROUPING actions first
        self.GROUP()
        self.top_k = self.args['top_k']
        self.n = self.args['n']
        self.row_k.append(*self.top_k)

    def PIVOT(self):
        self.action = 'pivot'
        self.row_k = self.args['row_k']
        self.col_k = self.args['col_k']
        self.rowsummary = self.args.get('rowsummary') or False
        self.colsummary = self.args.get('colsummary') or False
        #If val_k is passed we will need to use that column
        if self.args['val_k'] != None:
            self.val_k = self.args['val_k']
        #Otherwise we need to use some statistical summary
        else:
            pass
        self.aggfunc = self.args['f']
        self.summary = self.args['summary']
        self.summaryfunc = []
        if self.summary:
            self.summaryfunc = [self.aggfunc]
        if self.args['summaryf']:
            self.summaryfunc += self.args['summaryf']
        #Order preserving - https://www.peterbe.com/plog/fastest-way-to-uniquify-a-list-in-python-3.6
        self.summaryfunc = list(dict.fromkeys(self.summaryfunc))
        self.summarydata = {'row':{'heading':[], 'data':[]},
                            'col':{'heading':[], 'data':[]}}

    def pivot(self):
        """Pivot on row index and column index with an aggregation function applied on value index"""
        #To set up the necessary variables
        self.PIVOT()
        #row pointer as the result will be got from the table in the order r, c, v
        # The order comes from da_tool when handling fields needed for table creation    
        rp = 0 
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
        self.pivotdata = pivot_data
        #Deep copy to avoid overwriting pivotdata 
        # as it should not change over multiple summaries
        self.data = deepcopy(pivot_data)
        #If summary is needed, running on the resulting pivot table
        #Rest heading, Construct pivot heading using the parent Table's heading
        self.row_v = row_v
        self.col_v = col_v
        #Set the heading of the first column of the pivot table
        # self.heading has the names colX, colY, colZ  ...
        # where X, Y, Z are the field numbers from the input file
        # and the order is by rp, cp, vp
        self.heading = ['{}({}/{})'.format(self.aggfunc, self.heading[rp], self.heading[cp])]
        self.heading += self.col_v
        self.pivotheading = self.heading
        #Reset max_fields
        self.max_fields = len(self.heading)        
        summary_heading = self.heading.copy()
        for func in self.summaryfunc:
            self.add_summary(self.pivotdata, summary_heading, func,
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

    def get_topn(self):
        #To set up the necessary variables
        self.TOPN()
        group_d, group_k = self.create_groups()
        group_data = self.process_groups(group_d, group_k)
        topn_d = {}
        for row, data in groupby(group_data, key=lambda x:x[0]):
            topn = sorted(data, key=lambda x:x[-1], reverse=True)[:self.n]
            topn_d[row] = list(map(lambda x:'{}({})'.format(x[1], x[2]), topn))
            topn_items = len(topn_d[row]) 
            if topn_items < self.n:
                for i in range(topn_items, self.n):
                    topn_d[row].append('-')
        data = self.flatten_d(topn_d)
        self.data = data
        self.heading = [self.heading[self.row_k[0]]]
        self.heading += ['top{}'.format(i) for i in range(1, self.n+1)]

    def flatten_d(self, d):
        flat_l = []
        for k in d:
            flat_l.append([k, *d[k]])
        return flat_l 

    def create_groups(self):
        """Group is for grouping and summarising data for row ind key using data from valueind"""
        #row pointer as the result will be got from the table in the order r, c, v
        # The order comes from da_tool when handling fields needed for table creation    
        self.rp = len(self.row_k)
        self.vp = list(range(self.rp, len(self.fields)))
        #group_d will create a dictionary, with key as the row-index
        # and values is the list of values for that row-index
        group_d = defaultdict(dict)
        for v in self.vp:
            group_d[v] = defaultdict(list)
        #group_k will hold the keys of the row-index
        group_k = set()
        for d in self.data:
            #Get the row index, if it's None, use nan
            group_k.add(tuple(d[:self.rp]) or nan)
            #Get the values in a list for each rowindex, if it's None use nan
            for v in self.vp:
                r_key = tuple(d[:self.rp])
                group_d[v][r_key].append(d[v] or nan)
        return group_d, group_k

    def process_groups(self, group_d, group_k):
        """
        group_d: has the data for each group
        group_k: Keys or the grouped items from which group_d can be accessed
        """
        #Process the groups and print the grouped results
        #Making group_k into a list and sort it
        group_k = sorted(list(group_k))
        group_data = []
        for row in group_k:
            row_data = []
            for v in self.vp:
                cells = []
                for f in self.aggfunc:
                    cell = f_aggfunc(group_d[v][row], f, need_sort=True) 
                    if cell == None:
                        cell = self.missing_char
                    cells.append(cell)
                row_data += cells
            group_data.append(list(row) + row_data)
        return group_data

    def create_group_heading(self):
        #Set the heading of the first column of the new table
        # self.heading has the names colX, colY ...
        # where X, Y are the field numbers from the input file
        # and the order is by rp, cp, vp
        groupheading = []
        for i in range(self.rp):
            groupheading += ['group({})'.format(self.heading[i])]
        for v in self.vp:
            aggfuncheading = [i+'({})'.format(self.heading[v]) for i in self.aggfunc]
            groupheading += aggfuncheading 
        return groupheading

    def group(self):
        #To set up the necessary variables
        self.GROUP()
        group_d, group_k = self.create_groups()
        self.data = self.process_groups(group_d, group_k)
        self.heading = self.create_group_heading() 

    def to_ascii_table_pivot(self):
        #Intialise summary_rows as 0
        summary_rows = 0
        #If we have column key, that means, we are using the proper pivot
        # get the summary rows as the length of the summary function list
        # AND colsummary is TRUE
        if self.col_k and self.colsummary:
            summary_rows = len(self.summaryfunc)
        return self.to_ascii_table(heading_border=True,
                                   summary=summary_rows) 

class ColumnTable(Table):
    """
    A object with multiple columns as its members
    """
    action = 'transform'
    def __init__(self, data=[], name='Table', heading=None):
        self.name = name
        self.cdata = data
        if heading == None:
            self.heading = []
        else:
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
        return super().pipe(disable_heading=disable_heading, delim=delim)

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
                     'dummy': self.f_dummy,
                     'subtract_from': self.f_subtract_from,
                     'concat': self.f_concat
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
        #If the function is in a list of known internal functions
        if f in self.fmap:
            #Run that function by passing that param
            self.data = list(self.fmap[f](other))
        #If it's not a defined function internally
        else:
            #If function is defined under the global namespace, eval the function
            # and update column's data
            if f in globals():
                f = eval(f)
                self.data = f(self.data, other)
            else:
                #if it is not, print it to screen and return None
                print("{} does not exist".format(f))
                return None

    def transform(self, f, other):
        #Create a mapping for function and data to apply on
        # a-> is the data input
        # b-> parameter for the function to use on a
        return starmap(lambda a,b:f(a,b) if (a and b)!=None else nan, zip(self.data,
                                                                          self.get_operand(other)))

    def f_concat(self, other):
        return starmap(lambda a,b:str(a)+'_'+str(b), zip(self.data_as_categorical, other.data_as_categorical))

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
        #Address ZeroDivisionError issues
        return self.transform(lambda a,b: round(a/b, 3) if b!=0 else inf, other)

    def __floordiv__(self, other):
        return self.transform(lambda a,b: a//b, other)

    def __mod__(self, other):
        return self.transform(lambda a,b: a%b, other)

    def f_subtract_from(self, other):
        return self.transform(lambda a,b: b-a, other)

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
            result.append(['mean', round(sum(data_no_nans)/size, 2)])
            result.append(['stddev', round(stats.pstdev(data_no_nans), 2)])
            result.append(['min', min(data_no_nans)])
            pct = [5, 25, 50, 75, 90, 95, 99]
            for p in filter(lambda x:x<=100 and x>=0, pct):
                #Compute the index for the percentile
                # Reduce by 1 because of the 0 indexing
                # using ceil to find the value when it's not an integer
                ind = ceil((p*size)/100)
                #Add boundaries on the result to range from 0->highest index
                ind = max(0, min(ind, size-1))
                result.append(['{}p'.format(p), data_no_nans[ind]])
            result.append(['max', max(data_no_nans)])
        else:
            dtype = 'categorical'
            size = len(self.data_as_categorical)
            Ctr = Counter(self.data_as_categorical)
            result.append(['unique', len(Ctr.keys())])
            result.append(['count', size])
            cumsum = 0
            topN = []
            #get the share of the top5 repeating items
            for x in Ctr.most_common()[:5]:
                #Cumsum updates cumulative share, disabling it for now
                #cumsum += x[1]*100/size
                #topN.append(round(cumsum, 2))
                count = x[1]*100/size
                topN.append(round(count, 2))
            topN += ['-']*(5-len(topN))
            for n, i in enumerate(topN, 1):
                result.append(['top{}share'.format(n), '{}'.format(i)])
            result.append(['most', '{} ({})'.format(Ctr.most_common()[0][0], Ctr.most_common()[0][1])])
            result.append(['least', '{} ({})'.format(Ctr.most_common()[-1][0], Ctr.most_common()[-1][1])])
        return dtype, result


