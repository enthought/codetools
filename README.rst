============================================
codetools: code analysis and execution tools
============================================

The codetools project includes packages that simplify meta-programming
and help the programmer separate data from code in Python. This
library contains classes that allow defining simple snippets, or
"blocks", of Python code, analyze variable dependencies in the code
block, and use these dependencies to construct or restrict an
execution graph. These (restricted) code blocks can then be executed
in any namespace. However, this project also provides a
Traits-event-enhanced namespace, called a "context", which can be used
in place of a vanilla namespace to allow actions to be performed
whenever variables are assigned or retrieved from the namespace. This
project is used as the foundation for the BlockCanvas project.
