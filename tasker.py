
import os
import sys
import pickle
import readline
from copy import deepcopy
import datetime
import json


############################################################################
#
#	contents
#
############################################################################

"""
contents
  this section, lists organization of this document

utilities
  start of the code---basic utilities for parsing command line input,
  pretty-printing, and translating between data types

task / task_list classes
  core of the code---basically what it sounds like, classes for
  task and task list objects
"""


############################################################################
#
#	utilities
#
############################################################################


# change ID from internal list form to external string form
def ID_to_str(ID_list):
  # change from index by 0 to index by 1, and from int to str
  l = [str(i+1) for i in ID_list]
  # join delimited by periods
  return '.'.join(l)


# change ID from external string form to internal list form 
def ID_to_list(ID_str):
  # if empty string, return empty list
  if ID_str == '':
    ID_list = []
  # otherwise split by periods, convert from str to int, and
  #	change from index by 1 to index by 0
  else:
    ID_list = [int(i) - 1 for i in ID_str.split('.')]

  return ID_list


# change multiple IDs from external string form to internal list form 
# returns a list of ID lists
def IDs_to_lists(ID_strs):
  return [ID_to_list(i) for i in ID_strs.split()]


# split a string into ID list and name
def parse_ID_name(s):
  ID_str = ''
  ID_chars = ['.'] + [str(i) for i in range(10)]
  # chomp off ID string
  while s and s[0] in ID_chars:
    ID_str += s[0]
    s = s[1:]
  # the rest of 's' is now the name, except maybe whitespace
  name = s.strip()

  return ID_to_list(ID_str), name


# append prefix to beginning of each line of text after the first
def line_prefix(text, prefix):
  # strip whitespace from both ends of text
  text = text.strip()
  # replace newlines with newline plus prefix
  return text.replace('\n','\n'+prefix)


# sub-utility for justify function below
def chomp(line):
  # make lists of characters appearing in box-drawing prefix and in ID
  prefix_chars = ['\u2500','\u2502','\u2514','\u251C',' ']
  ID_chars = ['.']+[str(i) for i in range(10)]

  # chomp off box-drawing prefix
  prefix = ''
  while line and line[0] in prefix_chars:
    prefix += line[0]
    line = line[1:]
  # chomp off format escape code if there is one
  form = ''
  if line[0] == '\033':
    # escape code starts with '\033' and ends with 'm'
    # check condition at the end of the loop
    #	because we want to break after chomping the 'm'
    while line:
      c = line[0]
      form += c
      line = line[1:]
      if c == 'm':
        break
  # chomp off ID string
  ID_str = ''
  while line and line[0] in ID_chars:
    ID_str += line[0]
    line = line[1:]
  # strip format escape code off the end of string if there is one
  # do this by just deleting everything after the next '\033'
  if '\033' in line:
    idx = line.find('\033')
    line = line[:idx]
  # strip whitespace (usually just a leading space)
  name = line.strip()

  return prefix, form, ID_str, name


# fit to-do list to line_width nicely
def justify(text, width=None):
  # if width was not passed, get it dynamically
  if not width:
    try:
      width = os.get_terminal_size().columns
    except OSError:
      # if no width supplied and can't detect it, jus' choose smth
      width = 76

  out = ''
  lines = text.splitlines()
  # process each line independently, except checking the next line
  for i, line in enumerate(lines):
    # if line is short enough, just throw it in
    if len(line) <= width:
      out += line + '\n'
      continue
    # if it needs to be broken, carry on

    # split up prefix, ID string, and name
    prefix, form, ID_str, name = chomp(line)

    # janky check if the next line is a child of this line
    # will affect one character 'blox' of newline_prefix below
    blox = ' '	# default just a space
    if i+1 < len(lines):
      next_prefix, *_ = chomp(lines[i+1])
      if len(next_prefix) > len(prefix):
        # if it is a child, we need an extra box-drawing character
        blox = '\u2502'

    # determine prefix for lines after the first
    newline_prefix = prefix.replace('\u251C','\u2502')
    newline_prefix = newline_prefix.replace('\u2500',' ')
    newline_prefix = newline_prefix.replace('\u2514',' ')
    newline_prefix += blox + ' '*len(ID_str)

    # if newline prefix is as long as the line, make a fuss
    assert len(newline_prefix) < width, 'justify: Line too long to justify'

    # add to out until 'name' is empty
    # number of columns left for name text
    cols = width - len(newline_prefix)
    # first line
    out += prefix + form + ID_str + ' ' +  name[:cols] + '\033[0m\n'
    name = name[cols:]
    # subsequent lines
    while name:
      out += newline_prefix + form + name[:cols] + '\033[0m\n'
      name = name[cols:]

  # strip whitespace and return
  return out.strip()


