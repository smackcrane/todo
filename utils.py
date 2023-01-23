############################################################################
#
#   utils.py
#       utilities for todo list
#
############################################################################

#
#   Note on IDs:
#       IDs are stored in two ways:
#       - as a period-delimited string indexed by 1, e.g. '1.4.2'
#       - as a list of ints indexed by 0, e.g. [0, 3, 1]
#

# convert ID from list to string
def ID_to_str(ID_list):
    return '.'.join([str(i+1) for i in ID_list])

# convert ID from string to list
def ID_to_list(ID_str):
    if ID_str == '':
        return []
    else:
        return [int(i) - 1 for i in ID_str.split('.')]
