#!/usr/local/bin/python3
# -*- coding:utf-8 -*-
#上のエンコーディング指定は、1行目か２行目に書く必要がある

import sys, os, re, shlex, subprocess, curses, locale, time, datetime, treemod, filecmp, argparse



def CheckArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument("dirs", nargs=2, help="input two dirs you want to compare")
    parser.add_argument("-r", "--recursive", help="display all files recursively", action="store_true")
    parser.add_argument("-s", "--report-identical-file", help="report when two files are the same", action="store_true")
    args=parser.parse_args()
    return args

#print(CheckArgument())
#exit()


def GetDiffResults(args):
    dirs = args.dirs
    #dirsを/から始まるフルパスに書き換える
    for i in 0, 1:
        dirs[i] = dirs[i].rstrip("/")
        if not dirs[i].startswith("/"):
            dirs[i] = os.getcwd() + "/" + dirs[i]
    #ディレクトリのパスが正しいかチェック
    if not (os.path.isdir(dirs[0]) and os.path.isdir(dirs[1])):
        print("ERROR:No such directory")
        sys.exit()
    #-rオプションがついているとき
    if args.report_identical_file == True:
        cmd = "LANG=C diff -rqs {0} {1}".format(dirs[0], dirs[1])
    else:
        cmd = "LANG=C diff -rq {0} {1}".format(dirs[0], dirs[1])
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout_ori, stderr = p.communicate()
    stdout = stdout_ori.decode("utf-8", "ignore")
    diff_results = re.split("\n", stdout)
    diff_results.pop(-1)#末尾の改行コードを取り除く
    #diffの結果が空リストでないかチェック
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
            if diff_result_words[2].startswith(left_path):#左のみに存在
                del_len=len(left_path.split("/"))
                del path_list[0:del_len]
                treemod.make_Tree(tree, path=path_list, status="l")
            else:#右のみに存在
                del_len=len(right_path.split("/"))
                del path_list[0:del_len]
                treemod.make_Tree(tree, path=path_list, status="r")
        else:#左右に存在
            tmp_path_str = diff_result_words[1].replace(left_path+"/", "", 1)
            path_list = tmp_path_str.split("/")
            if diff_result_words[-1] == "identical":
                treemod.make_Tree(tree, path=path_list, status="i")
            elif diff_result_words[-1] == "differ":
                treemod.make_Tree(tree, path=path_list, status="d")
    return tree

#MakeTreeFromDiffResultsからの変化を最小にしたので冗長．改良の余地あり．
def MakeRecursiveTreeFromDiffResults(left_path, right_path, diff_results):
    tree = treemod.Tree(name="root", left=left_path, right=right_path)
    for diff_result in diff_results:
        diff_result_words = diff_result.split()
        if diff_result_words[0] == "Only":
            tmp_path_str = diff_result_words[2].rstrip(":")
            path_list = tmp_path_str.split("/")
            path_list.append(diff_result_words[3])
            if diff_result_words[2].startswith(left_path):#左のみ
                del_len=len(left_path.split("/"))
                del path_list[0:del_len]
                path_list=["/".join(path_list)]
                treemod.make_Tree(tree, path=path_list, status="l")
            else:#右のみ
                del_len=len(right_path.split("/"))
                del path_list[0:del_len]
                path_list=["/".join(path_list)]
                treemod.make_Tree(tree, path=path_list, status="r")
        else:
            tmp_path_str = diff_result_words[1].replace(left_path+"/", "", 1)
            path_list = tmp_path_str.split("/")
            path_list=["/".join(path_list)]
            if diff_result_words[-1] == "identical":
                treemod.make_Tree(tree, path=path_list, status="i")
            elif diff_result_words[-1] == "differ":
                treemod.make_Tree(tree, path=path_list, status="d")
    return tree

def CheckRecursiveFlagAndMakeTree(is_recursive, left_path, right_path, diff_results):
    if is_recursive == True:
        return MakeRecursiveTreeFromDiffResults(left_path, right_path, diff_results)
    else:
        return MakeTreeFromDiffResults(left_path, right_path, diff_results)



"""
ここから描画
"""
class CursesApp(object):
    __slots__=['stdscr', 'callbacks', 'input']
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.noecho() #エコーバックなし
        curses.cbreak() #cbreakモードに入る
        curses.curs_set(1) #カーソルの状態設定
        self.stdscr.keypad(1) #エスケープシーケンスが解釈される
        self.callbacks={}
        self.callbacks[ord('q')]=self.quit #終了コマンド
        self.x=0
        self.y=0
        (self.h, self.w)=self.stdscr.getmaxyx() #高さ，幅を取得
    def finalize(self):
        self.stdscr.keypad(0)
    def loop(self):
        while 1:
            c = self.stdscr.getch()
            if c in self.callbacks:
                if self.callbacks[c]():
                    break
            else:
                self.default(c)
    def quit(self):
        return True
    def default(self, c):
        pass


