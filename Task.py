############################################################################
#
#   Task.py
#       task class for todo list
#
############################################################################

import curses
import utils

class Task:
    def __init__(self, text):
        self.text = text                # name / text of task
        self.ID_str = ''                # ID string
        self.boxes = ''                 # box-drawing character prefix
        self.textlines = []             # lines of text for display
        self.next_task = None           # next task in display
        self.subtasks = []              # list of subtasks
        self.folded = False             # fold flag
        self.attr = curses.A_NORMAL     # formatting for display

    # recursively refresh ID string, boxes, lines, next task
    def refresh(self, width, ID_list, boxes, top_next):
        self.ID_str = utils.ID_to_str(ID_list)
        # refresh boxes; [2:] because children of root don't need boxes
        self.boxes = boxes[2:]
        # split text into lines for display
        self.textlines = []
        line_len = width - len(self.boxes+self.ID_str+' ')
        for n in range( -(len(self.text) // -line_len) ): # ceiling division
            self.textlines += [ self.text[n*line_len:(n+1)*line_len] ]
        
        # edge case: root should always have a subtask
        if ID_list == [] and not self.subtasks:
            self.subtasks.insert(0, Task('Empty!'))

        # recurse
        if not self.subtasks:
            self.next_task = top_next
            return
        else:
            self.next_task = self.subtasks[0]
        i = 0
        for sub in self.subtasks[:-1]:
            sub.refresh(
                    width,
                    ID_list+[i],
                    boxes+'\u251C\u2500',
                    self.subtasks[i+1])
            i += 1
        # last subtask gets different box prefix and next task
        self.subtasks[-1].refresh(
                width,
                ID_list+[i],
                boxes+'\u2514\u2500',
                top_next)
