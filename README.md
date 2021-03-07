## todo --- Command Line To-Do List

### Usage

`todo <command> <args>` manage to-do list from command line

`toeditor` start an interactive editor (which behaves the same, except not having to type `todo` every time)

##### Commands and arguments:

\<id> means a period-delimited list of numbers, e.g. 1.4.2

\<name> means a string (quotes optional), e.g. check email

    list                pretty-print to-do list
        [-sub <id>]         only print specified task and subtasks

    add <name>          add a task
        [-sub <id>]         add as subtask of specified task
        [-top]              at at top of list (rather than default bottom)

    rm <id>             remove a task
    finish, remove, fin     aliases for rm
    
    rename <id> [<name>]    rename a task; if name is not specified,
                            supplies current name for editing
        [-add]                  append instead of replacing
	edit				alias for rename
    
    move <id>           move a task; requires one of the following:
        -into <id2>         make a subtask of <id2>
        -to <id2>           move to position <id2>
        -upto <int>         move up to rank <int> within parent
        -upby <int>         move up <int> ranks within parent
        -downto <int>       move down to rank <int> within parent
        -downby <int>       move down <int> ranks within parent

    fold <id>           fold a task, i.e. children are not printed
        [-all]              fold all top-level tasks

    unfold <id>         unfold a task
        [-all]              unfold all top-level tasks

    focus <id>          focus on specified task; equivalent to always
                        including '-sub <id>' in commands that accept it

    unfocus             remove focus

    open <id>           equivalent to unfold + focus

    close               equivalent to fold (current focus task) + unfocus

    format <id> <str>   format a task with format <str>
                        to see known formats, try it and the error will tell you
    
    full_upgrade        upgrade from a previous version (rarely needed)

universal arguments, can be passed with any command

    -verbose            re-throws errors that are normally handled by
                        a chiding print statement
    
    -quiet              does not clear screen and re-print todo list

### (My) Setup

* Put contents of repo somewhere
* Create symbolic links somewhere on the search path

E.g.
```
cd ~/Documents
git clone https://github.com/smackcrane/todo.git
cd /usr/local/bin
sudo ln -s ~/Documents/todo/todo todo
sudo ln -s ~/Documents/todo/toeditor toeditor
```

#### Written on Lubuntu

No effort has been made yet for compatibility with other platforms.
