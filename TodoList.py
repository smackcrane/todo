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
        editor_mode = False

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

    #TODO
    def refresh(self):
        self.screen.erase()
        # update everything in preparation
        self.root.refresh(self.cols, [], '', None)
        self.update_top()

        # starting from self.top task, just print until end of screen
        row = 0
        t = self.grab_task(self.top_ID)
        while t:
            # highlight ID for active task
            if utils.ID_to_str(self.active_ID) == t.ID_str:
                ID_attr = curses.A_REVERSE
            else:
                ID_attr = t.attr
            # insert text, (then ID on first line), then prefix boxes
            try:
                self.screen.insstr( row,0, t.textlines[0], t.attr )
                self.screen.insstr( row,0, ' ')
                self.screen.insstr( row,0, t.ID_str, ID_attr )
                #self.screen.insstr( row,0, t.boxes )
                #for n in range(1,len(t.textlines)):
                #    self.screen.insstr( row+n,0, t.textlines[n], t.attr )
                #    self.screen.insstr( row+n,0, t.boxes )
            except curses.error:
                #assert False, f'{row}, {t.textlines[0]}, {t.attr}'
                break
            #TODO handle printing off end of screen
            row += len(t.textlines)
            t = t.next_task

        # hide cursor
        curses.curs_set(0)
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

    #TODO
    def keypress(self, k):
        elif k == Keys.CTRL_q:
            return 'quit'
        elif k == Keys.UP:              self.up()
        elif k == Keys.DOWN:            self.down()
        elif k == Keys.LEFT:            self.left()
        elif k == Keys.RIGHT:           self.right()
        self.refresh()
