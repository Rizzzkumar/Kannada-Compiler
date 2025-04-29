# Kannada-Compiler
A Kannada language based compiler designed and implemented that allows programming using Kannada language words transcribed in english as constructs and keywords, enabling users to write source code in their native language and compile it into intermediate or pseudo-code.

Architecture Flow: Source Code(Kannada) → Lexical Analyzer → Syntax Analyzer → Semantic Analyzer → IR Generator → Output

Main Algorithms and Routines:
Tokenization Algorithm: DFA-based pattern matcher for Kannada.
Parser Functions: Recursive routines to match production rules.
Semantic Checker: Ensures type safety, scope resolution.
IR Generator: Outputs structured intermediate code in a neutral syntax.
Emphasis: All algorithms are language-neutral, but adapted for Kannada inputs.

Data structures used: Symbol Tables, Token table, AST, TAC
