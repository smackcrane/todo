############################################################################
#
#   TodoList.py
#       task tree manager and curses editor
#
############################################################################

import curses
import pickle
import os
from Task import Task
from Keys import Keys
import utils
import config

class TodoList:
    def __init__(self, screen):
        # save file set in config file
        self.savefile = config.savefile
        # curses window we're working in
        self.screen = screen
        self.rows, self.cols = screen.getmaxyx()
        # top visible row, active ID, flags
        self.top_ID = [0]
        self.active_ID = [0]
        self.edit_mode = False

        self.load()
        self.refresh()

    def load(self):
        # if file exists, load it
        if os.path.isfile(self.savefile):
            with open(self.savefile, 'rb') as f:
                self.root = pickle.load(f)
            if not self.root.subtasks:
                self.root.subtasks.insert(0, Task('Empty!'))
        # if file doesn't exist, create it (as well as root task)
        else:
            self.root = Task('root')
            self.root.subtasks.insert(0, Task('Empty!'))
            with open(self.savefile, 'xb') as f:
                pickle.dump(self.root, f)

    def save(self):
        with open(self.savefile, 'wb') as f:
            pickle.dump(self.root, f)

    def refresh(self):
        self.screen.erase()
        # update everything in preparation
        self.root.refresh(self.cols, [], '', None)
        self.update_top()

        # starting from self.top task, just print until end of screen
        row = 0
        t = self.grab_task(self.top_ID)
        while t:
            # highlight ID for active task and locate cursor for edit_mode
            if utils.ID_to_str(self.active_ID) == t.ID_str:
                ID_attr = curses.A_REVERSE
                cursor_y, cursor_x = t.cursor_yx(self.cols)
                cursor_y += row
            else:
                ID_attr = t.attr
            # insert text, (then ID on first line), then prefix boxes
            try:
                self.screen.insstr( row,0, t.textlines[0], t.attr )
                self.screen.insstr( row,0, ' ')
                self.screen.insstr( row,0, t.ID_str, ID_attr )
                self.screen.insstr( row,0, t.boxes )
                for n in range(1,len(t.textlines)):
                    self.screen.insstr( row+n,0, t.textlines[n], t.attr )
                    self.screen.insstr( row+n,0, ' '*len(t.ID_str+' ') )
                    self.screen.insstr( row+n,0, utils.box_swap(t.boxes) )
            except curses.error:
                break # error when printing off end of screen, just ignore
            row += len(t.textlines)
            t = t.next_task

        # handle cursor
        if self.edit_mode:
            curses.curs_set(1)  # visible cursor
            self.screen.move( cursor_y,cursor_x )
        else:
            curses.curs_set(0)  # hide cursor

        self.screen.refresh()

    #TODO
    def update_top(self):
        pass

    # find and return task with given ID list
    def grab_task(self, ID_list):
        t = self.root
        for i in ID_list:
            t = t.subtasks[i]
        return t

    # shorthand
    def active_task(self):
        return self.grab_task(self.active_ID)

    # check if ID is valid
    def valid_ID(self, ID_list):
        t = self.root
        for i in ID_list:
            if i < len(t.subtasks):
                t = t.subtasks[i]
            else:
                return False
        return True

    #TODO
    # display text at bottom of screen
    def status(self, text):
        pass

    #TODO
    # handle terminal resizes
    def resize(self):
        pass

    def up(self):
        if self.active_ID[-1] > 0:
            self.active_ID[-1] -= 1

    def down(self):
        self.active_ID[-1] += 1
        if not self.valid_ID(self.active_ID):
            self.active_ID[-1] -= 1

    def right(self):
        if self.valid_ID(self.active_ID+[0]):
            self.active_ID = self.active_ID+[0]

    def left(self):
        if len(self.active_ID) > 1:
            self.active_ID.pop()

    # create a new task in location relative to active task, and make active
    def new_task(self, location):
        t = Task('')
        if location == 'child':
            self.active_task().subtasks.insert(0, t)
        elif location == 'below':
            parent = self.grab_task(self.active_ID[:-1])
            index = self.active_ID[-1] + 1
            parent.subtasks.insert(index, t)
        self.root.refresh(self.cols, [], '', None)
        self.active_ID = utils.ID_to_list(t.ID_str)

    def delete_active_task(self):
        index = self.active_ID[-1]
        parent = self.grab_task(self.active_ID[:-1])
        parent.subtasks.pop(index)
        # find new active ID
        if self.valid_ID(self.active_ID):   # first choice: next task
            pass
        elif self.active_ID[-1] > 0:        # second choice: previous task
            self.active_ID[-1] -= 1
        elif len(self.active_ID) > 1:       # third choice: parent
            self.active_ID.pop()
        else:                               # final case: empty task list
            pass

    def keypress(self, k):
        if k == Keys.RETURN or k == Keys.ESC:
            if self.edit_mode:
                self.edit_mode = False
        # if edit_mode, keys are passed to task except for the above
        elif self.edit_mode:
            self.active_task().edit(k)
        elif k == ord('i'):
            self.edit_mode = True
            self.active_task().edit(Keys.CTRL_a)
        elif k == ord('A'):
            self.edit_mode = True
            self.active_task().edit(Keys.CTRL_e)
        elif k == ord('n'): # new task below active task
            self.new_task('below')
            self.edit_mode = True
        elif k == ord('N'): # new task as child of active task
            self.new_task('child')
            self.edit_mode = True
        elif k == ord('D'): # delete task
            self.delete_active_task()
        elif k == Keys.CTRL_q:
            return 'quit'
        elif k == Keys.UP:              self.up()
        elif k == Keys.DOWN:            self.down()
        elif k == Keys.LEFT:            self.left()
        elif k == Keys.RIGHT:           self.right()
        self.refresh()
