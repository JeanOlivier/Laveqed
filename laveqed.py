#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess, sys
from xml.dom import minidom



class laveqed():

    def __init__(self,equation='',name='laveqed', scale=4, cleanAfter=True, eqonly=False):
        self.preamble= '% Created by laveqed (%NOW%)\n'\
                       '\\documentclass{article}\n'\
                       '\\usepackage{amssymb,amsmath,xcolor}\n'\
                       '\\pagestyle{empty}\n'\
                       '\\begin{document}\n'\
                       '\\begin{align*}\n'
                       # We use %NOW% instead of {NOW} to avoid hassle with .format and latex
        self.equation=equation
        self.postamble = '\n'\
                         '\\end{align*}\n'\
                         '\\end{document}'
        self.name=name.replace('.svg','')
        self.scale=scale
        if type(cleanAfter)==type(''):
            self.cleanAfter=bool(int(cleanAfter))
        else:
            self.cleanAfter=bool(cleanAfter)
        self.eqonly=eqonly
        self._tags=['LatexPreamble','LatexEquation','LatexPostamble','svgScale']

   
    def makesvg(self):
        # Handling name/filename
        basename=self.name
        # Base command that generates a .dvi and converts it to svg with as scale factor
        command = 'latex -interaction=batchmode \
                   {basename}.tex\
                   && dvisvgm --exact -c {scale},{scale} -n {basename}.dvi'
        if self.cleanAfter: # Removes the files LaTeX spits out if cleanAfter is True
            command=command+'&& rm {basename}.aux {basename}.log {basename}.dvi {basename}.tex'
        # Puts real basename and scale values in the command
        composed_command=command.format(basename = basename, scale = self.scale)
        self._maketex() # Makes the tex file for compiling
        subprocess.call(composed_command,shell=True) # Executes the shell command
        self._commentSVG()  # Adds metadata to the svg so it can be loaded in the futre

    def loadsvg(self,filename):
        # Handling filename
        if not filename[-4:]=='.svg':
            filename=filename+'.svg'
        # Loads and parses the svg xml file
        xmlsvg=minidom.parse(filename)
        tmp=xmlsvg.getElementsByTagName('desc')[0].childNodes # List of child nodes of desc
        if self.eqonly:  # Only loads the equation, not the -ambles
            self.equation=tmp[1].firstChild.nodeValue
        else:       # Loads the whole LaTeX "document"
            self.preamble,self.equation,self.postamble,self.scale=[i.firstChild.nodeValue for i in tmp]
            self.scale=int(self.scale)
        self.name=filename.replace('.svg','') # No error? -> Update the name of the object


    def display(self):
        print(self._getTexCode())   # Print the whole LaTeX "document"

    def _maketex(self): # Generates the tex file to compile
        with open(self.name+'.tex','w') as f:
            f.write(self._getTexCode())

    def _commentSVG(self):  # Adds metadata to the svg so it can be loaded in the futre
        basename=self.name
        # Parsing
        svgname=basename+'.svg' # That's why we ensure there's no '.svg' in self.name
        xmlsvg=minidom.parse(svgname)   # Loads and parses the svg xml file
        svg=xmlsvg.documentElement  # Represent the svg Element in the xml code
        # Creating text nodes
        Nodes=[xmlsvg.createTextNode(i) for i in \
                [self.preamble.replace('%NOW%', Now()),self.equation,self.postamble,str(self.scale)]]
        # Creating elements
        descElement=xmlsvg.createElementNS(None,'desc')
        Elements=[xmlsvg.createElementNS(None,i) for i in self._tags]
        # Appending respective text node to each LaTeX element and the formers to desc
        for i,j in zip(Elements,Nodes):
            i.appendChild(j)
            descElement.appendChild(i)
        # Appending the completed desc element to the svg element
        svg.appendChild(descElement)
        # Writing the modified svg xml to file
        with open(svgname,'w') as f:
            xmlsvg.writexml(f)

    def _getTexCode(self):
        # Returns a single string with the whole LaTeX "document"
        tmp=(self.preamble+self.equation+self.postamble).replace('%NOW%',Now())
        return tmp


# Prints usage of laveqed
def  _printUsage():
        usage = '\nlaveqed (LaTeX Vectorial Equation Editor) - Jos (2014)\n'\
                '\nUsage:\n'\
                '\n  -Creating a svg:'\
                '\n    laveqed "<equation>" [<filename>, <scale>, ...] \n'\
                '\n  -Reading a svg:\n    laveqed <filename.svg>\n'\
                '\n e.g.\n    laveqed "F=ma"\t\t-> Create svg file named as current time'\
                '\n    laveqed "F=ma" Newton.svg\t-> Create Newton.svg'\
                '\n    laveqed "F=ma" Newton 10\t-> Create Newton.svg with scale 10'\
                '\n    laveqed Newton.svg\t\t-> Read Newton.svg; output "F=ma"\n'
        print(usage)


# Returns a string of the form YYYY-MM-DD for current day! Adds _hour-min-sec if HMS is true
def Now(HMS=True):
    from time import time
    from datetime import datetime
    if not HMS:
        return datetime.fromtimestamp(time()).strftime('%Y-%m-%d')
    else:
        return datetime.fromtimestamp(time()).strftime('%Y-%m-%d_%H-%M-%S')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1][-4:]=='.svg':
        a=laveqed(eqonly=True)
        try:
            a.loadsvg(sys.argv[1])
            print(a.equation)
        except: print("Error loading file "+sys.argv[1])
    elif len(sys.argv) in [3,4,5]:
        a=laveqed(*sys.argv[1:])
        a.makesvg()
    elif len(sys.argv) == 2:
        if sys.argv[1]=='--help':
            _printUsage()
        else:
            a=laveqed(sys.argv[1])
            a.name=Now()
            a.makesvg()
    else:
        _printUsage()

        


