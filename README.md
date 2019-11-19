Creole Forth for Python
-----------------------

Intro
-----

This is a Forth-like scripting language built in Python 3 and is preceded by similar languages that were built in
Delphi/Lazarus, Excel VBA, and JavaScript.  It can be used either standalone or as a DSL embedded as part of a
larger application. 

Methodology
-----------
Primitives are defined as Python methods attached to objects. They are roughly analagous to core words defined 
in assembly language in some Forth compilers. They are then passed to the buildPrimitive method in the CreoleForthBundle 
class, which assigns them a name, vocabulary, and integer token value, which is used as an address. 

High-level or colon definitions are assemblages of primitives and previously defined high-level definitions.
They are defined by the colon compiler. 


Quick intro
-----------

1. Clone the cfpy project.

2. Navigate to the cfpy folder and run the following command: python runcfpyscr.py script1.f

3. A message saying "Hello World" should come up. 


Finding the contents of the dictionary
--------------------------------------
1. Run python runcfypscr.py script2.f. This will run the VLIST word.


Compiling and executing a high-level definition
-----------------------------------------------
1. Run python runcfypscr.py script3.f. This defines and executes the high-level definition TEST1.
   It uses IF-ELSE-THEN branching to either run the HELLO primitive or add and print the sum of 
   3 and 4. 

Application-specific definitions
--------------------------------
1. Define the primitives in AppSpec.py.
2. Build the primitives with the cfb1.buildPrimitive method.
3. Build high-level definitions with the cfb1.buildHighLevel method.
4. Run runcfypscr.py test.f to run the sample testing definition in the APPSPEC vocabulary. 
