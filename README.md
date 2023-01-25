# Introduction
Suite of actions to work on tabular data. Intended to be a single python script using the default libraries as much as possible.

Includes "actions" to perform on the tabular data. Each action is associated with it's set of options to facilitate it's working. Also includes general options to parse interpret the incoming data

# Usage
`da` performs `actions` on data. Each `action` has it's set of inputs (but most of them are common. Run `da $ACTION -h` to get the available options for each action.

## Actions
```
    table     Tabulate the input fields
    transpose
              Transpose rows into columns
    filter    Filter rows from table based on condition
    sort      Sort table by column fields
    corr      Sort table by column fields
    summary   Similar to pandas dataframe describe(), gives a statistical summary of the result, All values are treated as continous data
    hist      Get the histogram of the input fields
    pivot     Pivot the input data
    group     Group the input data by a column and run agg functions on the grouped data
    topn      Find topN values
    transform
              Transform columns by applying functions on the data
```

## Common input options
```
  -f 1,2,3,... or 1-3,5,8-10, --fields 1,2,3,... or 1-3,5,8-10
                        Field numbers to show in result, (numbers separated by comma or range separated by dash). Default is to show all.
  -d delimiter, --delim delimiter
                        Delimiter to split the input fields. Default is space ' '
  --heading HEADING     Custom heading to use, separate headings with comma (,). Missing ones will have colN ... N->field number
  --skip-rows SKIP_ROWS
                        Skip rows
  -h1                   Indicates that the first line is a heading
```

## Common output options
```
  --tocsv               write output as a csv to terminal
  --pipe                Pipe data to output with delim as space ' '
  --pipewith delimiter  Pipe data to output with the delim
  --fast                Attempts to be faster in producing the ascii table output, by pre-assuming cell widths of table. Use --width to set
                        custom cell widths.
  --rich                fancy table printing, only works if the rich python module is installed (Does not install by default).
  --noheading           Disables printing of heading on output when used with pipe/pipewith options. Useful if the data needs to passed into
                        sort,uniq commands
```

## Action specific options

### table
Pretty print the input data as tables. Columns can be chosen to print. By default, all columns are printed.

No special options exist.

### transpose
No special options exist.

### corr
No special options exist

### summary
No special options exist

### filter
```
  -p PATTERN, --pattern PATTERN
                        Pattern to use to filter
  --tag                 Tag the row under column 'filtered' instead of filtering it out
```

### sort
```
  -k SORT_KEY [SORT_KEY ...], --sort-key SORT_KEY [SORT_KEY ...]
                        Choose the field numbers to sort by. Multiple field numbers can be give. L->R preference
  --desc                Sort by descending order. Default is ascending
```

### hist
Creates Histogram out of the input fields

```
  --min N               the lowest of the bins. Default is the minimum of the data.
  --max N               the highest of the bins, highest value in set. Default is the maximum of the data.
  --bins BINS [BINS ...]
                        Specify the bins manually separated by space. They act as the upper edge of the bin. The lower edge is the previous
                        bin or the lowest-1 value. Has to be intergers
  --size N              Size of each bins.
  --count N             Count of histogram bins to have. Default is 20.
  --summary             Add statistical summary data
```

### pivot
```
  -r N, --rowind N      Position of the data that needs to be used as row index. Starts from 0
  -c N, --columnind N   Position of the data that needs to be used as column index. Starts from 0.
  -v N, --valueind N    Position of data that needs to be added as value to use on the cell. Starts from 0.
  --aggfunc {first,last,concat,max,min,sum,count,mean,median,stdev}
                        Agg function to use if there are multiple values for the row x column combination. Default is first
  --row_share           Compute share of results of pivot table within each row.
  --summary             Add a summary column using the same agg function, the summary is on the resulting cells with the aggfunc applied on
                        them.
  --summaryf SUMMARYF [SUMMARYF ...]
                        Running summary functions on the results, use this if you want multiple summaries
  --rowsummary          Only print the row summary, default is to print both column and row summaries
  --colsummary          Only print the column summary, default is to print both column and row summaries
 ```
 
### transform
Applies a transformation to each row. Creates a new column with the results.
Format is fN:function:arguments[|function:arguments][=result_column_name]
 - fN - N is the field number (starts from 0), "f" is necessary
 - function - any of the function names
 - arguments - arguments to be passed to the function. Refer to the function details. 
   If argument is fY the data from column Y is used on column N to get results
   If it's a  it will run the operation on fN using the number as the input
 - "|" can be used to chain functions
   Results of first transform will become inputs to second transform funfction
   the second transform functions follows the same rules as the above
 - "=" to rename the resulting column. the default is to use function(fN, arguments)
 

```
  --function format     transform function of the format fN:function_name:arguments[=name_of_result_column]
```

### topn
Find the top N (limted by -n) items (from -t column) for a group (from -r column) based on the data (from values in -v column) by applying the aggregation function (using --aggfunc)

```
  -n N                  How many of topn to show
  -r N [N ...], --rowind N [N ...]
                        Column to use for grouping data. Indexing starts from 0
  -t N [N ...], --topind N [N ...]
                        Column from which top items are selected. Indexing starts from 0
  -v N [N ...], --valueind N [N ...]
                        Values to use to compute top of '-t' for each group from '-r'. Indexing starts from 0
  --aggfunc {first,last,concat,max,min,sum,count,mean,median,stdev} [{first,last,concat,max,min,sum,count,mean,median,stdev} ...]
                        Agg function to use if there are multiple values for the row x column combination. Default is ['count']
 ```
 
### group
Group columns (got from -r) and apply the aggregate functions (got from --aagfunc) on the data from columns (got from -v)

```
   -r N [N ...], --rowind N [N ...]
                        Position of the data that needs to be used as row index. Starts from 0
  -v N [N ...], --valueind N [N ...]
                        Position of data that needs to be added as value to use on the cell. Starts from 0.
  --aggfunc {first,last,concat,max,min,sum,count,mean,median,stdev} [{first,last,concat,max,min,sum,count,mean,median,stdev} ...]
                        Agg function to use if there are multiple values for the row x column combination. Default is ['count']
 ```
 
