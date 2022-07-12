# The directory is in
import os
curDir = os.getcwd()
indexOfDL = curDir.index("Downloads")
print(f"The directory is {os.getcwd()[indexOfDL:]}")


# Start Graph Algorithms here:
    
# define a stack
class Stack:
    def __init__(self):
        self.top = None
        
    def is_empty(self):
        return self.top is None
        
    def push(self, val):
        self.top = Node(val, self.top)
        
    def pop(self):
        if self.is_empty():
            raise RuntimeError('Stack is empty')
    
        val = self.top.value
        self.top = self.top.next
        return val
        
class Queue:
    def __init__(self):
        self.first = None
        self.last = None
        
    def is_empty(self):
        return self.first is None
    
    def enqueue(self, val):
        if self.first is None:
            self.first = self.last = Node(val)
        else:
            self.last.next = Node(val)
            self.last = self.last.next
            
    def dequeue(self):
        if self.is_empty():
            raise RuntimeError('Queue is empty')

        val = self.first.value
        self.first = self.first.next
        return val
    
def dfs_search(G,src):
    marked = {}
    node_from = {}
    
    stack = Stack()
    marked[src] = True
    stack.push(src)
    
    while not stack.is_empty():
        v = stack.pop()
        for w in G[v]:
            if not w in marked:
                node_from[w] = v
                marked[w] = True
                stack.push(w)
        return node_from

def path_to(node_from, src, target):
    if not target in node_from:
        raise ValueError('Unreachable')
        
    path = []
    v = target
    while v != src:
        path.append(v)
        v = node_from[v]
    
    path.append(src)
    path.reverse()
    return path

def bfs_search(G, src):
    marked = {}
    node_from = {}
    
    q = Queue()
    marked[src] = True
    q.enqueue(src)
    
    while not q.is_empty():
        v = q.dequeue()
        for w in G[v]:
            if not w in marked:
                node_from[w] = v
                marked[w] = True
                q.enqueue(w)
    
    return node_from