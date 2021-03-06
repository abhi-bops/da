# Introduction

`da` is a custom python script that I have been using, tinkering for my daily use to analyse data. The original tools that I used to do analysis were bash commands like awk, grep, sort ... . `da` offers me to add some more analysis actions and additional features to apply on the output results. It attempts to be integrate into the workflow of using bash pipes to chain actions on data.

The usage is not yet simple and lacks documenation, as the consumer of the code has been mostly been me, so I ended up using what seemed like the best choices at the time. So it is in-a-way ended up being a playground for me to learn python and use them everyday. The documentation and code clean up is pending, which I plan to update very soon in a hope it will be useful to others too.

The inspiration to write `da` came from the amazing tool `visidata` from https://github.com/saulpw/visidata . However, I wrote `da` to be able to be a simple script that I can copy over to a remote machine and execute without having to worry about installing python modules. So, most of the functionality (except graphing, and fanc-ier output) works using the built-in python modules.

# Usage
`da` has certain actions that is attached with options which influence on how the action will be performed. Most of them have common options, some of them have special ones. It is best to do `da $ACTION -h` to get the available options for the action.

## Actions
1. **table**: print the input as a table with formatting (table boundaries, heading boundaries)
2. **summary**: prints the statistical summary of the input data
3. **hist**: prints the histogram of the input data. Options to create the bins are the special options to this action.
4. **pivot**: Pivoting the table on a row and column field and outputting results in the cells. Also allows grouping of data and reporting summaries of the results. (Half-pivot like)
5. **transform**: Run a function to translate input field and create a new column with the result. Options to provide the transformation commands/inputs are the special options to this action.

## Input related options
1. **-d** / **--delim** $DELIMITER: delimiter to use to split the lines to get the individual fields
2. **-h1**: Flag to indicate that the first line is to be treated as a heading.
3. **-f** / **--fields** $FIELDS: Option to filter fields to be considered to be working on, fields are interpreted as individuals, and also as range. ex: *-f 1,2,3-9* will select fields 1->9. The order specified in the input will be retained while printing the ouput. ex: -f *9,1,5,2* will select fields 9,1,5,2 in that oder. Duplicate field numbers are ignored.

## Output related options
1. Without any output option, it will pretty print the result in a simple ASCII table, with column widths adjusted to include the maximum length value in the field. Recommended to pipe result to `less -S` to view long lines of data.
2. **--fast**: attempts to stream the data as and when it is computed, useful if working on a large dataset and need to quickly view the head of the data. The formatting uses a fixed width output for columns. Recommended to pipe result to `less -S` to view long lines of data.
3. **--pipe**: No formatting is done to the data, the output fields are *space* separated and can be used as an input along the pipes to another command.
4. **--tocsv**: No formatting is done to the data, the output fields are *comma* separated and can be used as an input along the pipes to another command.
5. **--noheading**: Disable printing the heading of data. Useful if the next command in pipe cannot handle the heading as being not a part of the data.
6. **--rich**: Fancier table printing, uses the **rich** module ( https://github.com/willmcgugan/rich ) to print the results. Requires the module to have been installed to work.
7. **--graph**: Option to graph data, works for some of the actions as of now. Accepts an option which allows some control on what and which graph is outputted. Limited options (bar, line, scatter, pivot). Some of the actions have default options too based on the expectation of the action. Uses pandas, matplotlib, seaborn for plotting, tries to install them if they are not found. Graph option is of format - `kind:x:y:hue:split_interval:is_ts:subplots`. ex: **bar:1:0:2:10:False:False** --> Plot a bar chart(kind), with x-axis as column 1(x), y-axis from column 0(x), and group data by column2(hue). Split the graphs such that each  graph has 10 values(split_interval) in x-axis, x-axis is not of time format(is_ts=False), Plot all data in 1 chart(subplots=False). If format is not passed, a default format can be assumed based on action.
8. **--notable**: Do not print the table, useful if used with `--graph` if only the graphical output is sufficient.

## Action specific options

### hist
1. **--min N**: the lowest of the bins. Default is the minimum of the data.
2. **--max N**: the highest of the bins, highest value in set. Default is the maximum of the data.
3. **--bins BINS [BINS ...]**: Specify the bins manually separated by space. They act as the upper edge of the bin. The lower edge is the previous bin or the lowest-1 value. Has to be intergers.
4. **-size N**: Size of each bins.
5. **--count N**: Count of histogram bins to have. Default is 20

## pivot
1. **-r / --rowind N**: Position of the data that needs to be used as row index. Starts from 0
2. **c / --columnind N**: Position of the data that needs to be used as column index. Starts from 0.
3. **-v / --valueind N**: Position of data that needs to be added as value to use on the cell. Starts from 0.
4. **--aggfunc $FUNC**: Agg function to use if there are multiple values for the row x column combination. Available ({first,last,concat,max,min,sum,count,mean,median,stdev}) Default is first.
5. **--summary**: Add a summary column using the same agg function, the summary is on the resulting cells with the aggfunc applied on them.
6. **--summaryf $SUMMARYFUNC**: Running summary functions on the results, use this if you want multiple summaries. Function names should be separated by space. Available {first,last,concat,max,min,sum,count,mean,median,stdev}) Default is the one used in `--aggfunc``.
7. **--rowsummary**: Only print the row summary, default is to print both column and row summaries
8. **--colsummary**: Only print the column summary, default is to print both column and row summaries

## transform
1. **--function format**: 

   - function to run on the field. 1 field and one 1 action at a time is supported. 
   - Format is **fieldNumber:function:arguments**. 
   - Available functions are ['add', 'divide', 'div', 'floordiv', 'subtract', 'sub', 'multiply', 'mul', 'gt', 'lt', 'ge', 'le', 'eq', 'mod', 'dummy', 'sample']. 
   - Custom functions can also be used from by adding functions to the file eda_custom.py, there is a dummyfunction showing how the inputs are passed and how outputs should be returned. 
   - Functions can be chained with the pipe **|** and alias with the equal sign **=ALIAS**

