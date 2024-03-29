#!/bin/python3

import os
import sys
import pickle
import readline
import shlex
import copy
import pandas as pd

from tasker import *

# location of data directory
data_dir = os.path.expanduser('~/Documents/todo/pickle_jar/')

# locations within data directory
save_filepath = data_dir+'todo.pickle'
backup_filepath = data_dir+'backup.pickle'

# location of log file
log_filepath = data_dir+'task_log.csv'


############################################################################
#
#	contents
#
############################################################################

"""
contents
  this section, lists organization of this document

usage
  contains help-text describing usage

notes
  notes on the internal workings, useful for reading the code

execution
  point of contact with command line, top-level execution of code
"""


############################################################################
#
#	usage
#
############################################################################

help_text = """
todo - command line to-do list

usage:
  <command> <args>

commands and arguments:
<id> means a period-delimited list of numbers, e.g. 1.4.2
<name> means a string (quotes optional), e.g. check email

  help				print a help text very much like this one

  list				print to-do list
    [-sub <id>]			only print specified task and subtasks

  add <name>			add a task
    [-sub <id>]			add as subtask of specified task
    [-top]				at at top of list (rather than default bottom)

  rm <id>				remove a task
  finish, remove, fin		aliases for rm

  rename <id> [<name>]	rename a task; if name is not specified,
              supplies current name for editing
    [-add]					append instead of replacing

  move <id>			move a task; requires one of the following:
    -into <id2>			make a subtask of <id2>
    -to <id2>			move to position <id2>
    -upto <int>			move up to rank <int> within parent
    -upby <int>			move up <int> ranks within parent
    -downto <int>		move down to rank <int> within parent
    -downby <int>		move down <int> ranks within parent

  fold <id>			fold a task, i.e. children are not printed
    [-all]				fold all top-level tasks

  unfold <id>			unfold a task
    [-all]				unfold all top-level tasks

  focus <id>			focus on specified task; equivalent to always
            including '-sub <id>' in commands that accept it

  unfocus				remove focus

  open <id>			equivalent to unfold + focus

  close				equivalent to fold (current focus task) + unfocus

  format <id> <str>	format a task with format <str>
            to see known formats, try it and the error will say

  undo				undo the last relevant command
            e.g. add/rm/move/etc but not focus/unfocus/open/etc
            by default, last 10 states saved

  full_upgrade		upgrade from a previous version (rarely needed)

universal arguments, can be passed with any command

  -verbose			re-throws errors that are normally handled by
            a chiding print statement
""".replace('\t', '    ')

# to print if save filepath is rejected
save_filepath_help = 'You can edit this script to change save_filepath to the desired location.'

# to print along with error messages
error_help = "To check usage, use 'help'."

############################################################################
#
#	notes
#
############################################################################

"""
Definition of utility functions and task / task_list classes in tasker.py

Tasks are located by ID, a collection of numbers specifying subtask indices.
- IDs are displayed externally as period delimited strings indexing by 1,
  e.g. '1.4.2'
- IDs are used internally as lists of ints indexing by 0,
  e.g. [ 0, 3, 1 ]	(corresponding to '1.4.2' above).
- utilities ID_to_list and ID_to_str convert between them
- each task stores its own ID, which is updated whenever it may have changed

Arguments are read from input() into a dict (see parse_args utility)
- some are standalone flags, and are set to True if received
  e.g. 'todo list -verbose' results in { 'verbose' : True } in dict
- some are flags with parameters
  e.g. 'todo add -sub 1.4 ...' results in { 'sub' : '1.4' } in dict
- usually one argument is expected without a flag
  - depending on context, specifies name or ID of a task or smth else
  - called 'main' in dict
  e.g. 'todo add email' results in { 'main' : 'email' } in dict
Arguments are passed by dict unpacking
  e.g. 'todo add email'
    -> args = { 'main' : 'email" }
    -> todo_list.add(**args)
  thus class task_list methods generally take an argument 'main', which
    is renamed inside the method to clarify its role

Two main classes:
  class task holds basic task info and a small amount of functionality
    (just a couple functions that are defined recursively)
  class task_list accepts commands and manipulates tasks
    holds a root task which is the root of the task tree

Convention: commands should fail by throwing an error, rather than returning
"""


############################################################################
#
#	execution
#
############################################################################


# check for verbose flag on startup
if '-verbose' in sys.argv:
  verbose = True
  sys.argv.remove('-verbose')
else:
  verbose = False

# check for description flag on startup
if '-noshow' in sys.argv:
  show_description = False
  sys.argv.remove('-noshow')
else:
  show_description = True


#
#	big ol' function to wrap execution of a command
#

