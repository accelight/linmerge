#  Welcome to linmerge
Linmerge is a command line based directory diff tool written in python2.

## Description
With windows, we have strong diff & merge tool [WinMerge](https://sourceforge.net/projects/winmerge/).
With Linux, however, when you work under command line, there was not a good one so far.
But here, **linmerge** is the answer!
Linmerge will serch all files and subdirectories and show you difference.
If you want, you can merge one to another or use vimdiff to edit them subsequently.

## Demo
![Demo](https://github.com/chari8/linmerge/blob/master/demo.gif)

## Requirement
python-2.x<br>
**Note that this does not work under python-3.x currently!**

## Usage
### Basic usage
#### To start linmerge

```
python linmerge.py [dir1] [dir2]
```

Put directory names in [dir1] & [dir2].

#### While linmerge is running
Basically keybindings are based on vim.

|Key|Action|
|:-:|:------|
|j|scroll down|
|k|scroll up|
|G|scroll to bottom|
|g|scroll to top|
|Enter|edit file / see subdirectories (depends on situation)|
|h|merge right file/directory to left (if can)|
|l|merge left file/directory to right (if can)|
|q / Esc|exit|

### Options
This is how to add option.

```
python linmerge.py [options] [dir1] [dir2]
```

Like many other CUI tools, linmerge accept both short style option which begin with `-` and long ones begins with `--`.
Here's list.

|Option|Action|
|:-----|:-----|
|-h / --help|show help|
|-l / --list|display files in list style|
|-s / --show|show identical files|
|-w / --space|ignore space|
|-i / --case|ignore case|
|-B / --black|ignore blank line|
|-b / --o-space|ignore when only space changed|
|-e / --tab|ignore tab expansion

## Install
Simply download files and put two python files in parent directory of directories which you want compare.

```example
git clone https://github.com/accelight/linmerge.git
cp linmerge/*.py [parent directory]
```

## To do / reported bugs
We adimit that there are bunch of things to improve.
Here's our to do list. 

* rewrite it with python3
* prepare cool installer
* when the window width is not enough, went wrong

## Contribution
Feel free to tell us your **cool** idea!
Here's how you can help us.

* Send issues
* Send pull requeset

In case you want to try other things, contact us!
Let's think togeter!

## Licence
Code is under the [GPLv3 license](https://github.com/accelight/linmerge/blob/master/LICENSE)

## Author / Contact

* suguru araki - original author
* [shuohang gao (HN: chari8)](https://chari8.github.io) - current maintainer

contact: linmerge@accelight.co.jp