class suspend_curses():
    def __enter__(self):
        curses.endwin()
    def __exit__(self, exc_type, exc_val, tb):
        newscr = curses.initscr()
        newscr.refresh()
        curses.doupdate()


"""
表示領域を指定したpad
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
        self.format="%-"+("%d" % (self.right-self.left-1))+"s" #文字列を左寄せ
        self.pad=curses.newpad(self.lines, self.right-self.left)

    def setText(self, y, x, text, attrib=curses.A_NORMAL):
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
            self.setText(self.selected, 0, self.items[self.selected], curses.A_NORMAL)
            self.selected=index
        self.setText(self.selected, 0, self.items[self.selected], curses.A_REVERSE)
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
ファイルシステムを移動するサンプル
"""
class Filer(CursesApp):
    def __init__(self, stdscr, tree):
        CursesApp.__init__(self, stdscr)
        self.selected = 0
        self.topline = 0
        self.format = "%-"+("%d" % (self.w-1))+"s"
        self.mainPad = None
        self.dirInfoPad = None
        self.cmdPad = None
        self.tree = tree
        self.start = tree.root
        self.oldNode=treemod.Node(name="..", status="")
        self.path = ""
        self.setPadInfo()
        self.mainPad.select(0)
        self.AllPadRefresh()
        # keyboard callbacks
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
        #ディレクトリ情報のpad
        self.dirInfoPad=curses.newpad(1, self.w-1)
        self.dirInfoPad.addnstr(0, 0, "Left: " + self.tree.left + self.path, int((self.w-1)/2))
        self.dirInfoPad.addnstr(0, int(self.w/2), "Right: " + self.tree.right + self.path, int((self.w-1)/2))
        #self.dirInfoPad.refresh(0, 0, 0, 0, 1, self.w-1)
        #コマンドラインのpad
        self.cmdPad=PadList(self.h-1, 0, self.h, self.w-1, 1)
        self.cmdPad.setText(0, 0, "> ")
        #説明文
        self.textPad=PadList(2, 0, 3, self.w-1, 1)
        #text="qで終了．Enterでディレクトリin/ファイルを開く．h-lで左-右マージ．"
        #self.textPad.setText(0, 0, "j:scroll down, k:scroll up, g:scroll top, G:scroll bottom, q:exit, h:merge to left, l:merge to right")
        #メインのPad
        time_len = 20
        status_len = 6
        time_space = "                   "
        joint_space = "    "
        if self.mainPad:
            self.selected = self.mainPad.selected
            self.mainPad.clear()
        self.mainPad=PadList(top=5, left=0, bottom=self.h-2, right=self.w-1, lines=len(self.current_nodes))
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
            else:#選択したノードがフォルダかつ左右に存在
                info_text = joint_space.join(["      ", node.leftTime, node.rightTime])
            text = joint_space.join([folder_text, info_text])
            self.mainPad.setText(i, 0, text)
        #self.mainPad.select(0)
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
            cmd_result = self.ExecuteShellCmd(cmd)
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
        else: #選択ノードがフォルダかつ左右に存在
            self.start = node
            self.path = self.path + "/" + node.name
            self.setPadInfo()
            self.mainPad.select(0)
            self.AllPadRefresh()
    def AllPadRefresh(self):
        self.cmdPad.setText(0, 0, "> ")
        self.cmdPad.refresh()
        self.textPad.refresh()
        self.dirInfoPad.refresh(0, 0, 0, 0, 1, self.w-1)
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
    def ExecuteShellCmd(self, cmd):
        self.cmdPad.setText(0, 0, "> " + cmd + "    [y/n]?")
        self.cmdPad.refresh()
        c = self.mainPad.pad.getch()
        if c == ord("y"):
            with suspend_curses():
                subprocess.call(cmd, shell=True)
            return 1
        elif c == ord("n"):
            self.cmdPad.setText(0, 0, "> ")
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
    def loop(self):
        while 1:
            c = self.mainPad.pad.getch() # stdscrのgetchだと画面が更新されない
            if c in self.callbacks:
                if self.callbacks[c]():
                    break
            else:
                self.default(c)


#デバッグ用
def q():
    sys.exit()

def main(stdscr, tree):
    locale.setlocale(locale.LC_ALL, "")
    app=Filer(stdscr=stdscr, tree=tree)
    app.loop()
    app.finalize()


if __name__=='__main__':
    args = CheckArgument()
    left_path, right_path, diff_results = GetDiffResults(args)
    tree = CheckRecursiveFlagAndMakeTree(args.recursive, left_path, right_path, diff_results)
    curses.wrapper(main, tree)

