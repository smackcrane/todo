#!/bin/python3

import curses
from TodoList import TodoList
from Keys import Keys

def main(screen):
    screen.refresh()
    tl = TodoList(screen)

    while True:
        k = screen.getch()

        #TODO if resize, then resize
        if k == Keys.RESIZE:
            tl.resize()

        #TODO do we need try/except here?
        try:
            flag = tl.keypress(k)
        except Exception as error:
            raise
            tl.status(f'{type(error).__name__}: {error}')
        tl.save()

        if flag == 'quit':
            break

if __name__ == '__main__':
    curses.wrapper(main)
