# -*- coding:utf-8 -*-
"""
Copyright (C) {2016} {Accelight Inc.}
"""
#specification about coding above must be stated in 1st or 2nd line

import sys, os, re, shlex, subprocess, curses, locale, time, datetime, treemod, filecmp, argparse

def CheckArgument():
	parser = argparse.ArgumentParser()
	parser.add_argument('dirs', nargs=2, help="input two dirs you want to compare")
	parser.add_argument("-l", "--list", help="display files in list style", action="store_true") 
	parser.add_argument("-s", "--show", help="show identical files", action="store_true")
	parser.add_argument("-w", "--space", help="ignore space", action="store_true")
	parser.add_argument("-i", "--case", help="ignore case", action="store_true")
	parser.add_argument("-B", "--blank", help="ignore blank line", action="store_true")
	parser.add_argument("-b", "--o-space", help="ignore when only space changed", action="store_true")
	parser.add_argument("-e", "--tab", help="ignore tab expansion", action="store_true")
	parser.add_argument("-v", "--version", action='version', version='linmerge v1.1')
	parser.add_argument("-x", "--exclude", help="exclued following dirs", action='append')
	args=parser.parse_args()
	return args


def GetDiffResults(args):
	dirs = args.dirs
	#replace dirs for fullpath beginning with /
	for i in 0, 1:
		dirs[i] = dirs[i].rstrip("/")
		if not dirs[i].startswith("/"):
			dirs[i] = os.getcwd() + "/" + dirs[i]
	#check dir exist or not
	if not (os.path.isdir(dirs[0]) and os.path.isdir(dirs[1])):
		print("ERROR:No such directory")
		sys.exit()
	#オプションをチェック
	#check option
	option_list = []
	if args.show:
		option_list.append("s")
	if args.space:
		option_list.append("w")
	if args.case:
		option_list.append("i")
	if args.blank:
		option_list.append("B")
	if args.o_space:
		option_list.append("b")
	if args.tab:
		option_list.append("e")
	
	#chedk if there is exclude option
	if args.exclude is not None:
		for word in args.exclude:
			option_list.append(' --exclude=' + word) #do not remove the blank space before --exclude

	if option_list != []:
		options = "".join(option_list)
		cmd = "LANG=C diff -rq{0} {1} {2}".format(options, dirs[0], dirs[1])
	else:
		cmd = "LANG=C diff -rq {0} {1}".format(dirs[0], dirs[1])
	p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	stdout_ori, stderr = p.communicate()
	stdout = stdout_ori.decode("utf-8", "ignore") 
	diff_results = re.split("\n", stdout)
	diff_results.pop(-1)#末尾の改行コードを取り除くremove \n in last
	#diffの結果が空リストでないかチェック
	#check if diff_results is empty or not
	if diff_results == []:
		print("There is no differnce. App quits.")
		sys.exit()
	return dirs[0], dirs[1], diff_results


def MakeTreeFromDiffResults(left_path, right_path, diff_results):
	tree = treemod.Tree(name="root", left=left_path, right=right_path)
	for diff_result in diff_results:
		diff_result_words = diff_result.split()
		if diff_result_words[0] == "Only":
			tmp_path_str = diff_result_words[2].rstrip(":")
			path_list = tmp_path_str.split("/")
			path_list.append(diff_result_words[3])
			if diff_result_words[2].startswith(left_path):#左のみに存在 / only exists in left
				del_len=len(left_path.split("/"))
				del path_list[0:del_len]
				#treemod.make_Tree(tree, path=path_list, status="l")
				tmp = treemod.make_Tree(tree, path=path_list, status="l")	#debug
			else:#右のみに存在 only exists in right
				del_len=len(right_path.split("/"))
				del path_list[0:del_len]
				#treemod.make_Tree(tree, path=path_list, status="r")
				tmp = treemod.make_Tree(tree, path=path_list, status="r")	#debug
		else:#左右に存在 / exist in both
			tmp_path_str = diff_result_words[1].replace(left_path+"/", "", 1)
			path_list = tmp_path_str.split("/")
			if diff_result_words[-1] == "identical":
				#treemod.make_Tree(tree, path=path_list, status="i")
				tmp = treemod.make_Tree(tree, path=path_list, status="i")	#debug
			elif diff_result_words[-1] == "differ":
				#treemod.make_Tree(tree, path=path_list, status="d")
				tmp = treemod.make_Tree(tree, path=path_list, status="d")	#debug
	return tree

