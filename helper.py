from glob import glob
import os
import re

def getSpecificValueFromStrings(allStrings,searchString):
    matched_lines = [line for line in allStrings if searchString in line]
    return  int(re.findall(r'\d+', matched_lines[0])[0])

def getSpecificValue(path,file,start_end,searchString):
    Path = os.path.join(path,start_end,file)
    File = open(Path, 'r') 
    FileS = File.readlines() 
    FileVal =getSpecificValueFromStrings(FileS,searchString)
    return FileVal

def getSpecificValueDiff(path,file,searchString):
    startFileVal =getSpecificValue(path,file,"start",searchString)
    endFileVal =getSpecificValue(path,file,"end",searchString)
    return endFileVal - startFileVal

def getTestIdFromFilename(filename):
    return  int(re.findall(r'\d+', filename)[0])