# save to-do list
def save_tasks(todo_list, save_file):

  with open(save_file, 'wb') as f:
    pickle.dump(todo_list, f)


# load to-do list
def load_tasks(path):
  # read from specified path
  if os.path.isfile(path):
    with open(path, 'rb') as f:
      todo_list = pickle.load(f)
  # if file doesn't exist, offer to create it
  else:
    print('Save file not found at '+save_filepath)
    yn = input('Create it? [y/n] ')
    assert yn[0] in ['y','Y'], 'No save file found or created'
    # if asked to create it, make an empty to-do list and save it
    todo_list = task_list()
    with open(path, 'xb') as f:
      pickle.dump(todo_list, f)

  return todo_list


# parse command-line arguments into a dict
def parse_args(sysargs):
  args = {}
  while sysargs:
    # grab the next argument
    arg = sysargs[0]

    # complain if it's empty
    # it's not necessarily a problem to be empty,
    #	but I've got into habits where it's useful to trash this case
    assert arg, "empty main argument"

    # if it's a standalone flag, set that flag
    #	 and go forward one arg
    #		(note, in current setup we expect some to never appear)
    if arg in ['-verbose','-quiet','-add','-all','-rall','-top','-help']:
      args[arg[1:]] = True
      sysargs = sysargs[1:]

    # if it's not a standalone, read in key and value
    #	and go forward two args
    elif arg[0] == '-':
      key = arg[1:]
      # check that there's a value, and complain if not
      assert len(sysargs) > 1, f"flag {arg} needs a value"
      value = sysargs[1]
      args[key] = value
      sysargs = sysargs[2:]

    # if it's not accompanied by a flag, add to main argument
    #	usually is name of task or ID string
    else:
      # if already started, append separated by a space
      if 'main' in args:
        args['main'] += ' ' + arg
      # if not started, start it
      else:
        args['main'] = arg

      sysargs = sysargs[1:]

  return args


# clear screen (without clearing scrollback buffer)
def clear_screen(clear_buffer=True):
  if clear_buffer:
    os.system('clear')
  else:
    os.system('clear -x')


############################################################################
#
#	task / task_list classes
#
############################################################################


class task:
  def __init__(self, name):
    self.name = name				# name / description of task
    self.ID_str = ''				# ID string for printing
    self.subtasks = []				# list of subtasks
    self.folded = False				# fold flag
    self.format = ''			# formatting for print
    self.start_date = datetime.date.today().isoformat()

  # upgrade from previous versions
  def full_upgrade(self):
    # check if attributes exist, and create them if not
    try: self.ID_str
    except AttributeError: self.ID_str = ''
    try: self.folded
    except AttributeError: self.folded = False
    try: self.format
    except AttributeError: self.format = '\033[0m'
    try: self.start_date
    except AttributeError: self.start_date = ''

    # recurse to subtasks
    for sub in self.subtasks:
      sub.full_upgrade()

  # recursively update ID string of self and subtasks
  def update_IDs(self, ID_list):
    self.ID_str = ID_to_str(ID_list)
    for index, sub in enumerate(self.subtasks):
      sub.update_IDs(ID_list+[index])

  # recursively produce a pretty list of self and subtasks
  # returns it as a string
  def ls(self, autofold=False):
    out = ''	# output to build up

    # add self
    out += self.ID_str+' '+self.name+'\n'

    # if folded, end here
    if self.folded or autofold:
      # add indication of hidden subtasks if there are any
      if self.subtasks:
        out += '\u2514\u2500 ...\n'
      return out

    # add sub to-do lists with box-drawing indentation
    for i, sub in enumerate(self.subtasks):
      # treats last subtask differently for box-drawing
      if i < len(self.subtasks) - 1:
        out += '\u251C\u2500'
        out += line_prefix(sub.ls(), '\u2502 ')
        out += '\n'
      else:
        out += '\u2514\u2500'
        out += line_prefix(sub.ls(), '  ')
        out += '\n'

    return out

  # recursively unfold all tasks at all levels
  def recursively_unfold(self):
    self.folded = False
    for t in self.subtasks:
      t.recursively_unfold()

  # produce dict with log information
  def log(self):
    end_date = datetime.date.today().isoformat()
    log = {
        'name'        : self.name,
        'ID_str'      : self.ID_str,
        'start_date'  : self.start_date,
        'end_date'    : end_date
        }
    return log



