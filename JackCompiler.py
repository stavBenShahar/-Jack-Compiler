import sys
import os
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine


def compileFile(fp):
    with open(fp, 'r') as inputFile:
        fileName = os.path.basename(fp)
        fpNoExt, _ = os.path.splitext(fp)
        fileNameNoExt, _ = os.path.splitext(fileName)

        outputFp = fpNoExt + '.vm'
        with open(outputFp, 'w') as outputFile:
            tokenizer = JackTokenizer(inputFile.read())
            compiler = CompilationEngine(tokenizer, outputFile)
            compiler.compileClass()


def compileDir(dirPath):
    for file in os.listdir(dirPath):
        fp = os.path.join(dirPath, file)
        _, fileExt = os.path.splitext(fp)
        if os.path.isfile(fp) and fileExt.lower() == '.jack':
            compileFile(fp)


def main():
    if len(sys.argv) < 2:
        print('USAGE: use JackCompiler <path>'.format(sys.argv[0]))
        sys.exit(1)

    inputPath = sys.argv[1]

    if os.path.isdir(inputPath):
        compileDir(inputPath)
    elif os.path.isfile(inputPath):
        compileFile(inputPath)
    else:
        print("ERROR: Invalid file or directory, compilation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