def execute(todo_list, line=False, clear_buffer=True):

  global verbose

  # if no input, go again
  if not line:
    return

  # handle special flags
  if '-verbose' in line:
    verbose = True
    line.remove('-verbose')
  else:
    verbose = False
  if '-quiet' in line:
    quiet = True
    line.remove('-quiet')
  else:
    quiet = False

  # read command and arguments
  command = line[0]
  try:
    args = parse_args(line[1:])
  # may throw AssertionError if unhappy, complain and return
  except AssertionError as error:
    print(error.args[0])
    if verbose:
      raise error
    return

  # handle special commands
  if command == 'exit':
    sys.exit()
  elif command == 'help':
    print(help_text)
    return

  # string describing changes made
  description = False

  # execute command
  try:
    if command == 'add': description = todo_list.add(**args)
    elif command in ['rm','remove','forget','finish','fin']:
      description, logs = todo_list.remove(**args)
      # save data about the task
      try:
        data = pd.read_csv(log_filepath)
      except FileNotFoundError:
        description += f'\ncreating logfile at {log_filepath}\n'
        data = {
            'name'        : [],
            'ID_str'      : [],
            'parents'     : [],
            'start_date'  : [],
            'end_date'    : [],
            'command'     : []
            }
        data = pd.DataFrame(data)
      for log in logs:
        log['command'] = command
        data = data.append(log, ignore_index=True)
      data.to_csv(log_filepath, index=False)
    elif command == 'move': description = todo_list.move(**args)
    elif command in ['rename','edit']:
      description = todo_list.rename(**args)
    elif command == 'format': description = todo_list.format_task(**args)
    elif command == 'fold': description = todo_list.fold(**args)
    elif command == 'unfold': description = todo_list.unfold(**args)
    elif command == 'update': description = todo_list.update_IDs()
    elif command == 'focus': description = todo_list.set_focus(**args)
    elif command == 'unfocus': description = todo_list.unset_focus(**args)
    elif command == 'open': description = todo_list.open_task(**args)
    elif command == 'close': description = todo_list.close_task(**args)
    elif command == 'undo': description = todo_list.undo(**args)
    elif command == 'full_upgrade': description = todo_list.full_upgrade()
    # special commands that don't fall through to save and print
    elif command == 'backup':
      save_tasks(todo_list, backup_filepath)
      print('backed up.')
      return
    elif command in ['list','l']:
      # clear screen and list without saving
      clear_screen(clear_buffer=clear_buffer)
      print(todo_list.ls(**args))
      print()
      return
    else:
      assert False, "command '"+command+"' not recognized."
  # some methods throw AssertionError if they're unhappy
  except AssertionError as error:
    print(error.args[0])
    print(error_help)
    if verbose:
      raise error
    return
  # may incur TypeError if arguments are incorrect
  except TypeError as error:
    print("Error passing arguments to '"+command+"'.")
    print(error_help)
    if verbose:
      raise error
    return

  # clear screen and print
  if not quiet:
    clear_screen(clear_buffer=clear_buffer)
    print(todo_list.ls())
    print()

  # print description if there's anything to say
  if description and show_description:
    print(description.strip())

  # save todo list
  save_tasks(todo_list, save_filepath)

#
#	end of execute function
#
#	beginning of active code
#


# set input prompt with formatting
#	use ANSI escape sequences for color
#	enclose in \001 ... \002 to tell readline the characters are invisible
blue	= "\001\033[38;2;135;206;235m\002"
reg		= "\001\033[0m\002"
prompt	= f"{blue}todo: >  {reg}"


# read to-do list from file
try:
  todo_list = load_tasks(save_filepath)
# will incur AssertionError if file doesn't exist
#	and user declines to create it
except AssertionError as error:
  print(save_filepath_help)
  # if verbose is set to True, raise original error
  if verbose:
    raise error
  sys.exit()


# if we got command line arguments (besides -verbose), execute them and exit
#	in this case also don't clear the scrollback buffer
if len(sys.argv) > 1:

  # cut off the name of the script
  line = sys.argv[1:]

  try:
    execute(todo_list, line, clear_buffer=False)
  except Exception as error:
    print(f"{type(error).__name__}: {error}")
    if verbose:
      raise error

  sys.exit()


# if no command line arguments,
#	clear screen, print, and enter editor loop

clear_screen()
print(todo_list.ls())
print()

while True:

  try:
    # read a line of input and split shell-style into a list
    line = shlex.split(input(prompt))

    execute(todo_list, line)
  except Exception as error:
    print(f"{type(error).__name__}: {error}")
    if verbose:
      raise error


