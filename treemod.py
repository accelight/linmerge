#!/home/araki/bin/python3.3
# -*- coding:utf-8 -*-

import sys, os, time, datetime, shlex, subprocess, re

class Node:
    def __init__(self, leftTime="", rightTime="", isdir=None, next=None, child=None, name=None, status=None, path=None, parent=None):
        self.next = next
        self.child = child
        self.status = status #diffした時の結果．l,r,d,iのいずれか
        self.name = name
        self.path = path
        self.parent = parent
        self.leftTime = leftTime
        self.rightTime = rightTime
        self.isdir = isdir
    def show_info(self):
        print("----------------------------------")
        print(self)
        print("name: " + str(self.name))
        print("isdir: " + str(self.isdir))
        print("status: " + str(self.status))
        print("parent: " + str(self.parent))
        print("child: " + str(self.child))
        print("next: " + str(self.next))
        print("leftTime: " + str(self.leftTime))
        print("rightTime: " + str(self.rightTime))

class Tree(Node):
    def __init__(self, name, left, right, dict={}):
        root = Node(name = name, status="")
        self.root = root
        self.dict = dict
        self.left = left
        self.right = right
    def set_Node(self, parent, node):
        if parent.child is None:
            parent.child = node
        else:
            tmp_node = parent.child
            while tmp_node.next is not None:
                tmp_node = tmp_node.next
            tmp_node.next = node


def make_Tree(tree, path, status):
    var = 0
    key = ["/".join(path[0:i+1]) for i in range(len(path))] #挿入するノードのキー=そのノードのrootからのフルパス
    while var < len(path):
        left_path = tree.left + "/" + key[var]
        right_path = tree.right + "/" + key[var]
        left_time_stamp = getTimeStamp(left_path)
        right_time_stamp = getTimeStamp(right_path)
        isdir = checkIsDir(left_path) or checkIsDir(right_path)
        if var == 0:
            if key[var] not in tree.dict:
                if len(path) == 1:
                    tree.dict[key[var]] = Node(name=path[var], isdir=isdir, status=status, parent=tree.root, leftTime=left_time_stamp, rightTime=right_time_stamp)
                else:
                    tree.dict[key[var]] = Node(name=path[var], isdir=isdir, status="", parent=tree.root, leftTime=left_time_stamp, rightTime=right_time_stamp)
                tree.set_Node(parent=tree.root, node=tree.dict[key[var]])
            else:
                pass
        elif 0 < var < len(path)-1:
            if key[var] not in tree.dict:
                tree.dict[key[var]] = Node(name=path[var], isdir=isdir, status="", parent=tree.dict[key[var-1]], leftTime=left_time_stamp, rightTime=right_time_stamp)
                tree.set_Node(parent=tree.dict[key[var-1]], node=tree.dict[key[var]])
            else:
                pass
        elif var == len(path) -1:
            tree.dict[key[var]] = Node(name=path[var], isdir=isdir, status=status, parent=tree.dict[key[var-1]], leftTime=left_time_stamp, rightTime=right_time_stamp)
            tree.set_Node(parent=tree.dict[key[var-1]], node=tree.dict[key[var]])
        var += 1

def getTimeStamp(path):
    try:
        time=os.stat(path).st_mtime
        time=datetime.datetime.fromtimestamp(time)
        time=time.strftime("%Y-%m-%d %H:%M:%S")
    except:
        time=""
    return time

def checkIsDir(path):
    try:
        return os.path.isdir(path)
    except:
        return false



if __name__ == "__main__":
    sys.exit()



