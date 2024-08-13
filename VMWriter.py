kindToSegment = {'static': 'static',
                 'field': 'this',
                 'arg': 'argument',
                 'var': 'local'}


class VMWriter:

    def __init__(self, oStream):
        self.oStream = oStream
        self.labelCount = 0

    def writeIf(self, label):
        self.oStream.write(
            'not\n')  # Negate to jump if the conditions doesn't hold
        self.oStream.write('if-goto {}\n'.format(label))

    def writeGoto(self, label):
        self.oStream.write('goto {}\n'.format(label))

    def writeLabel(self, label):
        self.oStream.write('label {}\n'.format(label))

    def writeFunction(self, jackSubroutine):
        className = jackSubroutine.jackClass.name
        name = jackSubroutine.name
        localVars = jackSubroutine.varSymbols

        self.oStream.write('function {}.{} {}\n'.format(className, name, localVars))

    def writeReturn(self):
        self.oStream.write('return\n')

    def writeCall(self, className, funcName, argCount):
        self.oStream.write('call {0}.{1} {2}\n'.format(
            className, funcName, argCount))

    def writePopSymbol(self, jackSymbol):
        kind = jackSymbol.kind
        offset = jackSymbol.id  # the offset in the segment

        segment = kindToSegment[kind]
        self.writePop(segment, offset)

    def writePushSymbol(self, jackSymbol):
        kind = jackSymbol.kind
        offset = jackSymbol.id  # the offset in the segment

        segment = kindToSegment[kind]
        self.writePush(segment, offset)

    def writePop(self, segment, offset):
        self.oStream.write('pop {0} {1}\n'.format(segment, offset))

    def writePush(self, segment, offset):
        self.oStream.write('push {0} {1}\n'.format(segment, offset))

    def write(self, action):
        self.oStream.write('{}\n'.format(action))

    def writeInt(self, n):
        self.writePush('constant', n)

    def writeStr(self, s):
        s = s[1:-1]
        self.writeInt(len(s))
        self.writeCall('string', 'new', 1)
        for c in s:
            self.writeInt(ord(c))
            self.writeCall('string', 'appendChar', 2)
