from tokenize import group
from tracemalloc import start
from turtle import position


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
LetterByPos = dict()
PositionOfEnd = -1
def buildAST(regex, start, counter):
    global LetterByPos, PositionOfEnd
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
                LetterByPos[c] = regex[i]
                if regex[i] == "#":
                    PositionOfEnd = c
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
        return firstpos(node.children[0]).union(firstpos(node.children[1]))
    elif node.label == "Conc":
        if(nullable(node.children[0])):
            return firstpos(node.children[0]).union(firstpos(node.children[1]))
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

def getTransitionsFromAST(binaryAST):
    startState = frozenset(firstpos(binaryAST))
    Dstates = set()
    Dstates.add(startState)
    seen = set()
    transitions = dict()
    while len(Dstates) != 0:
        setToConsider = frozenset(Dstates.pop())
        seen.add(setToConsider)
        for letter in alphabet:
            U = set()
            for node in setToConsider:
                if LetterByPos[node] == letter:
                    U = U.union(posDic[node])    
            U = frozenset(U)
            if U not in seen:
                Dstates.add(U)
            transitions[(setToConsider, letter)] = U 
    return transitions

acceptingGroups = set() 
startingGroupGlobal = None
def simplifyTableName(transition:dict, posOfAccept, startingLetterIn):
    global acceptingGroups, startingGroupGlobal
    startingLetter = startingLetterIn
    betterDictionary = dict()
    realDictionary = dict()
    for (key, letter), value in transition.items():
        if key not in betterDictionary:
            betterDictionary[key] = startingLetter
            startingLetter = chr(ord(startingLetter) + 1)
        if value not in betterDictionary:
            betterDictionary[value] = startingLetter
            startingLetter = chr(ord(startingLetter) + 1)
        if startingGroupGlobal is None:
            startingGroupGlobal = betterDictionary[key]
        if posOfAccept in value or posOfAccept == value: 
            realDictionary[(betterDictionary[key], letter)] = (betterDictionary[value], True)
            acceptingGroups.add(betterDictionary[value])
        else:
            realDictionary[(betterDictionary[key], letter)] = (betterDictionary[value], False)
    return realDictionary

def getAccepting(transitions):
    accept = set()
    reject = set()
    for (a,b), _ in transitions.items():
        if a in acceptingGroups:
            accept.add(a)
        else:
            reject.add(a)
    return accept, reject

def sameGroup(transitions, group1, entire_group):
    for letter in alphabet:
        (t1, _) = transitions[(group1, letter)] 
        # this group doesn't belong in the whole group, if it maps to something
        # not in the group
        if t1 not in entire_group and t1 is not group1:
            return False
    return True    

def findGroup(goTo, RepsFor):
    for i in range(len(RepsFor)):
        if goTo in RepsFor[i]:
            return i

def minimizeDFA(transitions):
    partition = [getAccepting(transitions)]
    newPartition = []
    while True:
        for bolier in partition:
            for group in bolier:
                # for every group in tempGroups, you only need to look
                # at the last group in each entry to see if they are the "same"
                for state in group:
                    # if this is the first time then we have our first partition
                    if len(newPartition) == 0:
                        newPartition.append(set(state))
                    else:
                        # for every partition we have
                        broke = False
                        for i in range(len(newPartition)):
                            # if it doesn't go to any partition then add it as a new thing
                            if sameGroup(transitions, state, newPartition[i]):
                                newPartition[i].add(state)
                                broke = True
                                break
                        if not broke:
                            newPartition.append(set(state))
        if newPartition == partition:
            break
        else:
            partition = newPartition
            newPartition = []
    finalDFA = dict()
    # to make the finalDFA, you need to figure out
    # who will represent each group
    Reps = []
    RepsFor = []
    for bolier in partition:
        RepsFor.append(bolier)
        for group in bolier:
            Reps.append(group)
            break
    startingGroup = None
    print(len(Reps))
    for i in range(len(Reps)):
        # this would only happen once...
        if startingGroupGlobal in RepsFor[i]:
            startingGroup = Reps[i]
        for letter in alphabet:
            (goTo, end) = transitions[(Reps[i], letter)]
            groupIdx = findGroup(goTo, RepsFor)
            # the group this needs to go is itself...
            finalDFA[(Reps[i], letter)] = (Reps[groupIdx], end)
            
    return finalDFA, startingGroup
            

def combinationMachine(firstTransitions, secondTransitions):
    combinedDFA = dict()
    endingStates = []
    for letter in alphabet:
        for (key, inp), (value, out) in firstTransitions.items(): 
            if inp != letter:
                continue
            for (key2, inp2), (value2, out2) in secondTransitions.items():  
                if inp2 != letter:
                    continue
                # given Qi, a = Qj and Qi', a = Qj'
                # then, (Qi, Qi'), a = (Qj, Qj')
                combinedDFA[((key, key2), letter)] = (value, value2)
                if out2 and out:
                    endingStates.append((value,value2))
    return combinedDFA, endingStates

alphabet = "ab"
testRegex = "((a*ba*)*)#"
AST, _, _ = buildAST(parseIntoTokens(testRegex), 0, 1)
binaryAST = buildTree(AST.children)
followpos(binaryAST, set(), set(), set())
basicTran = simplifyTableName(getTransitionsFromAST(binaryAST), PositionOfEnd, "R")
pOend1 = PositionOfEnd
start1 = startingGroupGlobal

testRegex = "((a|b)*aa(a|b)*)#"
AST, _, _ = buildAST(parseIntoTokens(testRegex), 0, 1)
binaryAST = buildTree(AST.children)
followpos(binaryAST, set(), set(), set())
startingGroupGlobal = None
basicTran2 = simplifyTableName(getTransitionsFromAST(binaryAST), PositionOfEnd, "A")
pOend2 = PositionOfEnd
start2 = startingGroupGlobal

bigDFA, accpetingStates = combinationMachine(basicTran, basicTran2)
print(bigDFA)
print(accpetingStates)

bigDFA = simplifyTableName(bigDFA, accpetingStates[0], "A")

startingGroupGlobal = (start1, start2)


print(startingGroupGlobal)
print(bigDFA)

finalDFA, startingGroup = minimizeDFA(bigDFA)
print(finalDFA)
# print(basicTran)
# transitionsFirst = simplifyTableName(basicTran, PositionOfEnd, "A")
# print(transitionsFirst)
# finalDFA, startingGroup = minimizeDFA(transitionsFirst)
# print(finalDFA)