#MakeTreeFromDiffResultsからの変化を最小にしたので冗長．改良の余地あり．
#made changes from MakeTreeFromDiffResults are smallest, can be improved
def MakeRecursiveTreeFromDiffResults(left_path, right_path, diff_results):
	tree = treemod.Tree(name="root", left=left_path, right=right_path)
	for diff_result in diff_results:
		diff_result_words = diff_result.split()
		if diff_result_words[0] == "Only":
			tmp_path_str = diff_result_words[2].rstrip(":")
			path_list = tmp_path_str.split("/")
			path_list.append(diff_result_words[3])
			if diff_result_words[2].startswith(left_path):#左のみ / only exists in left
				del_len=len(left_path.split("/"))
				del path_list[0:del_len]
				path_list=["/".join(path_list)]
				treemod.make_Tree(tree, path=path_list, status="l")
				#tmp = treemod.make_Tree(tree, path=path_list, status="l")	#debug
			else:#右のみ / only exists in right 
				del_len=len(right_path.split("/"))
				del path_list[0:del_len]
				path_list=["/".join(path_list)]
				treemod.make_Tree(tree, path=path_list, status="r")
				#tmp = treemod.make_Tree(tree, path=path_list, status="r")
		else:
			tmp_path_str = diff_result_words[1].replace(left_path+"/", "", 1)
			path_list = tmp_path_str.split("/")
			path_list=["/".join(path_list)]
			if diff_result_words[-1] == "identical":
				treemod.make_Tree(tree, path=path_list, status="i")
				#tmp = treemod.make_Tree(tree, path=path_list, status="i")
			elif diff_result_words[-1] == "differ":
				treemod.make_Tree(tree, path=path_list, status="d")
				#tmp = treemod.make_Tree(tree, path=path_list, status="d")
	return tree

def CheckRecursiveFlagAndMakeTree(is_recursive, left_path, right_path, diff_results):
	if is_recursive == True:
		return MakeRecursiveTreeFromDiffResults(left_path, right_path, diff_results)
	else:
		return MakeTreeFromDiffResults(left_path, right_path, diff_results)



"""
draw window
"""
class CursesApp(object):
	def __init__(self, stdscr):
		self.stdscr = stdscr
		curses.curs_set(0) #カーソルを表示しない / hide cursor
		self.stdscr.keypad(1) #エスケープシーケンスが解釈される / interprete escape sequences generated by keys
		self.x=0
		self.y=0
		(self.h, self.w)=self.stdscr.getmaxyx() #高さ，幅を取得 / get height and width of sceen


	def finalize(self):
		curses.nocbreak()
		self.stdscr.keypad(0)
		curses.echo()
		curses.endwin()

class suspend_curses():
	def __enter__(self):
		curses.endwin()
	def __exit__(self, exc_type, exc_val, tb):
		newscr = curses.initscr()
		newscr.refresh()
		curses.doupdate()


"""
pad for drawing
"""
class PadList(object):
	__slots__=['top', 'left', 'bottom', 'right', 'lines', 'topline', 'selected', 'items', 'pad', 'format']
	def __init__(self, top, left, bottom, right, lines):
		self.top=top
		self.left=left
		self.right=right
		self.bottom=bottom
		self.lines=lines
		self.topline=0
		self.selected=0
		self.items={}
		self.format="%-"+("%d" % (self.right-self.left-1))+"s" #文字列を左寄せ / left-align
		self.pad=curses.newpad(self.lines, self.right-self.left)

	def setText(self, y, x, text, attrib = curses.A_NORMAL):
		if y<0: 
			pass
		if y>=self.lines:
			pass
		self.items[y]=text
		#self.pad.addstr(y, x, (self.format % text), attrib)
		self.pad.addstr(y, x, text, attrib)
        
	def select(self, index):
		height=self.bottom-self.top
		if index<0: 
			index=0
		if index>=self.lines: 
			index=self.lines-1
		if index<self.topline:
			self.topline=index
		if index>self.topline+height:
			self.topline=index-height
		if self.topline+height>self.lines:
			self.topline=self.lines-height
		if self.selected!=index:
			self.setText(self.selected, 0, self.items[self.selected], color())
			self.selected=index
		self.setText(self.selected, 0, self.items[self.selected], color("mw","R"))
		self.refresh()

	def next(self):
		self.select(self.selected+1)
	def prev(self):
		self.select(self.selected-1)
	def refresh(self):
		self.pad.refresh(self.topline, 0, self.top, self.left, self.bottom, self.right)
	def clear(self):
		self.pad.erase()
		self.refresh()


