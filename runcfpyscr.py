# Runs a Creole Forth for Python script
import sys
from CreoleForth import *

if len(sys.argv) != 2:
    print("Error: please enter exactly one input file name")
    sys.exit()
else: 
    f= open(sys.argv[1],"r")
    oneLine = f.read()
    all_lines = f.readlines()
    input = ""
    for line in all_lines:
        line += '\n'
        input += line
    f.close()
    # gsp.cleanFields()
    
    # gsp.PADarea = []
    gsp.InputArea = oneLine
    cfb1.Modules.Interpreter.doParseInput(gsp)
    cfb1.Modules.Interpreter.doOuter(gsp)


