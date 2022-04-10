from cProfile import label
from itertools import count

class Node:
    children = list()
    value = -1
    label = ""
    def __init__(self, children, value, label):
        self.children = children
        self.value = value
        self.label = label
        
    def isEmpty(self):
        return self.label == ""
    
    def __str__(self):
        output = self.label
        if self.children is None:
            return output 
        for i in range(len(self.children)):
            output += "{" + str(self.children[i]) + "}"
        return output
        
        

def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return False


# Need to use this to detect errors in the given regex
def parseIntoTokens(regex):
    tokens = []
    i = 0
    while i  < len(regex):
        match regex[i]:
            case "(", ")", "*", "|":
                tokens.append(regex[i])
                i += 1
            case "[":
                tval = "["
                while regex[i] != "]":
                    i += 1
                    tval += regex[i]
                i += 1
                tokens.append(tval)
            case _:
                if regex[i] == "\\" and regex[i+1]:
                    tokens.append("\l")
                    i += 2
                    continue 
                tokens.append(regex[i])
                i += 1
    return tokens

# Assume a "valid" regex
def buildAST(regex, start, counter):
    AST = Node(list(), -1, "Conc")
    i, c = start, counter
    while i < len(regex):
        match regex[i]:
            case "(":
                rAST, i, c = buildAST(regex, i+1, c)
                AST.children.extend(rAST.children)
            case ")":
                return AST, i+1, c
            case "*":
                AST.children.append(Node([AST.children.pop(-1)], -1, "Star"))
                i += 1
            case "|":
                prevNode = AST.children.pop(-1)
                nextNode, i, c = buildAST(regex, i+1, c)
                toAdd = list()
                toAdd.append(prevNode)
                toAdd.extend(nextNode.children)
                AST.children.append(Node(toAdd , -1, "Or"))
                return AST, i, c
            case _:
                if regex[i] == "\l":
                    AST.children.append(Node(list(), -1, regex[i]))
                    i += 1
                    continue
                unit = Node(list(), c, regex[i])
                c += 1
                i += 1
                AST.children.append(unit)
    return AST, -1, c

def buildTree(AST):
    if len(AST) == 1:
        return AST[0]
    # Need some queue or stack so that
    # Take off 2, make new node, put back in...
    # we will reuse the Node class st: children[0] is left (or single...) 
    # and children[1] is right
    rTree = buildTree(AST[:-1])
    return Node([rTree, AST[-1]], -1, "Conc")


# Return true if this node can accept null 
def nullable(node:Node):
    if node.label == "\l" or node.label == "Star":
        return True
    if node.value != -1:
        return False
    if node.label == "Or":
        return nullable(node.children[0]) or nullable(node.children[1])
    else:
        return nullable(node.children[0]) and nullable(node.children[1])


def firstpos(node:Node):
    retSet = set()
    if node.label == "\l":
        return retSet
    if node.value != -1:
        retSet.add(node.value)
        return retSet
    if node.label == "Or":
        retSet = firstpos(node.children[0])
        retSet = retSet.union(firstpos(node.children[1]))
        return retSet
    elif node.label == "Conc":
        if(nullable(node.children[0])):
            return retSet.union(firstpos(node.children[1]))
        else:
            return firstpos(node.children[0])
    else:
        return firstpos(node.children[0])

def lastpos(node:Node):
    retSet = set()
    if node.label == "\l":
        return retSet
    if node.value != -1:
        retSet.add(node.value)
        return retSet
    if node.label == "Or":
        return firstpos(node.children[0]).union(firstpos(node.children[1]))
    elif node.label == "Conc":
        if(nullable(node.children[1])):
            return firstpos(node.children[0]).union(firstpos(node.children[1]))
        else:
            return firstpos(node.children[1])
    else:
        return firstpos(node.children[0])

posDic = dict()
def followpos(node:Node, recurCat:set, lastPosStar: set, firstPosStar: set):
    global posDic
    if node.value != -1:
        if node.value in lastPosStar:
            posDic[node.value] = recurCat.union(firstPosStar)
        else:
            posDic[node.value] = recurCat
        return
    if node.label == "Conc":
        # if n is a conc node, then:
        # for every value i in lastpos(c1), all of firstpos(c2) are in followpos(i)
        toGoLeft = firstpos(node.children[1])
        # namely, the left will get firstpos(c2)
        # right will get whatever was in the recursion
        followpos(node.children[0], toGoLeft, lastPosStar, firstPosStar)
        followpos(node.children[1], recurCat, lastPosStar, firstPosStar)
    if node.label == "Star":
        # this node will only have 1 child...
        # if n is a star node, and i is a position in lastpos(n)
        # then all of firstpos(n) are in followpos(i)
        lastPos = lastpos(node)
        firstPos = firstpos(node)
        followpos(node.children[0], recurCat, lastPosStar.union(lastPos), firstPosStar.union(firstPos))
    elif node.label == "Or":
        # Or does nothing...
        followpos(node.children[0], recurCat, lastPosStar, firstPosStar)
        followpos(node.children[1], recurCat, lastPosStar, firstPosStar)
        
def checkPos(binaryAST:Node):
    print("This is node: " + str(binaryAST))
    print(firstpos(binaryAST))
    print(lastpos(binaryAST))
    for node in binaryAST.children:
        checkPos(node)
    pass        

testRegex = "(a|b)*abb#"
AST, _, _ = buildAST(parseIntoTokens(testRegex), 0, 1)
binaryAST = buildTree(AST.children)
#print(AST)
#checkPos(binaryAST)
followpos(binaryAST, set(), set(), set())
print(posDic)
