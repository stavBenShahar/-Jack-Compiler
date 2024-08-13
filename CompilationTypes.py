from collections import namedtuple

JackSymbol = namedtuple('Symbol', ['kind', 'type', 'id'])


class JackClass:

	def __init__(self, name):
		self.name = name
		self.symbols = dict()

		self.staticSymbols = 0
		self.fieldSymbols = 0

	def addField(self, name, varType):
		self.symbols[name] = JackSymbol('field', varType, self.fieldSymbols)
		self.fieldSymbols += 1

	def addStatic(self, name, varType):
		self.symbols[name] = JackSymbol('static', varType, self.staticSymbols)
		self.staticSymbols += 1

	def getSymbol(self, name):
		return self.symbols.get(name)


class JackSubroutine:

	def __init__(self, name, subroutineType, returnType, jackClass):
		self.name = name
		self.jackClass = jackClass
		self.subroutineType = subroutineType
		self.returnType = returnType

		self.symbols = dict()
		self.argSymbols = 0
		self.varSymbols = 0

		if subroutineType == 'method':
			self.addArg('this', self.jackClass.name)

	def addArg(self, name, varType):
		self.symbols[name] = JackSymbol('arg', varType, self.argSymbols)
		self.argSymbols += 1

	def addVar(self, name, varType):
		self.symbols[name] = JackSymbol('var', varType, self.varSymbols)
		self.varSymbols += 1

	def getSymbol(self, name):
		symbol = self.symbols.get(name)
		if symbol:
			return symbol

		return self.jackClass.getSymbol(name)
