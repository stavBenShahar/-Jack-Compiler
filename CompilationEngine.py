import VMWriter
import CompilationTypes

INDENT = 2
biOpActions = {'+': 'add',                      '-': 'sub',
               '*': 'call Math.multiply 2',     '/': 'call Math.divide 2',
               '&': 'and',                      '|': 'or',
               '<': 'lt',                       '>': 'gt',
               '=': 'eq'}

unaryOpActions = {'-': 'neg',                   '~': 'not',
                  '^': 'shiftleft',             '#': 'shiftright'}

labelCount = 0


class CompilationEngine:

    def __init__(self, tokenizer, oStream):
        self.tokenizer = tokenizer
        self.vmWriter = VMWriter.VMWriter(oStream)

    @staticmethod
    def getLabel():
        global labelCount

        label = 'L{}'.format(labelCount)
        labelCount += 1

        return label

    def compileClass(self):
        self.tokenizer.advance()  # class

        # class name
        className = self.tokenizer.advance().value
        jackClass = CompilationTypes.JackClass(className)

        self.tokenizer.advance()  # {

        self.compileClassVars(jackClass)
        self.compileClassSubroutines(jackClass)

        self.tokenizer.advance()  # }

    def compileClassVars(self, jackClass):
        token = self.tokenizer.curToken()
        while token and token.type == 'keyword' and token.value in ['static', 'field']:
            self.tokenizer.advance()

            isStatic = token.value == 'static'

            # var type
            varType = self.tokenizer.advance().value

            stillVars = True
            while stillVars:
                # var name
                varName = self.tokenizer.advance().value

                if isStatic:
                    jackClass.addStatic(varName, varType)
                else:
                    jackClass.addField(varName, varType)

                token = self.tokenizer.advance()
                stillVars = token == ('symbol', ',')

            # load next token, to check if another var declaration
            token = self.tokenizer.curToken()

    def compileClassSubroutines(self, jackClass):
        token = self.tokenizer.curToken()
        while token and token.type == 'keyword'\
                and token.value in ['constructor', 'function', 'method']:
            # Advance for same reason as in varDec
            subroutineType = self.tokenizer.advance().value
            # return type
            returnType = self.tokenizer.advance().value
            # name
            name = self.tokenizer.advance().value

            jackSubroutine = CompilationTypes.JackSubroutine(
                name, subroutineType, returnType, jackClass)

            self.tokenizer.advance()  # ( - open parameterList
            self.compileParameterList(jackSubroutine)
            self.tokenizer.advance()  # ) - close parameterList
            self.compileSubroutineBody(jackSubroutine)

            # load the next token to check 
            token = self.tokenizer.curToken()

    def compileParameterList(self, jackSubroutine):
        token = self.tokenizer.curToken()
        # Check if the next token is a valid variable type
        stillVars = token and token.type in ['keyword', 'identifier']
        while stillVars:
            # param type
            token = self.tokenizer.advance()  # Don't advance to avoid eating
            paramType = token.value
            # param name
            paramName = self.tokenizer.advance().value

            jackSubroutine.addArg(paramName, paramType)

            token = self.tokenizer.curToken()
            # If there are still vars
            if token == ('symbol', ','):
                self.tokenizer.advance()  # Throw the ',' away
                token = self.tokenizer.curToken()
                stillVars = token and token.type in ['keyword', 'identifier']
            else:
                stillVars = False

    def compileSubroutineBody(self, jackSubroutine):

        self.tokenizer.advance()  # {

        self.compileSubroutineVars(jackSubroutine)

        self.vmWriter.writeFunction(jackSubroutine)

        if jackSubroutine.subroutineType == 'constructor':
            fieldCount = jackSubroutine.jackClass.fieldSymbols
            self.vmWriter.writePush('constant', fieldCount)
            self.vmWriter.writeCall('Memory', 'alloc', 1)
            # Set 'this' in the function to allow it to return it
            self.vmWriter.writePop('pointer', 0)
        elif jackSubroutine.subroutineType == 'method':
            self.vmWriter.writePush('argument', 0)
            self.vmWriter.writePop('pointer', 0)

        self.compileStatements(jackSubroutine)

        self.tokenizer.advance()  # }

    def compileSubroutineVars(self, jackSubroutine):

        token = self.tokenizer.curToken()
        # Check that a variable declarations starts
        while token and token == ('keyword', 'var'):
            self.tokenizer.advance()
            # varType
            varType = self.tokenizer.advance().value
            # varName
            varName = self.tokenizer.advance().value

            jackSubroutine.addVar(varName, varType)

            # repeat as long as there are parameters, o.w eats the semicolon
            while self.tokenizer.advance().value == ',':
                # varName
                varName = self.tokenizer.advance().value
                jackSubroutine.addVar(varName, varType)

            token = self.tokenizer.curToken()

    def compileStatements(self, jackSubroutine):

        checkStatements = True
        while checkStatements:
            token = self.tokenizer.curToken()

            if token == ('keyword', 'if'):
                self.compileStatementIf(jackSubroutine)
            elif token == ('keyword', 'while'):
                self.compileStatementWhile(jackSubroutine)
            elif token == ('keyword', 'let'):
                self.compileStatementLet(jackSubroutine)
            elif token == ('keyword', 'do'):
                self.compileStatementDo(jackSubroutine)
            elif token == ('keyword', 'return'):
                self.compileStatementReturn(jackSubroutine)
            else:
                checkStatements = False

    def compileStatementIf(self, jackSubroutine):
        self.tokenizer.advance()  # if
        self.tokenizer.advance()  # (

        self.compileExpression(jackSubroutine)

        self.tokenizer.advance()  # )
        self.tokenizer.advance()  # {

        falseLabel = CompilationEngine.getLabel()
        endLabel = CompilationEngine.getLabel()

        self.vmWriter.writeIf(falseLabel)

        # Compile inner statements
        self.compileStatements(jackSubroutine)

        self.vmWriter.writeGoto(endLabel)
        self.vmWriter.writeLabel(falseLabel)

        self.tokenizer.advance()  # }

        token = self.tokenizer.curToken()
        if token == ('keyword', 'else'):
            self.tokenizer.advance()  # else
            self.tokenizer.advance()  # {

            # Compile inner statements
            self.compileStatements(jackSubroutine)

            self.tokenizer.advance()  # }

        self.vmWriter.writeLabel(endLabel)

    def compileStatementWhile(self, jackSubroutine):
        self.tokenizer.advance()  # while
        self.tokenizer.advance()  # (

        whileLabel = CompilationEngine.getLabel()
        falseLabel = CompilationEngine.getLabel()

        self.vmWriter.writeLabel(whileLabel)
        self.compileExpression(jackSubroutine)

        self.tokenizer.advance()  # )
        self.tokenizer.advance()  # {

        self.vmWriter.writeIf(falseLabel)

        # Compile inner statements
        self.compileStatements(jackSubroutine)

        self.vmWriter.writeGoto(whileLabel)
        self.vmWriter.writeLabel(falseLabel)

        self.tokenizer.advance()  # }

    def compileStatementLet(self, jackSubroutine):
        self.tokenizer.advance()  # let
        varName = self.tokenizer.advance().value  # var name
        jackSymbol = jackSubroutine.getSymbol(varName)

        isArray = self.tokenizer.curToken().value == '['
        if isArray:
            self.tokenizer.advance()  # [
            self.compileExpression(jackSubroutine)  # Index
            self.tokenizer.advance()  # ]
            self.tokenizer.advance()  # =
            # Add the base and index
            self.vmWriter.writePushSymbol(jackSymbol)
            self.vmWriter.write('add')
            # Base 'that' at base+index, stored in stack
            # to avoid the expression assigned changing pointer:1, we don't
            # pop it yet
            self.compileExpression(jackSubroutine)  # Expression to assign
            self.vmWriter.writePop('temp', 0)  # Store assigned value in temp
            self.vmWriter.writePop('pointer', 1)  # Restore destination
            self.vmWriter.writePush('temp', 0)  # Restore assigned value
            self.vmWriter.writePop('that', 0)  # Store in target
        else:
            self.tokenizer.advance()  # =
            self.compileExpression(jackSubroutine)  # Expression to assign
            self.vmWriter.writePopSymbol(jackSymbol)

        self.tokenizer.advance()  # ;

    def compileStatementDo(self, jackSubroutine):
        self.tokenizer.advance()  # do

        self.compileTerm(jackSubroutine)  # Do options are a subset of terms
        self.vmWriter.writePop('temp',
                               0)  # Pop to avoid filling the stack with garbage

        self.tokenizer.advance()  # ;

    def compileStatementReturn(self, jackSubroutine):
        self.tokenizer.advance()  # return

        # Check if an expression is given
        token = self.tokenizer.curToken()
        if token != ('symbol', ';'):
            self.compileExpression(jackSubroutine)
        else:
            self.vmWriter.writeInt(0)

        self.vmWriter.writeReturn()
        self.tokenizer.advance()  # ;

    def compileExpressionList(self, jackSubroutine):
        # Handle expression list, so long as there are expressions
        count = 0  # Count expressions
        token = self.tokenizer.curToken()
        while token != ('symbol', ')'):

            if token == ('symbol', ','):
                self.tokenizer.advance()

            count += 1
            self.compileExpression(jackSubroutine)
            token = self.tokenizer.curToken()

        return count

    def compileExpression(self, jackSubroutine):
        self.compileTerm(jackSubroutine)

        token = self.tokenizer.curToken()
        while token.value in '+-*/&|<>=':
            binaryOp = self.tokenizer.advance().value

            self.compileTerm(jackSubroutine)
            self.vmWriter.write(biOpActions[binaryOp])

            token = self.tokenizer.curToken()

    def compileTerm(self, jackSubroutine):

        token = self.tokenizer.advance()
        # In case of unary operator, compile the term after the operator
        if token.value in unaryOpActions:
            self.compileTerm(jackSubroutine)
            self.vmWriter.write(unaryOpActions[token.value])
        # In case of opening parenthesis for an expression
        elif token.value == '(':
            self.compileExpression(jackSubroutine)
            self.tokenizer.advance()  # )
        elif token.type == 'integerConstant':
            self.vmWriter.writeInt(token.value)
        elif token.type == 'stringConstant':
            self.vmWriter.writeStr(token.value)
        elif token.type == 'keyword':
            if token.value == 'this':
                self.vmWriter.writePush('pointer', 0)
            else:
                self.vmWriter.writeInt(0)  # null / false
                if token.value == 'true':
                    self.vmWriter.write('not')

        # In case of a function call or variable name
        elif token.type == 'identifier':
            # Save token value as symbol and function in case of both
            tokenValue = token.value
            tokenVar = jackSubroutine.getSymbol(tokenValue)

            token = self.tokenizer.curToken()
            if token.value == '[':  # Array
                self.tokenizer.advance()  # [
                self.compileExpression(jackSubroutine)
                self.vmWriter.writePushSymbol(tokenVar)
                self.vmWriter.write('add')
                # rebase 'that' to point to var+index
                self.vmWriter.writePop('pointer', 1)
                self.vmWriter.writePush('that', 0)
                self.tokenizer.advance()  # ]
            else:
                # Default class for function calls is this class
                funcName = tokenValue
                funcClass = jackSubroutine.jackClass.name
                # Used to mark whether to use the default call, a method one
                defaultCall = True
                argCount = 0

                if token.value == '.':
                    defaultCall = False
                    self.tokenizer.advance()  # .
                    # try to load the object of the method
                    funcObj = jackSubroutine.getSymbol(tokenValue)
                    funcName = self.tokenizer.advance().value  # function name
                    # If this is an object, call as method
                    if funcObj:
                        funcClass = tokenVar.type  # Use the class of the object
                        argCount = 1  # Add 'this' to args
                        self.vmWriter.writePushSymbol(
                            tokenVar)  # push "this"
                    else:
                        funcClass = tokenValue
                    token = self.tokenizer.curToken()

                # If in-fact a function call
                if token.value == '(':
                    if defaultCall:
                        # Default call is a method one, push this
                        argCount = 1
                        self.vmWriter.writePush('pointer', 0)

                    self.tokenizer.advance()  # (
                    argCount += self.compileExpressionList(jackSubroutine)
                    self.vmWriter.writeCall(funcClass, funcName, argCount)
                    self.tokenizer.advance()  # )
                # If a variable instead
                elif tokenVar:
                    self.vmWriter.writePushSymbol(tokenVar)
