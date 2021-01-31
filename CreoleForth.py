'''
    Program     : CreoleForth.py
    Author      : Joseph M. O'Connor
    Purpose     : A Forth scripting language built on top of Python
    Date        : Sep 2019
    Predecessors: Creole Forth for Delphi/Lazarus, Creole Forth for Excel,
                  and Creole Forth for JavaScript
'''

import datetime
import math
import re
# from pymsgbox import *
import copy

class Modules:
    def __init__(self, coreprims, interpreter, compiler, logicops, appspec):
        self.CorePrims = coreprims
        self.Interpreter = interpreter
        self.Compiler = compiler
        self.LogicOps = logicops
        self.AppSpec = appspec

class CreoleForthBundle:
    def __init__(self):
        self.Modules = None
        self.Address = []
        self.Dict = {}

class BasicForthConstants:
    def __init__(self):
        self.SmudgeFlag = "SMUDGED"
        self.ImmediateVocab = "IMMEDIATE"
        self.PrefilterVocab = "PREFILTER"
        self.PostfilterVocab = "POSTFILTER"
        self.ExecZeroAction = "EXEC0"
        self.CompLitAction = "COMPLIT"


class GlobalSimpleProps:
    def __init__(self, cfb):
        self.cfb = CreoleForthBundle() 
        self.CurrWord = None
        self.Scratch = None
        self.DataStack = []
        self.ReturnStack = []
        self.VocabStack = []
        self.PrefilterStack = []
        self.PostfilterStack = []
        self.PADarea = []
        self.ParsedInput = []
        self.loopLabels = ["I", "J", "K"]
        self.LoopLabelPtr = 0
        self.LoopCurrIndexes = [0, 0, 0]
        self.ParsedInputPtr = 0
        self.ExecPtr = 0
        self.ParamFieldPtr = 0
        self.InputArea = ""
        self.OutputAra = ""
        self.CurrentVocab = ""
        self.HelpCommentField = ""
        self.SoundField = ""
        self.CompiledList = ""
        self.BFC = BasicForthConstants()
        self.MinArgsSwitch = True  # Not sure this is needed
        self.pause= False
        self.onContinue = None
	
    def push(self, Stack):	
        Stack.append(self.Scratch)
	
    def pop(self, Stack):
        if len(Stack) == 0:
            print("Error: Stack Underflow")
            return -1
        else:
            self.Scratch = Stack.pop()
        return 0

    def cleanFields(self):
        self.Scratch = None
        self.CurrWord = None
        self.ParamField = []
        self.DataStack = []
        self.ReturnStack = []
        self.PADarea = []
        self.ParsedInput = []
        self.LoopLabelPtr = 0
        self.LoopCurrIndexes = [0, 0, 0]
        self.ParsedInputPtr = 0
        self.ExecPtr = 0
        self.ParamFieldPtr = 0
        self.InputArea = ""
        self.OutputArea = ""
        self.HelpCommentField = ""
        self.SoundField = ""
        self.CompiledList = []
        self.pause = None
	
# These objects are to be stored on the return stack
class ReturnLoc:
    def __init__(self, currWord, pfAddr):	
        self.CurrWord = currWord
        self.ParamFieldAddr = pfAddr

class LoopInfo:
    def __init__(self, label, index, limit):
        self.Label = label
        self.Index = index
        self.Limit = limit

# Colon definitions are built into the PAD area - each new entry
# is a triplet consisting of the word's fully qualified name, its
# dictionary address, and associated compilation action. 
class CompileInfo:
    def __init__(self, fqName, address, compileAction):
        self.FQName = fqName
        self.Address = address
        self.CompileAction = compileAction