"""
file system
"""
class Filer(CursesApp):
	__slots__=['callbacks']
	def __init__(self, stdscr, tree):
		CursesApp.__init__(self, stdscr)
		self.selected = 0
		self.topline = 0
		self.format = "%-"+("%d" % (self.w-1))+"s"
		self.mainPad = None
		self.dirInfoPad = None
		self.cmdPad = None
		self.titlePad = None
		self.tree = tree
		self.start = tree.root
		self.oldNode=treemod.Node(name="..", status="")
		self.path = ""
		self.setPadInfo()
		self.mainPad.select(0)
		self.AllPadRefresh()
		# keyboard callbacks
		self.callbacks={}
		self.callbacks[ord('q')]=self.retTrue
		self.callbacks[0x1b]=self.retTrue
		self.callbacks[ord('j')]=self.Down
		self.callbacks[curses.KEY_DOWN]=self.Down
		self.callbacks[ord('k')]=self.Up
		self.callbacks[curses.KEY_UP]=self.Up
		self.callbacks[ord('g')]=self.First
		self.callbacks[ord('G')]=self.Last
		self.callbacks[0x0a]=self.Enter
		self.callbacks[ord("h")]=self.CpToLeft
		self.callbacks[ord("l")]=self.CpToRight

	def setPadInfo(self):
		self.current_nodes=[]
		child =self.start.child
		if self.path != "":
			self.current_nodes.append(self.oldNode)
		while child is not None:
			self.current_nodes.append(child)
			child = child.next

		#title pad
		self.titlePad = PadList(0, 0, 1, self.w-1, 1)
		self.titlePad.setText(0, 0, "linmerge", color("bc","B"))
		self.titlePad.refresh()

		#ディレクトリ情報のpad / directory pad
		self.dirInfoPad = PadList(8, 0, 8, self.w-1, 1)
		self.dirInfoPad.setText(0, 0, "Left: " + self.tree.left + self.path, color("gb"))	
		self.dirInfoPad.setText(0, int(self.w/2), "Right: " + self.tree.right + self.path, color("gb"))
		self.dirInfoPad.refresh()

		#コマンドラインのpad / command pad
		self.cmdPad=PadList(9, 0, 9, self.w-1, 1)
		self.cmdPad.setText(0, 0, "> ", color("yb")) 
		self.cmdPad.refresh()

		#使い方のテキストを表示するためのpad / text pad to show how to use
		self.textPad=PadList(1, 0, 6, self.w-1, 6)
		#qで終了．Enterでディレクトリin/ファイルを開く．h-lで左-右マージ
		#q:exit Enter:directory in / open file, h-l:merge to left/right
		self.textPad.setText(0, 0, "="*(self.w-5), color("cb","B")) 
		self.textPad.setText(1, 0, "k:scroll up, g:scroll top", color("cb","B")) 
		self.textPad.setText(2, 0, "h:merge to left,  l:merge to right", color("cb","B")) 
		self.textPad.setText(3, 0, "j:scroll to down, G:scroll to bottom", color("cb","B")) 
		self.textPad.setText(4, 0, "q / ESC :exit", color("cb","B")) 
		self.textPad.setText(5, 0, "="*(self.w-5), color("cb","B")) 
		self.textPad.refresh()
		#self.textPad.setText(0, 0, "j:scroll down, k:scroll up, g:scroll top, G:scroll bottom, q:exit, h:merge to left, l:merge to right")

		#メインのPad / main pad
		time_len = 20
		status_len = 6
		time_space = "                   "
		joint_space = "    "
		if self.mainPad:
			self.selected = self.mainPad.selected
			self.mainPad.clear()
		self.mainPad=PadList(top=10, left=0, bottom=self.h-2, right=self.w-1, lines=len(self.current_nodes))
		for i, node in enumerate(self.current_nodes):
			tmp_folder_text = "{0:<"+ str(self.w-2*time_len-status_len-15) +"}"
			if node.isdir == True:
				name_text = node.name +"/"
			else:
				name_text = node.name
			folder_text = tmp_folder_text.format(name_text)
			if node.status == "l":
				info_text = joint_space.join(["L     ", node.leftTime, time_space])
			elif node.status == "r":
				info_text = joint_space.join(["     R", time_space, node.rightTime])
			elif node.status == "d":
				info_text = joint_space.join(["L != R", node.leftTime, node.rightTime])
			elif node.status == "i":
				info_text = joint_space.join(["L == R", node.leftTime, node.rightTime])
			else: #選択したノードがフォルダかつ左右に存在 / node selected is folder and exists in both
				info_text = joint_space.join([" DIR  ", node.leftTime, node.rightTime])
			text = joint_space.join([folder_text, info_text])
			if re.search("\A\.{2}", text.strip()) != None:   #上のディレクトリに戻るための選択肢を表示 / back to upper dir
				text = "<< back"
			self.mainPad.setText(i, 0, text)
		#self.mainPad.select(0)clear()
		#self.mainPad.refresh()

	def Enter(self):
		node = self.current_nodes[self.mainPad.selected]
		if node.name == "..":
			list = self.path.split("/")
			list.pop(-1)
			self.path = "/".join(list)
			path = self.tree.left + self.path
			self.start = self.start.parent
			self.setPadInfo()
			self.mainPad.select(0)
			self.AllPadRefresh()
		elif node.status == "l": 
			tmp_path = self.tree.left + self.path + "/" + node.name
			if node.isdir:
				pass
			else:
				cmd = "vimdiff {0}".format(tmp_path)
				cmd_result = self.ExecuteShellCmd(cmd)
				if cmd_result==True:
					while node != None:
						node.leftTime=treemod.getTimeStamp(tmp_path)
						node = node.parent
					self.setPadInfo()
					self.mainPad.select(self.selected)
					self.AllPadRefresh()
		elif node.status == "r": 
			tmp_path = self.tree.right + self.path + "/" + node.name
			if node.isdir:
				pass
			else:
				cmd = "vimdiff {0}".format(tmp_path)
				cmd_result = self.ExecuteShellCmd(cmd)
				if cmd_result==True:
					while node != None:
						node.leftTime=treemod.getTimeStamp(tmp_path)
						node = node.parent
					self.setPadInfo()
					self.mainPad.select(self.selected)
					self.AllPadRefresh()
		elif node.status == "d" or node.status == "i":
			left_path = self.tree.left + self.path + "/" + node.name
			right_path = self.tree.right + self.path + "/" + node.name
			cmd = "vimdiff {0} {1}".format(left_path, right_path)
			cmd_result = self.ExecuteShellCmd(cmd, 1)
			if cmd_result==True:
				if filecmp.cmp(left_path, right_path) == True:
					node.status="i"
				else:
					node.status="d"
				while node != None:
					node.leftTime=treemod.getTimeStamp(left_path)
					node.rightTime=treemod.getTimeStamp(right_path)
					node = node.parent
				self.setPadInfo()
				self.mainPad.select(self.selected)
				self.AllPadRefresh()
		else: #選択したノードがフォルダかつ左右に存在 / node selected is folder and exists in both
			self.start = node
			self.path = self.path + "/" + node.name
			self.setPadInfo()
			self.mainPad.select(1)	#一番上にくる<< backを飛ばして次のインデッックスから / select first index (pass "<<back" button)
			self.AllPadRefresh()
	def AllPadRefresh(self):
		#self.titlePad.refresh()
		#self.textPad.refresh()
		#self.dirInfoPad.refresh()
		self.cmdPad.setText(0, 0, "> ", color("yb")) 
		self.cmdPad.refresh()
		#self.dirInfoPad.refresh(0, 0, 0, 0, 1, self.w-1) #debug
		self.mainPad.refresh()
	def CpToLeft(self):
		node = self.current_nodes[self.mainPad.selected] 
		left_path = self.tree.left + self.path + "/" + node.name
		right_path = self.tree.right + self.path + "/" + node.name
		cmd = "cp -rf {0} {1}".format(right_path, left_path)
		if node.status=="r" or node.status=="d":
			cmd_result=self.ExecuteShellCmd(cmd)
			if cmd_result == True:
				time_stamp=treemod.getTimeStamp(left_path)
				node.status="i"
				while node != None:
					node.leftTime=time_stamp
					node = node.parent
				self.setPadInfo()
				self.mainPad.select(self.selected)
				self.AllPadRefresh()
		else:
			pass
		self.mainPad.refresh()
	def CpToRight(self):
		node = self.current_nodes[self.mainPad.selected] 
		left_path = self.tree.left + self.path + "/" + node.name
		right_path = self.tree.right + self.path + "/" + node.name
		cmd = "cp -rf {0} {1}".format(left_path, right_path)
		if node.status=="l" or node.status=="d":
			cmd_result=self.ExecuteShellCmd(cmd)
			if cmd_result == True:
				time_stamp=treemod.getTimeStamp(right_path)
				node.status="i"
				while node != None:
					node.rightTime=time_stamp
					node = node.parent
				self.setPadInfo()
				self.mainPad.select(self.selected)
				self.AllPadRefresh()
		else:
			pass
		self.mainPad.refresh()
	def ExecuteShellCmd(self, cmd, skip_ask=0):
		if skip_ask != 1: #when skip_ask=1, exec cmd without ask via cmdPad
			self.cmdPad.setText(0, 0, "> " + cmd + "    [y/n]?", color("yb"))
			self.cmdPad.refresh()
			c = self.mainPad.pad.getch()	
		else:
			c = ord("y")

		if c == ord("y"):
			with suspend_curses():
				subprocess.call(cmd, shell=True)
			return 1
		elif c == ord("n") or c == ord("j") or c == ord("k") or c == ord("g") or c == ord("G"):
			self.cmdPad.clear()
			self.cmdPad.setText(0, 0, ">", color("yb"))
			self.cmdPad.refresh()
			return 0
		else:
			self.ExecuteShellCmd(cmd)

	def Down(self):
		self.mainPad.next()
	def Up(self):
		self.mainPad.prev()
	def First(self):
		self.mainPad.select(0)
	def Last(self):
		self.mainPad.select(len(self.current_nodes)-1)
	def retTrue(self):
		return True
	def default(self, c):
		pass
	def loop(self):
		while 1:
			c = self.mainPad.pad.getch() # stdscrのgetchだと画面が更新されない / do not use stdscr.getch, screen won't refresh
			if c in self.callbacks:
				if self.callbacks[c]():
					break
			else:
				self.default(c)

