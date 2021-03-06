#!/usr/bin/python

import inspect
header = """#!/usr/bin/python3

#NOTE:
#This is a flat file genereated by using the da_* scripts, if you want to modify 
# clone the repository https://github.com/abhi-bops/da and then edit the files 
# and then run get_daflat.py to get a flat file like this. 
# The sole purpose of this file is to genereate the python script da, a single file 
# that can be copied and run without worrying about importing the other da_* files.

"""

#improt all the da_related files
import da_utils
import da_classes
import da_tool

#We need the shebang line and the header line on top
output_data = header
#Add source code of each file
files = [da_utils, da_classes, da_tool]
for f in files:
    source = inspect.getsource(f)
    #If it contains "from da", ignore that line, as we are importing
    # the code here and this will not have any dependency
    for i in source:
        if i.startswith('from da'):
            continue
        output_data += i
#write it to a file
with open('da', 'w') as fd:
    fd.write(output_data)