class CorePrims:
    def __init__(self):
        self.Title = "Core Primitives Grouping"
        self.returnVal = 0
    
    # ( -- ) Do-nothing primitive which is surprisingly useful
    def doNOP(self, gsp):
        # empty method
        return 0
    
    # ( n1 n2 -- sum ) Adds two numbers on the stack"
    def doPlus(self, gsp):
        self.returnVal = gsp.pop(gsp.DataStack)
        val2 = gsp.Scratch
        self.returnVal = gsp.pop(gsp.DataStack)
        val1 = gsp.Scratch
        sum = float(val1) + float(val2)
        if sum == int(sum):
            sum = int(sum)
        gsp.Scratch = sum
        gsp.push(gsp.DataStack)
        return 0
    
    # ( n1 n2 -- difference ) Subtracts two numbers on the stack"
    def doMinus(self, gsp):
        self.returnVal = gsp.pop(gsp.DataStack)
        val2 = gsp.Scratch
        self.returnVal = gsp.pop(gsp.DataStack)
        val1 = gsp.Scratch
        difference = float(val1) - float(val2)
        if difference == int(difference):
            difference = int(difference)
        gsp.Scratch = difference     
        gsp.push(gsp.DataStack)  

    # ( n1 n2 -- product ) Multiplies two numbers on the stack
    def doMultiply(self, gsp):
        self.returnVal = gsp.pop(gsp.DataStack)
        val2 = gsp.Scratch
        self.returnVal = gsp.pop(gsp.DataStack)
        val1 = gsp.Scratch
        product = float(val1) * float(val2)
        if product == int(product):
            product = int(product)
        gsp.Scratch = product     
        gsp.push(gsp.DataStack)  
    
    # ( n1 n2 -- quotient ) Divides two numbers on the stack
    def doDivide(self, gsp):
        self.returnVal = gsp.pop(gsp.DataStack)
        val2 = gsp.Scratch
        self.returnVal = gsp.pop(gsp.DataStack)
        val1 = gsp.Scratch
        quotient = float(val1) / float(val2)
        if quotient == int(quotient):
            quotient = int(quotient)
        gsp.Scratch = quotient    
        gsp.push(gsp.DataStack)  
    
    # ( n1 n2 -- remainder ) Returns remainder of division operation
    def doMod(self, gsp):
        self.returnVal = gsp.pop(gsp.DataStack)
        val2 = gsp.Scratch
        self.returnVal = gsp.pop(gsp.DataStack)
        val1 = gsp.Scratch
        remainder = int(val1) % int(val2)    
        gsp.Scratch = remainder   
        gsp.push(gsp.DataStack)  
    
    # ( val --  val val ) Duplicates the argument on top of the stack
    def doDup(self, gsp):
        self.returnVal = gsp.pop(gsp.DataStack)
        val = gsp.Scratch
        gsp.DataStack.append(val)
        gsp.DataStack.append(val)
    
    # ( val1 val2 -- val2 val1 ) Swaps the positions of the top two stack arguments
    def doSwap(self, gsp):
        val2 = gsp.DataStack.pop()
        val1 = gsp.DataStack.pop()
        gsp.DataStack.append(val2)
        gsp.DataStack.append(val1)

    # ( val1 val2 val3 -- val2 val3 val1 ) Moves the third stack argument to the top
    def doRot(self, gsp):
        val3 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        val1 = gsp.DataStack.pop()

        gsp.DataStack.append(val2)
        gsp.DataStack.append(val3)
        gsp.DataStack.append(val1)

    # ( val1 val2 val3 -- val3 val1 val2 ) Moves the top stack argument to the third position
    def doMinusRot(self, gsp):
        val3 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        val1 = gsp.DataStack.pop()

        gsp.DataStack.append(val3)
        gsp.DataStack.append(val1)
        gsp.DataStack.append(val2)

    # ( val1 val2 -- val2 ) Removes second stack argument
    def doNip(self, gsp):   
        val1 = gsp.DataStack.pop()
        gsp.DataStack.pop()
        gsp.DataStack.append(val1)
    
    # ( val1 val2 -- val2 val1 val2 ) Copies top stack argument under second argument
    def doTuck(self, gsp):
        val2 = gsp.DataStack.pop()
        val1 = gsp.DataStack.pop()
        gsp.DataStack.append(val2)
        gsp.DataStack.append(val1)
        gsp.DataStack.append(val2)
    
    # ( val1 val2 -- val1 val2 val1 ) Copies second stack argument to the top of the stack
    def doOver(self, gsp):
        val2 = gsp.DataStack.pop()
        val1 = gsp.DataStack.pop()
        gsp.DataStack.append(val1)
        gsp.DataStack.append(val2)
        gsp.DataStack.append(val1)  

    # ( val -- ) Drops the argument at the top of the stack
    def doDrop(self, gsp):
        gsp.DataStack.pop()
    
    # ( val -- ) Prints the argument at the top of the stack
    def doDot(self,gsp):
        gsp.Scratch = gsp.DataStack.pop()
        print(gsp.Scratch)
    
    # ( -- n ) Returns the stack depth
    def doDepth(self, gsp):
        gsp.DataStack.append(len(gsp.DataStack))

    # ( -- ) prints out Hello World"
    def doHello(self, gsp):
        print("Hello world")
    
    # ( -- ) Either prints Tulip or pops up a message
    def doTulip(self, gsp):
        # uncomment the code to import pymsgbox to do the alert 
        # alert(text="Tulip", title='Creole Forth', 
        # button='OK')
        print("Tulip")
    
    # ( msg -- ) Pops up an alert saying the message
    def doMsgBox(self, gsp):
        msg = gsp.DataStack.pop()
        # alert(text=str(msg), title='Creole Forth', 
        # button='OK')

    # ( code -- ) Evaluates raw Python code
    def doEval(self, gsp):
        self.returnVal = gsp.DataStack.pop()
        pyCode = gsp.Scratch
        eval(pyCode)

    # ( -- ) Lists the dictionary definitions
    def doVList(self, gsp):
        definitionTable = []
        cw = None
        dtString = ""

        definitionTable.append(str(len(gsp.cfb.Address)) + " definitions")
        definitionTable.append("Index    Name    Vocabulary    Code Field    Param Field    Data Field   Help Field")
        definitionTable.append("-----    ----    ----------    ----------    -----------    ----------   ----------")
        for i in range(len(gsp.cfb.Address)):
            cw = gsp.cfb.Address[i]
            if (cw != None):
                definitionTable.append(str(gsp.cfb.Address[i].IndexField) + " " +
                                       str(gsp.cfb.Address[i].NameField)  + " " +
                                       str(gsp.cfb.Address[i].Vocabulary) + " " +
                                       str(gsp.cfb.Address[i].CodeFieldStr) + " " + 
                                       str(gsp.cfb.Address[i].ParamField) + " " + 
                                       str(gsp.cfb.Address[i].DataField) + " " + 
                                       str(gsp.cfb.Address[i].HelpField))
                
            definitionTable.append("")
            dtString = "\n".join(definitionTable)
        gsp.HelpCommentField = dtString
        print(dtString)
    
    # ( -- ) Prints today's date
    def doToday(self, gsp):
        today = datetime.datetime.now()
        print(today.strftime("%m/%d/%Y"))
    
    # ( --  time ) Puts the time on the stack
    def doNow(self, gsp):
        gsp.DataStack.append(datetime.datetime.now())
    
    # ( time -- ) Formats the time
    def doToHoursMinSecs(self, gsp):
        gsp.pop(gsp.DataStack)
        print(gsp.Scratch.strftime("%H:%M:%S"))

class Interpreter:
    def __init(self, cfb):
        self.Title = "Interpreter grouping"
    
    # splits the input into individual words
    def doParseInput(self, gsp):
        lines = gsp.InputArea.split("\n")
        for i in range(len(lines)):
            lines[i] += " __#EOL#__  "
        codeLine = " ".join(lines)
        gsp.ParsedInput = re.split(r'\s+', codeLine.strip())
    
    # Looks up the word based on its list index and executes whatever is in its code field
    def doRunWord(self, gsp):
        try:
            gsp.CurrWord = gsp.cfb.Address[gsp.ExecPtr]
            gsp.CurrWord.CodeField(gsp)
        except IndexError:
            print("Error: Stack underflow")
            gsp.cleanFields()
        except:
            print("Unknown error")

    # Run-time code for colon definitions
    def doColon(self, gsp):
        gsp.ParamFieldPtr = gsp.CurrWord.ParamFieldStart
        paramField = gsp.CurrWord.ParamField
        while (gsp.ParamFieldPtr < len(paramField)):
            addrInPF = paramField[gsp.ParamFieldPtr]
            currContextWord = gsp.CurrWord
            gsp.CurrWord = gsp.cfb.Address[addrInPF]
            codeField = gsp.cfb.Address[addrInPF].CodeField
            gsp.ParamFieldPtr += 1
            rLoc = ReturnLoc(currContextWord, gsp.ParamFieldPtr)
            gsp.ReturnStack.append(rLoc)
            codeField(gsp)
            rLoc = gsp.ReturnStack.pop()
            gsp.CurrWord = rLoc.CurrWord
            gsp.ParamFieldPtr = rLoc.ParamFieldAddr
    
    # ( -- ) Empties the vocabulary stack, then puts ONLY on it
    def doOnly(self, gsp):
        gsp.VocabStack = []
        gsp.VocabStack.append("ONLY")

    # ( -- ) Puts FORTH on the vocabulary stack
    def doForth(self, gsp):
        gsp.VocabStack.append("FORTH")

    # ( -- ) Puts APPSPEC on the vocabulary stack
    def doAppSpec(self, gsp):
        gsp.VocabStack.append("APPSPEC")

    # Search vocabularies from top to bottom for word. If found, execute. If not, it gets pushed onto the stack
    def doOuter(self, gsp):
        rawWord = ""
        fqWord = ""
        isFound = False
        gsp.ParsedInputPtr = 0
        gsp.ExecPtr = 0
        gsp.ParamFieldPtr = 0

        while (gsp.ParsedInputPtr < len(gsp.ParsedInput)):
            if (gsp.pause == False):
                rawWord = gsp.ParsedInput[gsp.ParsedInputPtr]
                searchVocabPtr = len(gsp.VocabStack) - 1
                while (searchVocabPtr >= 0):
                    fqWord = rawWord.upper() + "." + gsp.VocabStack[searchVocabPtr]
                    if (fqWord in gsp.cfb.Dict):
                        gsp.ExecPtr = gsp.cfb.Dict[fqWord].IndexField
                        self.doRunWord(gsp)
                        isFound = True
                        break
                    else:
                        searchVocabPtr -= 1
            if (isFound == False):
                gsp.DataStack.append(rawWord)
            gsp.ParsedInputPtr += 1
            isFound = False
        gsp.PADarea = []