class task_list:
  def __init__(self, root=None, focus=[], focus_past=[],
      undo_states=[], max_undo_depth=10):
    if root == None: self.root = task(name='root')
    else:	self.root = root
    self.focus = focus
    self.focus_past = focus_past
    self.undo_states = undo_states
    self.max_undo_depth = max_undo_depth

  # find and return task for given ID list
  def grab_task(self, ID_list):
    t = self.root
    for index in ID_list:
      t = t.subtasks[index]
    return t

  # find and return task for given ID list
  def list_names(self, ID_list):
    t = self.root
    s = []
    for index in ID_list:
      t = t.subtasks[index]
      s.append(t.name)
    return s

  # upgrade from previous version
  def full_upgrade(self):
    # check if attributes exist, and if not create them
    try: self.focus
    except AttributeError: self.focus = []
    try: self.focus_past
    except AttributeError: self.focus_past = []
    try: self.undo_states
    except AttributeError: self.undo_states = []
    try: self.max_undo_depth
    except AttributeError: self.max_undo_depth = 10

    # send it down to the task tree
    self.root.full_upgrade()

  # update ID strings in tasks
  # no return value
  def update_IDs(self):
    self.root.update_IDs([])

  # pretty-print task list
  # returns output as string
  def ls(self, sub=''):
    # convert parent ID 'sub' to list form, or use focus if no parent
    if sub:
      parent = ID_to_list(sub)
    else:
      parent = self.focus

    t_list = ''
    # if parent / focus is set, list that task
    if parent:
      t_list = self.grab_task(parent).ls()
    # if not, concatenate lists for each top-level task
    else:
      for sub in self.root.subtasks:
        t_list += sub.ls()

    return justify(t_list)

  # add a new task
  # returns string describing addition
  def add(self, main, sub=None, top=False):
    self.save_undo_state()
    # arg 'main' is name / description of task
    name = main
    # convert parent ID 'sub' to list form, or use focus if no parent
    if sub == None:
      parent = self.focus
    else:
      parent = ID_to_list(sub)

    # make new task and add to parent
    #	at the top of the list if specified, otherwise at the bottom
    new_task = task(name)
    if top:
      self.grab_task(parent).subtasks.insert(0, new_task)
    else:
      self.grab_task(parent).subtasks.append(new_task)

    # update task IDs
    self.update_IDs()

    # return description
    return 'added:\n'+justify(new_task.ls())

  # remove a task
  # returns string describing removal and
  # a list of dicts with task data for logging
  def remove(self, main):
    self.save_undo_state()
    # arg 'main' is ID string(s) of task(s) to remove
    ID_lists = IDs_to_lists(main)
    # sort lists backwards so removing doesn't change upcoming IDs
    ID_lists.sort()
    ID_lists.reverse()

    out = ''
    logs = []
    for ID_list in ID_lists:
      # pop index off end of ID_list, leaving parent ID in ID_list
      index = ID_list.pop()

      # grab parent and remove subtask
      removed = self.grab_task(ID_list).subtasks.pop(index)
      # record names of parent tasks
      parents = self.list_names(ID_list)

      # add removed task to description and log
      out += 'removed:\n'+justify(removed.ls())+'\n'
      log = removed.log()
      log['parents'] = json.dumps(parents)
      logs.append(log)

    # update task IDs
    self.update_IDs()

    return out.strip(), logs

  # rename task
  # returns a string describing new name
  def rename(self, main, add=False):
    self.save_undo_state()
    # arg 'main' is string with ID and optionally new name
    ID_list, name = parse_ID_name(main)

    t = self.grab_task(ID_list)

    # if no name is specified, give current text for editing
    if not name:
      # much obliged to https://stackoverflow.com/a/2533142/791462
      readline.set_startup_hook(lambda: readline.insert_text(t.name))
      try:
        name = input(t.ID_str+' ')
        t.name = name
      finally:
        readline.set_startup_hook()
    # if name was specified, rename or add to name
    elif add:
      t.name += ' '+name
    else:
      t.name = name

    return 'renamed:\n'+justify(t.ls(autofold=True))

  # move task
  # returns string describing moved task
  # throws AssertionError if unhappy
  def move(self, main, into='',
      to='', upto='', upby='', downto='', downby=''):
    self.save_undo_state()
    # arg 'main' is ID string of task to move
    ID_list = ID_to_list(main)
    # pop index, leaving parent in ID_list
    index = ID_list.pop()

    # figure out which type of move, and move it
    if into:	# move to new parent
      # get new parent
      new_parent = ID_to_list(into)

      # remove task, and add to new parent
      # but grab new parent first so IDs are not disturbed
      p = self.grab_task(new_parent)
      t = self.grab_task(ID_list).subtasks.pop(index)
      p.subtasks.append(t)
    elif to:	# move to new specific ID
      # convert to list and pop the last element,
      # leaving new parent and new index
      new_parent = ID_to_list(to)
      new_index = new_parent.pop()

      # remove task, and add to new parent at new index
      p = self.grab_task(new_parent)
      t = self.grab_task(ID_list).subtasks.pop(index)
      p.subtasks.insert(new_index, t)
    elif upto or downto or upby or downby: # up or down within parent
      # find new index
      if upto: new_index = int(upto) - 1 # change index-by-0 to -by-1
      elif downto: new_index = int(downto) - 1
      elif upby: new_index = index - int(upby)
      elif downby: new_index = index + int(downby)
      # make sure new index is at least 0
      new_index = max( new_index, 0 )

      # grab parent (same as old parent) and move subtask
      p = self.grab_task(ID_list)
      t = p.subtasks.pop(index)
      p.subtasks.insert(new_index, t)
    else:
      assert False, "'move' needs an argument."

    # update IDs
    self.update_IDs()

    return 'moved:\n'+justify(t.ls(autofold=True))

  # fold task
  # no return value
  def fold(self, main='', all=False):
    self.save_undo_state()
    # if 'all' is passed, fold all top-level tasks
    # I cringe at using a built-in name for a kwarg, but
    #	I really want to call it 'all' from the outside
    #	and not have to make exceptions on how arguments are passed
    if all:
      # get list of top-level subtasks and convert to list of IDs
      top_level = self.grab_task(self.focus).subtasks
      ID_lists = [ID_to_list(t.ID_str) for t in top_level]
    # otherwise arg 'main' is ID string(s) of task(s) to fold
    else:
      ID_lists = IDs_to_lists(main)

    for ID_list in ID_lists:
      # grab task and fold it
      t = self.grab_task(ID_list)
      t.folded = True

  # unfold task
  # no return value
  def unfold(self, main='', all=False, rall=False):
    self.save_undo_state()
    # if 'rall' is passed, unfold *all* tasks ('r'ecursively)
    if rall:
      self.root.recursively_unfold()
      return

    # if 'all' is passed, unfold all top-level tasks
    if all:
      # get list of top-level subtasks and convert to list of IDs
      top_level = self.grab_task(self.focus).subtasks
      ID_lists = [ID_to_list(t.ID_str) for t in top_level]
    # otherwise arg 'main' is ID string(s) of task(s) to unfold
    else:
      ID_lists = IDs_to_lists(main)

    for ID_list in ID_lists:
      # grab task and unfold it
      t = self.grab_task(ID_list)
      t.folded = False

  # set focus
  # no return value
  def set_focus(self, main):
    self.save_undo_state()
    # if there's a focus, remember it
    if self.focus:
      self.focus_past.append(self.focus)

    # arg 'main' is ID string of task to focus on
    self.focus = ID_to_list(main)

  # un-set focus
  # no return value
  def unset_focus(self):
    self.save_undo_state()
    # if there's a past focus, return to it; otherwise remove focus
    if self.focus_past:
      self.focus = self.focus_past.pop()
    else:
      self.focus = []

  # open, i.e. unfold and focus
  # no return value
  def open_task(self, main):
    self.save_undo_state()
    # unfold and focus
    self.unfold(main)
    self.set_focus(main)

  # close, i.e. fold and unfocus
  # no return value
  def close_task(self):
    self.save_undo_state()
    # fold and unfocus
    self.fold(ID_to_str(self.focus))
    self.unset_focus()

  formats =	{ 
      'none'        : '\033[0m',
      'bold'        : '\033[1m',
      'italic'      : '\033[3m',
      'underline'   : '\033[4m',
      'bright'      : '\033[38;2;255;255;255m',
      'dim'         : '\033[38;5;240m',
      'invisible'   : '\033[30m',
      'red'         : '\033[31m',
      'orange'      : '\033[33m',
      'yellow'      : '\033[38;5;220m',
      'green'       : '\033[32m',
      'cyan'        : '\033[36m',
      'pink'        : '\033[35m',
      }

  # format task
  # no return value
  def format_task(self, main):
    self.save_undo_state()
    # arg 'main' is ID strig of task and key string for format dict
    ID_list, form = parse_ID_name(main)

    assert form in self.formats, 'format "'+form+'" not recognized\nknown formats: '+' '.join(self.formats.keys())

    self.grab_task(ID_list).format = self.formats[form]

  # undo last command
  # no return value
  def undo(self):
    # make sure there's a state to restore
    assert self.undo_states, "no undo state found"

    state = self.undo_states.pop()
    self.root = state['root']
    self.focus = state['focus']
    self.focus_past = state['focus_past']

  # save an undo state
  def save_undo_state(self):
    # record state in a dict
    state = {
        'root': deepcopy(self.root),
        'focus': deepcopy(self.focus),
        'focus_past': deepcopy(self.focus_past)}
    # add to undo states
    self.undo_states.append(state)
    # pop down to max_undo_depth
    while len(self.undo_states) > self.max_undo_depth:
      self.undo_states.pop(0)

  #TODO handle keypress
  def keypress(self, k):
      pass


