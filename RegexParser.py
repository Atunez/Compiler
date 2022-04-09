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
        
    
        
        

testRegex = "(a|b)*abb#"
AST, _, _ = buildAST(parseIntoTokens(testRegex), 0, 1)
binaryAST = buildTree(AST.children)
print(AST)
print(binaryAST)