class Compiler:
    def __init__(self):
        self.Title = "Compiler grouping"
    
    # ( n --) Compiles value off the TOS into the next parameter field cell
    def doComma(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        gsp.Scratch = int(gsp.DataStack.pop())
        token = gsp.Scratch
        newCreoleWord = gsp.cfb.Address[newRow]
        newCreoleWord.ParamField.append(token)
        newCreoleWord.ParamFieldStart += 1
        gsp.ParamFieldPtr = len(newCreoleWord.ParamField) - 1
    
    # Executes at time zero of colon compilation, when CompileInfo triplets are placed in the PAD area.
    # Example : comment handling - the pointer is moved past the comments
    # ( -- ) Single-line comment handling
    def doSingleLineCmts(self, gsp):
        while (gsp.ParsedInput[gsp.ParsedInputPtr].find("__#EOL#__") == -1):
            gsp.ParsedInputPtr += 1
    
    # ( -- ) Multiline comment handling
    def doParenCmts(self, gsp):
        while (gsp.ParsedInput[gsp.ParsedInputPtr].find(")") == -1):
            gsp.ParsedInputPtr += 1
    
    # ( -- list ) List compiler
    def compileList(self, gsp):
        gsp.CompiledList = []
        gsp.ParsedInputPtr += 1
        
        isFound = re.search(gsp.ParsedInput[gsp.ParsedInputPtr],'\}')
        while (isFound == None):
            gsp.CompiledList.append(gsp.ParsedInput[gsp.ParsedInputPtr])
            gsp.ParsedInputPtr += 1
            isFound = re.search(gsp.ParsedInput[gsp.ParsedInputPtr],'\}')

        joinedList = " ".join(gsp.CompiledList)
        gsp.DataStack.append(joinedList)
    
    # ( address -- ) Executes the word corresponding to the address on the stack
    def doExecute(self, gsp):
        address = int(gsp.DataStack.pop())
        gsp.ExecPtr = address
        gsp.cfb.Address[address].CodeField(gsp)

    # ( -- location ) Returns address of the next available dictionary location
    def doHere(self, gsp):
        hereLoc = len(gsp.cfb.Address) 
        gsp.DataStack.append(hereLoc)
    
    # Used internally by doCreate - is not compiled into the dictionary
    def doMyAddress(self, gsp):
        cw = gsp.cfb.Address[gsp.ExecPtr]
        gsp.DataStack.append(cw.IndexField)
    
    # CREATE <name>. Adds a named entry into the dictionary
    def doCreate(self, gsp):
        hereLoc = len(gsp.cfb.Address)
        name = gsp.ParsedInput[gsp.ParsedInputPtr + 1]
        params = []
        data = []
        help = "TODO: "
        cw = CreoleWord(name, gsp.cfb.Modules.Compiler.doMyAddress, "Compiler.doMyAddress", gsp.CurrentVocab,
        "COMPINPF", help, hereLoc - 1, hereLoc, hereLoc - 1, hereLoc, params, data)
        fqName = name + "." + gsp.CurrentVocab
        gsp.cfb.Dict[fqName] = cw
        gsp.cfb.Address.append(gsp.cfb.Dict[fqName])
        gsp.ParsedInputPtr += 2
        
    # ( -- ) Starts compilation of a colon definition
    def compileColon(self, gsp):
        hereLoc = len(gsp.cfb.Address)
        name = gsp.ParsedInput[gsp.ParsedInputPtr + 1]
        params = []
        data = []
        help = "TODO: "
        rawWord = None
        searchVocabPtr = None
        isFound = False
        compAction = None
        compInfo = None
        isSemiPresent = False
        colonIndex = -1
        gspComp = copy.deepcopy(gsp)
        i = 0
        codeField = None
        isSemiPresent = False
        fqName = name + "." + gsp.CurrentVocab
        # Elementary syntax check - if a colon isn't followed by a matching semicolon, you get an error message and the stacks and input are cleared.
        for i in range(0, len(gsp.ParsedInput)):
            if (gsp.ParsedInput[i] == "i"):
                colonIndex = i
            if (gsp.ParsedInput[i] == ";" and i > colonIndex):
                isSemiPresent = True
        if (isSemiPresent == False):
            print("Error: colon def must have matching semicolon")
            gsp.cleanFields()
            return

        # Compilation is started when the IMMEDIATE vocabulary is pushed onto the vocabulary stack. No need for the usual Forth STATE flag.
        gsp.VocabStack.append(gsp.BFC.ImmediateVocab)       
        cw = CreoleWord(name, gsp.cfb.Modules.Interpreter.doColon, "Interpreter.doColon", gsp.CurrentVocab, "COMPINPF", help, 
        hereLoc - 1, hereLoc, hereLoc - 1, hereLoc, params, data)
        # The smudge flag avoids accidental recursion. But it's easy enough to get around if you want to. 
        fqNameSmudged = name + "." + gsp.CurrentVocab + "." + gsp.BFC.SmudgeFlag
        gsp.cfb.Dict[fqNameSmudged] = cw
        gsp.cfb.Address.append(gsp.cfb.Dict[fqNameSmudged]) 
        
        gsp.ParsedInputPtr += 2
        # Parameter field contents are set up in the PAD area. Each word is looked up one at a time in the dictionary, and its name, address, and
        # compilation action are placed in the CompileInfo triplet.
        while (gsp.ParsedInputPtr < len(gsp.ParsedInput) and gsp.VocabStack[len(gsp.VocabStack) - 1] == gsp.BFC.ImmediateVocab and gsp.ParsedInput[gsp.ParsedInputPtr] != ";"):
            rawWord = gsp.ParsedInput[gsp.ParsedInputPtr]
            searchVocabPtr = len(gsp.VocabStack) - 1     
            isFound = False
            while (searchVocabPtr >= 0):
                fqWord = rawWord.upper() + "." + gsp.VocabStack[searchVocabPtr]
                if (fqWord in gsp.cfb.Dict):
                    compAction = gsp.cfb.Dict[fqWord].CompileActionField
                    if (compAction != gsp.BFC.ExecZeroAction):
                        compInfo = CompileInfo(fqWord, gsp.cfb.Dict[fqWord].IndexField, compAction)
                        gsp.PADarea.append(compInfo)
                    else:
                        # This is stuff where the outer ptr is manipulated such as comments
                        codeField = gsp.cfb.Dict[fqWord].CodeField
                        codeField(gsp)
                    isFound = True
                    break
                else:
                    searchVocabPtr -= 1

            # If no dictionary entry is found, it's tagged as a literal.
            if (isFound == False):
                compInfo = CompileInfo(rawWord, rawWord, gsp.BFC.CompLitAction)
                gsp.PADarea.append(compInfo)
            gsp.ParsedInputPtr += 1
        
        # 1. Builds the definition in the parameter field from the PAD area. Very simple; the address of each word appears before its associated
        #    compilation action. Most of the time, it will be COMPINPF, which will simply compile the word into the parameter field (it's actually
        #    , (comma) with a different name for readability purposes).
        #    Compiling words such as CompileIf will execute since that's the compilation action they're tagged with.
        # 2. Attaches it to the smudged definition.
        # 3. "Unsmudges" the new definition by copying it to its proper fully-qualified property and places it in the Address array.
        # 4. Deletes the smudged definition.
        # 5. Pops the IMMEDIATE vocabulary off the vocabulary stack and halts compilation. 
        
        i = 0
        gspComp.VocabStack = gsp.VocabStack
        gspComp.cfb.Address.append(gsp.cfb.Dict[fqNameSmudged]) 
        
        # Putting the args and compilation actions together then executing them seems to cause a problem with compiling words.
        # Getting around this by putting one arg on the stack, one in the input area, then executing. 
        while (i < len(gsp.PADarea)):
            compInfo = gsp.PADarea[i]
            gspComp.DataStack.append(compInfo.Address)
            gspComp.InputArea = compInfo.CompileAction
            gspComp.cfb.Modules.Interpreter.doParseInput(gspComp)
            gspComp.cfb.Modules.Interpreter.doOuter(gspComp)
            i += 1
        
        gspComp.InputArea = ";"
        gspComp.cfb.Modules.Interpreter.doParseInput(gspComp)
        gspComp.cfb.Modules.Interpreter.doOuter(gspComp)
        
        cw = gspComp.cfb.Address[hereLoc]
        cw.ParamFieldStart = 0
        gsp.cfb.Dict[fqName] = cw

        # remove the smudged dictionary entry
        gsp.cfb.Dict.pop(fqNameSmudged)

    # ( -- ) Terminates compilation of a colon definition
    def doSemi(self, gsp):
        gsp.PADarea = []
        gsp.VocabStack.pop()
        # print("Compilation is complete")
    
    # ( -- ) Compiles doLit and a literal into the dictionary
    def compileLiteral(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        doLitAddr = gsp.cfb.Dict["doLiteral.IMMEDIATE"].IndexField
        litVal = gsp.DataStack.pop()
        newCreoleWord.ParamField.append(doLitAddr)

        numberSet = re.findall(r"[-+]?\d*\.\d+|\d+", litVal)
        if (len(numberSet) > 0):
            litValNum = float(litVal)
            if (litValNum == int(litValNum)):
                newCreoleWord.ParamField.append(int(litValNum))
            else:
                newCreoleWord.ParamField.append(litValNum)
        else:
            newCreoleWord.ParamField.append(litVal)
        gsp.ParamFieldPtr = len(newCreoleWord.ParamField) - 1
    
        # ( -- lit ) Run-time code that pushes a literal onto the stack
    def doLiteral(self, gsp):
        rLoc = gsp.ReturnStack.pop()
        paramField = rLoc.CurrWord.ParamField
        litVal = paramField[rLoc.ParamFieldAddr]
        gsp.DataStack.append(litVal)
        rLoc.ParamFieldAddr += 1
        gsp.ReturnStack.append(rLoc)

    # ( addr -- val ) Fetches the value in the param field  at addr
    def doFetch(self, gsp):
        address = gsp.DataStack.pop()
        if (len(gsp.cfb.Address[address].ParamField) > 0):
            storedVal = gsp.cfb.Address[address].ParamField[0]
        if (len(gsp.cfb.Address[address].DataField) > 0):
            storedVal = gsp.cfb.Address[address].DataField[0]
        gsp.DataStack.append(storedVal)

    # ( val addr --) Stores the value in the param field  at addr"
    def doStore(self, gsp):
        address = gsp.DataStack.pop()
        valToStore = gsp.DataStack.pop()
        numberSet = re.findall(r"[-+]?\d*\.\d+|\d+",valToStore)
        if (len(numberSet) > 0):
            valRes1 = float(valToStore)
            if (valRes1 == int(valRes1)):
                gsp.cfb.Address[address].ParamField.append(int(valRes1))
            else:
                gsp.cfb.Address[address].ParamField.append(valRes1)
        else:
            gsp.cfb.Address[address].DataField.append(valToStore)
    
    # (  -- ) Sets the current (compilation) vocabulary to the context vocabulary (the one on top of the vocabulary stack)
    def doSetCurrentToContext(self, gsp):
        currentVocab = gsp.VocabStack[len(gsp.VocabStack) - 1]
        gsp.CurrentVocab = currentVocab
        print("Current vocab is now " + gsp.CurrentVocab)

    # ( -- ) Flags a word as immediate (so it executes instead of compiling inside a colon definition)
    def doImmediate(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        fqName = newCreoleWord.fqNameField
        newCreoleWord.CompileAction = "EXECUTE"
        newCreoleWord.Vocabulary = "IMMEDIATE"
        gsp.cfb.Address[newRow] = newCreoleWord
        gsp.cfb[fqName] = newCreoleWord

    # ( -- location ) Compile-time code for IF
    def compileIf(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        zeroBranchAddr = gsp.cfb.Dict["0BRANCH.IMMEDIATE"].IndexField
        newCreoleWord.ParamField.append(zeroBranchAddr)
        newCreoleWord.ParamField.append(-1)
        gsp.ParamFieldPtr = len(newCreoleWord.ParamField) - 1
        gsp.DataStack.append(gsp.ParamFieldPtr)
    
    # ( -- location ) Compile-time code for ELSE
    def compileElse(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        jumpAddr = gsp.cfb.Dict["JUMP.IMMEDIATE"].IndexField
        elseAddr = gsp.cfb.Dict["doElse.IMMEDIATE"].IndexField
        newCreoleWord.ParamField.append(jumpAddr)
        newCreoleWord.ParamField.append(-1)
        jumpAddrPFLoc = len(newCreoleWord.ParamField) - 1
        newCreoleWord.ParamField.append(elseAddr)
        zeroBrAddrPFLoc = gsp.DataStack.pop()
        newCreoleWord.ParamField[zeroBrAddrPFLoc] = len(newCreoleWord.ParamField) - 1
        gsp.DataStack.append(jumpAddrPFLoc)
        gsp.ParamFieldPtr = len(newCreoleWord.ParamField) - 1

    # ( -- location ) Compile-time code for THEN
    def compileThen(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        branchPFLoc = gsp.DataStack.pop()
        thenAddr = gsp.cfb.Dict["doThen.IMMEDIATE"].IndexField
        newCreoleWord.ParamField.append(thenAddr)
        newCreoleWord.ParamField[branchPFLoc] = len(newCreoleWord.ParamField) - 1

    # ( flag -- ) Run-time code for IF
    def do0Branch(self, gsp):
        currWord = gsp.cfb.Address[gsp.ExecPtr]
        paramField = currWord.ParamField
        rLoc = gsp.ReturnStack.pop()
        jumpAddr = paramField[rLoc.ParamFieldAddr]
        branchFlag = int(gsp.DataStack.pop())
        if (branchFlag == 0):
            gsp.ParamFieldPtr = jumpAddr
        else:
            gsp.ParamFieldPtr += 1
        rLoc.ParamFieldAddr = gsp.ParamFieldPtr
        gsp.ReturnStack.append(rLoc)
    
    # ( -- beginLoc ) Compile-time code for BEGIN
    def compileBegin(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        beginAddr = gsp.cfb.Dict["doBegin.IMMEDIATE"].IndexField
        newCreoleWord.ParamField.append(beginAddr)
        beginLoc = len(newCreoleWord.ParamField) - 1
        gsp.DataStack.append(beginLoc)
    
    # ( beginLoc -- ) Compile-time code for UNTIL
    def compileUntil(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        beginLoc = gsp.DataStack.pop()
        zeroBranchAddr = gsp.cfb.Dict["0BRANCH.IMMEDIATE"].IndexField
        newCreoleWord.ParamField.append(zeroBranchAddr)
        newCreoleWord.ParamField.append(beginLoc)
    
    # ( -- beginLoc ) Compile-time code for DO
    def compileDo(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        doStartDoAddr = gsp.cfb.Dict["doStartDo.IMMEDIATE"].IndexField
        doAddr = gsp.cfb.Dict["doDo.IMMEDIATE"].IndexField
        newCreoleWord.ParamField.append(doStartDoAddr)
        newCreoleWord.ParamField.append(doAddr)
        doLoc = len(newCreoleWord.ParamField) - 1
        gsp.DataStack.append(doLoc)

    # ( -- beginLoc ) Compile-time code for LOOP
    def compileLoop(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        loopAddr = gsp.cfb.Dict["doLoop.IMMEDIATE"].IndexField
        doLoc = gsp.DataStack.pop()
        newCreoleWord.ParamField.append(loopAddr)
        newCreoleWord.ParamField.append(doLoc)

    # ( -- beginLoc ) Compile-time code for +LOOP
    def compilePlusLoop(self, gsp):
        newRow = len(gsp.cfb.Address) - 1
        newCreoleWord = gsp.cfb.Address[newRow]
        loopAddr = gsp.cfb.Dict["doPlusLoop.IMMEDIATE"].IndexField
        doLoc = gsp.DataStack.pop()
        newCreoleWord.ParamField.append(loopAddr)
        newCreoleWord.ParamField.append(doLoc)

    # ( start end -- ) Starts off the Do by getting the start and end
    def doStartDo(self, gsp):
        rLoc = gsp.ReturnStack.pop()
        startIndex = gsp.DataStack.pop()
        loopEnd = gsp.DataStack.pop()
        li = LoopInfo(gsp.loopLabels[gsp.LoopLabelPtr], startIndex, loopEnd)
        gsp.LoopCurrIndexes = [0, 0, 0]
        gsp.LoopLabelPtr += 1
        gsp.ReturnStack.append(li)
        gsp.ReturnStack.append(rLoc)

    #  ( inc -- ) Loops back to doDo until the start >= the end and increments with inc
    def doPlusLoop(self, gsp):
        incVal = int(gsp.DataStack.pop())
        currWord = gsp.cfb.Address[gsp.ExecPtr]
        paramField = currWord.ParamField
        rLoc = gsp.ReturnStack.pop()
        li = gsp.ReturnStack.pop()
        jumpAddr = paramField[rLoc.ParamFieldAddr]
        loopLimit = int(li.Limit)
        loopLabel = li.Label
        currIndex = int(li.Index)
        if (incVal < 0):
            loopLimit += incVal
        else:
            loopLimit -= incVal
        if ( ( (incVal > 0) and currIndex >= loopLimit) or ( (incVal < 0) and currIndex <= loopLimit)):
            gsp.ParamFieldPtr += 1
            rLoc.ParamFieldAddr = gsp.ParamFieldPtr
            gsp.LoopLabelPtr -= 1
        else:
            gsp.ParamFieldPtr = jumpAddr
            currIndex = currIndex + incVal
            li.Index = currIndex
            rLoc.ParamFieldAddr = gsp.ParamFieldPtr
            gsp.ReturnStack.append(li)
        if   (loopLabel == "I"):
            gsp.LoopCurrIndexes[0] = currIndex
        elif (loopLabel == "J"):
            gsp.LoopCurrIndexes[1] = currIndex
        elif (loopLabel == "K"):
            gsp.LoopCurrIndexes[2] = currIndex
        else:
            print("Error: invalid loop label")
        gsp.ReturnStack.append(rLoc)
    
    # doLoop is treated as a special case of doPlusLoop
    # ( -- ) Loops back to doDo until the start equals the end
    def doLoop(self, gsp):
        gsp.DataStack.append(1)
        codeField = gsp.cfb.Dict["doPlusLoop.IMMEDIATE"].CodeField
        codeField(gsp)

    # ( -- index ) Returns the index of I
    def doIndexI(self, gsp):
        gsp.DataStack.append(gsp.LoopCurrIndexes[0])

    # ( -- index ) Returns the index of J
    def doIndexJ(self, gsp):
        gsp.DataStack.append(gsp.LoopCurrIndexes[1])
    
    # ( -- index ) Returns the index of K
    def doIndexK(self, gsp):
        gsp.DataStack.append(gsp.LoopCurrIndexes[2])
    
    # ( address -- ) Run-time code for DOES>
    def doDoes(self, gsp):
        gsp.DataStack.append(gsp.CurrWord.IndexField)
        gsp.cfb.Modules.Interpreter.doColon(gsp)
   
    # DOES> <list of runtime actions>. When defining word is created, copies code following it into the child definition
    def compileDoes(self, gsp):
        rLoc = gsp.ReturnStack.pop()
        parentRow = rLoc.CurrWord.IndexField
        newRow = len(gsp.cfb.Address) - 1
        parentCreoleWord = gsp.cfb.Address[parentRow]
        childCreoleWord = gsp.cfb.Address[newRow]
        fqNameField = childCreoleWord.fqNameField
        doesAddr = gsp.cfb.Dict["DOES>.FORTH"].IndexField
        i = 0
        childCreoleWord.CodeField = gsp.cfb.Modules.Compiler.doDoes
        childCreoleWord.CodeFieldStr = "Compiler.doDoes"
        # Find the location of the does address in the parent definition
        while (i < len(parentCreoleWord.ParamField)):
            if (parentCreoleWord.ParamField[i] == doesAddr):
                startCopyPoint = i + 1
                break
            else:
                i += 1
        
        # Need the definition's address do doDoes can get it easily either when it's being
        # called from the interpreter from from within a compiled definition
        childCreoleWord.ParamField.append(newRow)
        childCreoleWord.ParamFieldStart = len(childCreoleWord.ParamField)
        i = 0
        while (startCopyPoint < len(parentCreoleWord.ParamField)):
            childCreoleWord.ParamField.append(parentCreoleWord.ParamField[startCopyPoint])
            startCopyPoint += 1
            i += 1
        
        rLoc.ParamFieldAddr += i
        gsp.ReturnStack.append(rLoc)
        gsp.cfb.Address[newRow] = childCreoleWord
        gsp.cfb.Dict[fqNameField] = childCreoleWord

     # ( -- ) Jumps unconditionally to the parameter field location next to it and is compiled by ELSE   
    def doJump(self, gsp):
        currWord = gsp.cfb.Address[gsp.ExecPtr]
        paramField = currWord.ParamField
        jumpAddr = paramField[gsp.ParamFieldPtr + 1]
        rLoc = gsp.ReturnStack.pop()
        gsp.ParamFieldPtr = jumpAddr
        rLoc.ParamFieldAddr = gsp.ParamFieldPtr
        gsp.ReturnStack.append(rLoc)
    
class LogicOps:
    def __init__(self):
        self.Title = "Logical operatives grouping"
    
    # ( val1 val2 -- flag ) -1 if equal, 0 otherwise
    def doEquals(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if (val1 == val2):
            gsp.DataStack.append(-1)
        else:
             gsp.DataStack.append(0)
    
    # ( val1 val2 -- flag ) 0 if equal, -1 otherwise
    def doNotEquals(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if (val1 == val2):
            gsp.DataStack.append(0)
        else:
             gsp.DataStack.append(-1)
    
    # ( val1 val2 -- flag ) -1 if less than, 0 otherwise"
    def doLessThan(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if (val2 < val1):
            gsp.DataStack.append(-1)
        else:
             gsp.DataStack.append(0)
    
    # ( val1 val2 -- flag ) -1 if greater than, 0 otherwise
    def doGreaterThan(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if (val2 > val1):
            gsp.DataStack.append(-1)
        else:
             gsp.DataStack.append(0)
    
    # ( val1 val2 -- flag ) -1 if less than or equal to, 0 otherwise
    def doLessThanOrEquals(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if (val2 <= val1):
            gsp.DataStack.append(-1)
        else:
             gsp.DataStack.append(0)
    
    # ( val1 val2 -- flag ) -1 if greater than or equal to, 0 otherwise
    def doGreaterThanOrEquals(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if (val2 >= val1):
            gsp.DataStack.append(-1)
        else:
             gsp.DataStack.append(0)
    
    # ( val -- opval ) -1 if 0, 0 otherwise
    def doNot(self, gsp):
        val = gsp.DataStack.pop()
        if int(val) == 0:
            gsp.DataStack.append(-1)
        else:
            gsp.DataStack.append(0)
    
    # ( val1 val2 -- flag ) -1 if both arguments are non-zero, 0 otherwise
    def doAnd(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if int(val1) != 0 and int(val2) != 0:
            gsp.DataStack.append(-1)
        else:
            gsp.DataStack.append(0)
    
    # ( val1 val2 -- flag ) -1 if one or both arguments are non-zero, 0 otherwise
    def doOr(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        if int(val1) != 0 or int(val2) != 0:
            gsp.DataStack.append(-1)
        else:
            gsp.DataStack.append(0)

    # ( val1 val2 -- flag ) -1 if one and only one argument is non-zero, 0 otherwise
    def doXor(self, gsp):
        val1 = gsp.DataStack.pop()
        val2 = gsp.DataStack.pop()
        #     if (int(val1) != 0 or int(val2) != 0) and not (int(val1) == 0 and int(val2) == 0):
        #        gsp.DataStack.append(-1)
        #else:
        #    gsp.DataStack.append(0)

from AppSpec import *
   
class CreoleWord:
    def __init__(self, NameField, CodeField, CodeFieldStr, Vocabulary, CompileActionField, HelpField,PrevRowLocField, RowLocField, LinkField, IndexField, ParamField, DataField):
        self.NameField = NameField
        self.CodeField = CodeField
        self.CodeFieldStr = CodeFieldStr
        self.Vocabulary = Vocabulary
        self.fqNameField = NameField + "." + Vocabulary
        self.CompileActionField = CompileActionField
        self.HelpField = HelpField
        self.PrevRowLocField = PrevRowLocField
        self.RowLocField = RowLocField
        self.LinkField = LinkField
        self.IndexField = IndexField
        self.ParamField = ParamField
        self.DataField = DataField
        self.ParamFieldStart = 0
        self.ParamFieldStartFrom = 0

def buildPrimitive(self, name, cf, cfs, vocab, compAction, help):
    params = []
    data = []
    cw = CreoleWord(name, cf, cfs, vocab, compAction, help, len(self.Address) - 1, 
    len(self.Address) , len(self.Address) -1, len(self.Address), params, data)
    fqName = name + "." + vocab
    self.Dict[fqName] = cw
    self.Address.append(cw)

def buildHighLevel(self, gsp, code, help):
    gsp.InputArea = code
    # This could be done in compileColon, but choose to do it here. 
    gsp.PADarea = []
    self.Modules.Interpreter.doParseInput(gsp)
    self.Modules.Interpreter.doOuter(gsp)
    self.Address[len(self.Address) - 1].HelpField = help
    newDef = self.Address[len(self.Address) - 1]
    self.Dict[newDef.fqNameField] = newDef

CreoleForthBundle.buildPrimitive = buildPrimitive
CreoleForthBundle.buildHighLevel = buildHighLevel

coreprims = CorePrims()
interpreter = Interpreter()
compiler = Compiler()
logicops = LogicOps()
appspec = AppSpec()
modules = Modules(coreprims, interpreter, compiler, logicops, appspec)
cfb1 = CreoleForthBundle()
cfb1.Modules = modules
gsp = GlobalSimpleProps(cfb1)
gsp.VocabStack.append("ONLY")
gsp.VocabStack.append("FORTH")
gsp.VocabStack.append("APPSPEC")
gsp.CurrentVocab = "FORTH"
gsp.cfb = cfb1

# The onlies
cfb1.buildPrimitive("ONLY", cfb1.Modules.Interpreter.doOnly, "Interpreter.doOnly", "ONLY", "EXECUTE","( -- ) Empties the vocabulary stack, then puts ONLY on it")
cfb1.buildPrimitive("FORTH", cfb1.Modules.Interpreter.doForth, "Interpreter.doForth", "ONLY", "EXECUTE","( -- ) Puts FORTH on the vocabulary stack")
cfb1.buildPrimitive("APPSPEC", cfb1.Modules.Interpreter.doAppSpec, "Interpreter.doAppSpec", "ONLY", "EXECUTE","( -- ) Puts APPSPEC on the vocabulary stack")
cfb1.buildPrimitive("NOP", cfb1.Modules.CorePrims.doNOP, "CorePrims.doNOP", "ONLY", "COMPINPF","( -- ) Do-nothing primitive which is surprisingly useful")
cfb1.buildPrimitive("__#EOL#__", cfb1.Modules.CorePrims.doNOP, "CorePrims.doNOP", "ONLY", "NOP","( -- ) EOL marker")

# dialogs and help
cfb1.buildPrimitive("HELLO", cfb1.Modules.CorePrims.doHello, "CorePrims.doHello", "FORTH", "COMPINPF","( -- ) prints out Hello World")
cfb1.buildPrimitive("TULIP", cfb1.Modules.CorePrims.doTulip, "CorePrims.doTulip", "FORTH", "COMPINPF","( -- ) Either prints Tulip or pops up a message")
cfb1.buildPrimitive("MSGBOX", cfb1.Modules.CorePrims.doMsgBox, "CorePrims.doMsgBox", "FORTH", "COMPINPF","( msg -- ) Pops up an alert saying the message")

cfb1.buildPrimitive("EVAL", cfb1.Modules.CorePrims.doEval, "CorePrims.doEval", "FORTH", "COMPINPF","( code -- ) Evaluates raw JavaScript code - only allows alerts")
cfb1.buildPrimitive("VLIST", cfb1.Modules.CorePrims.doVList, "CorePrims.doVList", "FORTH", "COMPINPF","( -- ) Lists the dictionary definitions")

# Basic math
cfb1.buildPrimitive("+", cfb1.Modules.CorePrims.doPlus, "CorePrims.doPlus", "FORTH", "COMPINPF","( n1 n2 -- sum ) Adds two numbers on the stack")
cfb1.buildPrimitive("-", cfb1.Modules.CorePrims.doMinus, "CorePrims.doMinus", "FORTH", "COMPINPF","( n1 n2 -- difference ) Subtracts two numbers on the stack")
cfb1.buildPrimitive("*", cfb1.Modules.CorePrims.doMultiply, "CorePrims.doMultiply", "FORTH", "COMPINPF","( n1 n2 -- product ) Multiplies two numbers on the stack")
cfb1.buildPrimitive("/", cfb1.Modules.CorePrims.doDivide, "CorePrims.doDivide", "FORTH", "COMPINPF","( n1 n2 -- quotient ) Divides two numbers on the stack")
cfb1.buildPrimitive("%", cfb1.Modules.CorePrims.doMod, "CorePrims.doMod", "FORTH", "COMPINPF","( n1 n2 -- remainder ) Returns remainder of division operation")

# Date/time handling
cfb1.buildPrimitive("TODAY", cfb1.Modules.CorePrims.doToday, "CorePrims.doToday", "FORTH", "COMPINPF","( -- ) Pops up today's date")
cfb1.buildPrimitive("NOW", cfb1.Modules.CorePrims.doNow, "CorePrims.doNow", "FORTH", "COMPINPF","( --  time ) Puts the time on the stack")
cfb1.buildPrimitive(">HHMMSS", cfb1.Modules.CorePrims.doToHoursMinSecs, "CorePrims.doToHoursMinSecs", "FORTH", "COMPINPF","( time -- ) Formats the time")

# Stack manipulation
cfb1.buildPrimitive("DUP", cfb1.Modules.CorePrims.doDup, "CorePrims.doDup", "FORTH", "COMPINPF","( val --  val val ) Duplicates the argument on top of the stack")
cfb1.buildPrimitive("SWAP", cfb1.Modules.CorePrims.doSwap, "CorePrims.doSwap", "FORTH", "COMPINPF","( val1 val2 -- val2 val1 ) Swaps the positions of the top two stack arguments")
cfb1.buildPrimitive("ROT", cfb1.Modules.CorePrims.doRot, "CorePrims.doRot", "FORTH", "COMPINPF","( val1 val2 val3 -- val2 val3 val1 ) Moves the third stack argument to the top")
cfb1.buildPrimitive("-ROT", cfb1.Modules.CorePrims.doMinusRot, "CorePrims.doMinusRot", "FORTH", "COMPINPF","( val1 val2 val3 -- val3 val1 val2 ) Moves the top stack argument to the third position")
cfb1.buildPrimitive("NIP", cfb1.Modules.CorePrims.doNip, "CorePrims.doNip", "FORTH", "COMPINPF","( val1 val2 -- val2 ) Removes second stack argument")
cfb1.buildPrimitive("TUCK", cfb1.Modules.CorePrims.doTuck, "CorePrims.doTuck", "FORTH", "COMPINPF","( val1 val2 -- val2 val1 val2 ) Copies top stack argument under second argument")
cfb1.buildPrimitive("OVER", cfb1.Modules.CorePrims.doOver, "CorePrims.doOver", "FORTH", "COMPINPF","( val1 val2 -- val1 val2 val1 ) Copies second stack argument to the top of the stack")
cfb1.buildPrimitive("DROP", cfb1.Modules.CorePrims.doDrop, "CorePrims.doDrop", "FORTH", "COMPINPF","( val -- ) Drops the argument at the top of the stack")
cfb1.buildPrimitive(".", cfb1.Modules.CorePrims.doDot, "CorePrims.doDot", "FORTH", "COMPINPF","( val -- ) Prints the argument at the top of the stack")
cfb1.buildPrimitive("DEPTH", cfb1.Modules.CorePrims.doDepth, "CorePrims.doDepth", "FORTH", "COMPINPF","( -- n ) Returns the stack depth")

# Logical operatives
cfb1.buildPrimitive("=", cfb1.Modules.LogicOps.doEquals, "LogicOps.doEquals", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if equal, 0 otherwise")
cfb1.buildPrimitive("<>", cfb1.Modules.LogicOps.doNotEquals, "LogicOps.doNotEquals", "FORTH", "COMPINPF","( val1 val2 -- flag ) 0 if equal, -1 otherwise")
cfb1.buildPrimitive("<", cfb1.Modules.LogicOps.doLessThan, "LogicOps.doLessThan", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if less than, 0 otherwise")
cfb1.buildPrimitive(">", cfb1.Modules.LogicOps.doGreaterThan, "LogicOps.doGreaterThan", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if greater than, 0 otherwise")
cfb1.buildPrimitive("<=", cfb1.Modules.LogicOps.doLessThanOrEquals, "LogicOps.doLessThanOrEquals", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if less than or equal to, 0 otherwise")
cfb1.buildPrimitive(">=", cfb1.Modules.LogicOps.doGreaterThanOrEquals, "LogicOps.doGreaterThanOrEquals", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if greater than or equal to, 0 otherwise")
cfb1.buildPrimitive("NOT", cfb1.Modules.LogicOps.doNot, "LogicOps.doNot", "FORTH", "COMPINPF","( val -- opval ) -1 if 0, 0 otherwise")
cfb1.buildPrimitive("AND", cfb1.Modules.LogicOps.doAnd, "LogicOps.doAnd", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if both arguments are non-zero, 0 otherwise")
cfb1.buildPrimitive("OR", cfb1.Modules.LogicOps.doOr, "LogicOps.doOr", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if one or both arguments are non-zero, 0 otherwise")
cfb1.buildPrimitive("XOR", cfb1.Modules.LogicOps.doXor, "LogicOps.doXor", "FORTH", "COMPINPF","( val1 val2 -- flag ) -1 if one and only one argument is non-zero, 0 otherwise")

# Compiler definitions
cfb1.buildPrimitive(",", cfb1.Modules.Compiler.doComma, "Compiler.doComma", "FORTH", "COMPINPF","( n --) Compiles value off the TOS into the next parameter field cell")
cfb1.buildPrimitive("COMPINPF", cfb1.Modules.Compiler.doComma, "Compiler.doComma", "IMMEDIATE", "COMPINPF","( n --) Does the same thing as , (comma) - given a different name for ease of reading")
cfb1.buildPrimitive("EXECUTE", cfb1.Modules.Compiler.doExecute, "Compiler.doExecute", "FORTH", "COMPINPF","( address --) Executes the word corresponding to the address on the stack")
cfb1.buildPrimitive(":", cfb1.Modules.Compiler.compileColon, "Compiler.compileColon", "FORTH", "COMPINPF","( -- ) Starts compilation of a colon definition")
cfb1.buildPrimitive(";", cfb1.Modules.Compiler.doSemi, "Compiler.doSemi", "IMMEDIATE", "EXECUTE","( -- ) Terminates compilation of a colon definition")
cfb1.buildPrimitive("COMPLIT", cfb1.Modules.Compiler.compileLiteral, "Compiler.compileLiteral", "IMMEDIATE", "EXECUTE","( -- ) Compiles doLit and a literal into the dictionary")
cfb1.buildPrimitive("doLiteral", cfb1.Modules.Compiler.doLiteral, "Compiler.doLiteral", "IMMEDIATE", "NOP","( -- lit ) Run-time code that pushes a literal onto the stack")
cfb1.buildPrimitive("HERE", cfb1.Modules.Compiler.doHere, "Compiler.doHere", "FORTH", "COMPINPF","( -- location ) Returns address of the next available dictionary location")
cfb1.buildPrimitive("CREATE", cfb1.Modules.Compiler.doCreate, "Compiler.doCreate", "FORTH", "COMPINPF","CREATE <name>. Adds a named entry into the dictionary")
cfb1.buildPrimitive("doDoes", cfb1.Modules.Compiler.doDoes, "Compiler.doDoes", "IMMEDIATE", "COMPINPF", "( address -- ) Run-time code for DOES>");
cfb1.buildPrimitive("DOES>", cfb1.Modules.Compiler.compileDoes, "Compiler.compileDoes", "FORTH", "COMPINPF", 
                    "DOES> <list of runtime actions>. When defining word is created, copies code following it into the child definition")
cfb1.buildPrimitive("@", cfb1.Modules.Compiler.doFetch, "Compiler.doFetch", "FORTH", "COMPINPF","( addr -- val ) Fetches the value in the param field  at addr")
cfb1.buildPrimitive("!", cfb1.Modules.Compiler.doStore, "Compiler.doStore", "FORTH", "COMPINPF","( val addr --) Stores the value in the param field  at addr")
cfb1.buildPrimitive("DEFINITIONS", cfb1.Modules.Compiler.doSetCurrentToContext, "Compiler.doSetCurrentToContext", "FORTH",
"COMPINPF","(  -- ). Sets the current (compilation) vocabulary to the context vocabulary (the one on top of the vocabulary stack)")
cfb1.buildPrimitive("IMMEDIATE", cfb1.Modules.Compiler.doImmediate, "Compiler.doImmediate", "FORTH", "COMPINPF","( -- ) Flags a word as immediate (so it executes instead of compiling inside a colon definition)")
# Branching compiler definitions
cfb1.buildPrimitive("IF", cfb1.Modules.Compiler.compileIf, "Compiler.compileIf", "IMMEDIATE", "EXECUTE","( -- location ) Compile-time code for IF")
cfb1.buildPrimitive("ELSE", cfb1.Modules.Compiler.compileElse, "Compiler.compileElse", "IMMEDIATE", "EXECUTE","( -- location ) Compile-time code for ELSE")
cfb1.buildPrimitive("THEN", cfb1.Modules.Compiler.compileThen, "Compiler.compileThen", "IMMEDIATE", "EXECUTE","( -- location ) Compile-time code for THEN")
cfb1.buildPrimitive("0BRANCH", cfb1.Modules.Compiler.do0Branch, "Compiler.do0Branch", "IMMEDIATE", "NOP","( flag -- ) Run-time code for IF")
cfb1.buildPrimitive("JUMP", cfb1.Modules.Compiler.doJump, "Compiler.doJump", "IMMEDIATE", "NOP", 
"( -- ) Jumps unconditionally to the parameter field location next to it and is compiled by ELSE")
cfb1.buildPrimitive("doElse", cfb1.Modules.CorePrims.doNOP, "CorePrims.doNOP", "IMMEDIATE", "NOP","( -- ) Run-time code for ELSE")
cfb1.buildPrimitive("doThen", cfb1.Modules.CorePrims.doNOP, "CorePrims.doNOP", "IMMEDIATE", "NOP","( -- ) Run-time code for THEN")
cfb1.buildPrimitive("BEGIN", cfb1.Modules.Compiler.compileBegin, "Compiler.CompileBegin", "IMMEDIATE", "EXECUTE","( -- beginLoc ) Compile-time code for BEGIN")
cfb1.buildPrimitive("UNTIL", cfb1.Modules.Compiler.compileUntil, "Compiler.CompileUntil", "IMMEDIATE", "EXECUTE","( beginLoc -- ) Compile-time code for UNTIL")
cfb1.buildPrimitive("doBegin", cfb1.Modules.CorePrims.doNOP, "CorePrims.doNOP", "IMMEDIATE", "NOP","( -- ) Run-time code for BEGIN")
cfb1.buildPrimitive("DO", cfb1.Modules.Compiler.compileDo, "Compiler.compileDo", "IMMEDIATE", "EXECUTE","( -- beginLoc ) Compile-time code for DO")
cfb1.buildPrimitive("LOOP", cfb1.Modules.Compiler.compileLoop, "Compiler.compileLoop", "IMMEDIATE", "EXECUTE","( -- beginLoc ) Compile-time code for LOOP")
cfb1.buildPrimitive("+LOOP", cfb1.Modules.Compiler.compilePlusLoop, "Compiler.compilePlusLoop", "IMMEDIATE", "EXECUTE","( -- beginLoc ) Compile-time code for +LOOP")
cfb1.buildPrimitive("doStartDo", cfb1.Modules.Compiler.doStartDo, "Compiler.doStartDo", "IMMEDIATE", "COMPINPF","( start end -- ) Starts off the Do by getting the start and end")
cfb1.buildPrimitive("doDo", cfb1.Modules.CorePrims.doNOP, "CorePrims.doNOP", "IMMEDIATE", "COMPINPF","( -- ) Marker for DoLoop to return to")
cfb1.buildPrimitive("doLoop", cfb1.Modules.Compiler.doLoop, "Compiler.doLoop", "IMMEDIATE", "COMPINPF","( -- ) Loops back to doDo until the start equals the end")
cfb1.buildPrimitive("doPlusLoop", cfb1.Modules.Compiler.doPlusLoop, "Compiler.doPlusLoop", "IMMEDIATE", "COMPINPF","( inc -- ) Loops back to doDo until the start >= the end and increments with inc")
cfb1.buildPrimitive("I", cfb1.Modules.Compiler.doIndexI, "Compiler.doIndexI", "FORTH", "COMPINPF","( -- index ) Returns the index of I")
cfb1.buildPrimitive("J", cfb1.Modules.Compiler.doIndexJ, "Compiler.doIndexJ", "FORTH", "COMPINPF","( -- index ) Returns the index of J")
cfb1.buildPrimitive("K", cfb1.Modules.Compiler.doIndexK, "Compiler.doIndexK", "FORTH", "COMPINPF","( -- index ) Returns the index of K")

# Commenting and list compiler
cfb1.buildPrimitive("//", cfb1.Modules.Compiler.doSingleLineCmts, "Compiler.doSingleLineCmts", "FORTH", gsp.BFC.ExecZeroAction,"( -- ) Single-line comment handling")
cfb1.buildPrimitive("(", cfb1.Modules.Compiler.doParenCmts, "Compiler.doParenCmts", "FORTH", gsp.BFC.ExecZeroAction,"( -- ) Multiline comment handling")
cfb1.buildPrimitive("{", cfb1.Modules.Compiler.compileList, "Compiler.compileList", "FORTH", gsp.BFC.ExecZeroAction,"( -- list ) List compiler")

# cfb1.buildHighLevel(gsp,": x  NOP ;", "Executing a colon")
cfb1.buildHighLevel(gsp,": HT IF HELLO ELSE TULIP THEN ;", "My first high-level definition")
cfb1.buildHighLevel(gsp,": HT2 NOP NOP NOP ;", "My second high-level definition")
cfb1.buildHighLevel(gsp,": TLIT 3 4 5 ;", "Testing literals")
cfb1.buildHighLevel(gsp,": TESTBU BEGIN 1 + DUP 10 TULIP > UNTIL . ;", "Testing BEGIN UNTIL")
cfb1.buildHighLevel(gsp,": TDL DO HELLO LOOP ;", "Testing DO LOOP")
cfb1.buildHighLevel(gsp,": CONSTANT CREATE , DOES> @ ;", "The quintessential defining word")
cfb1.buildHighLevel(gsp,": H3 HELLO HELLO HELLO ;", "3 hellos")

gsp.DataStack = []

#cp = CorePrims()
#interpreter = Interpreter()
gsp.CurrentVocab = "APPSPEC"
from AppSpecBuildDefs import *
