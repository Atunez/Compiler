
from tkinter.messagebox import NO


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
def buildAST(regex, start):
    AST = Node(list(), -1, "Conc")
    i, c = start, 1
    while i < len(regex):
        match regex[i]:
            case "(":
                rAST, i = buildAST(regex, i+1)
                AST.children.extend(rAST.children)
            case ")":
                return AST, i+1
            case "*":
                AST.children.append(Node([AST.children.pop(-1)], -1, "Star"))
                i += 1
            case "|":
                prevNode = AST.children.pop(-1)
                nextNode, i = buildAST(regex, i+1)
                toAdd = list()
                toAdd.append(prevNode)
                toAdd.extend(nextNode.children)
                AST.children.append(Node(toAdd , -1, "Or"))
                return AST, i
            case _:
                unit = Node(list(), c, regex[i])
                c += 1
                i += 1
                AST.children.append(unit)
    return AST, -1

#testRegex = "(a|b)*abb#"
testRegex = "ab*c(a|b*)(d)d|e"
AST, _ = buildAST(parseIntoTokens(testRegex), 0)
print(AST)