"""
色の設定 / set color
"""
colorlist = {}

def setColor():
	global colorlist
	curses.start_color()
	if curses.has_colors():	#when terminal has color
		curses.use_default_colors()
		#curses.init_pair(1, "fore", "back")
		#red green yellow blue magenta cyan white
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
		curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
		curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
		curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
		curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
		curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)
		colorlist["bc"]=curses.color_pair(1)
		colorlist["gb"] = curses.color_pair(2)
		colorlist["mw"] = curses.color_pair(3)
		colorlist["cb"] = curses.color_pair(4)
		colorlist["rb"] = curses.color_pair(5)
		colorlist["yb"] = curses.color_pair(6)
	colorlist[""] = curses.A_NORMAL
	colorlist["R"] = curses.A_REVERSE
	colorlist["B"] = curses.A_BOLD
	colorlist["BL"] = curses.A_BLINK
	colorlist["D"] = curses.A_DIM
	colorlist["S"] = curses.A_STANDOUT
	colorlist["U"] = curses.A_UNDERLINE

def color( color1=None, color2=None): 
	global colorlist
	if color1 in colorlist:	#ターミナルがカラーに対応している時の色 / when terminal has color
		return colorlist[color1]
	elif color2 in colorlist: #ターミナルがカラーに対応していない時の色 / when terminal does not have color
		return  colorlist[color2]
	else:   #利用可能な色を指定しなかった時は白黒のノーマル / if both color are not available use normal color
		return colorlist[""]

#デバッグ用 / for debug
def q():
	sys.exit()


def main(stdscr, tree):
	locale.setlocale(locale.LC_ALL, "")
	setColor()
	app=Filer(stdscr=stdscr, tree=tree)
	app.loop()
	app.finalize()


if __name__=='__main__':
	args = CheckArgument()
	left_path, right_path, diff_results = GetDiffResults(args)
	tree = CheckRecursiveFlagAndMakeTree(args.list, left_path, right_path, diff_results)
	curses.wrapper(main, tree)


