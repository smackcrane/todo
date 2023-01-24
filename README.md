## todo --- Terminal To-Do list
### in python curses

### Organization

`todo.py` execution entry-point

`TodoList.py` class handling curses display and overall task tree

`Task.py` class for task objects making up task tree

`utils.py` utility functions, `config.py` config file

`Keys.py` key codes

### Usage

* Arrow keys to navigate
* `i` or `A` to edit (`RETURN` or `ESC` to finish editing)
* 'n' or 'N' for new task
* 'D' to delete task

### (My) Setup

* Put contents of repo somewhere
* Create symbolic link to `todo.py` somewhere on the search path
* Rready to run `todo`

E.g.
```
cd ~/Documents
git clone https://github.com/smackcrane/todo.git
sudo ln -s ~/Documents/todo/todo.py /usr/local/bin/todo
todo
```

#### Written on Lubuntu

No effort has been made yet for compatibility with other platforms.


