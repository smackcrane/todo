
import curses
from Keys import Keys

class TodoWindow:
    def __init__(self, screen, todo_list):
        # curses screen we're living in
        self.screen = screen
        self.rows, self.cols = self.screen.getmaxyx()
        # todo list we're working from
        self.todo_list = todo_list
        # top row visible
        self.top = 0
        # cursor row
        self.row = 0
        # flag for editing a task
        editor_mode = False

        self.refresh()

    def refresh(self):
        self.screen.erase()

        content = self.todo_list.ls()
        lines = content.splitlines()

        for i, text in enumerate(lines):
            if i == self.row:
                attr = curses.A_REVERSE
            else:
                attr = curses.A_NORMAL
            self.screen.insstr( i,0, text, attr )

        # hide cursor
        curses.curs_set(0)

    def down(self):
        #TODO stop at end of todo list, not just end of window
        if self.row < self.rows - 1:
            self.row += 1
        self.refresh()

    def up(self):
        if self.row > 0:
            self.row -= 1
        self.refresh()

    def keypress(self, k):
        if k == Keys.CTRL_q:
            return 'quit'
        elif k == Keys.RETURN:
            editor_mode = not editor_mode
        elif editor_mode:
            #TODO uh oh how is editing gonna work? figure it out!
            pass
        elif k == Keys.DOWN:
            self.down()
        elif k == Keys.UP:
            self.up()
