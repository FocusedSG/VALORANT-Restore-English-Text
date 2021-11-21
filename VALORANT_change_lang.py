import os
import ctypes
import string
import sys
import requests
import time
from ctypes import windll, wintypes
from uuid import UUID
from shutil import copy2


def printHeader():
    print("=========================================")
    print("VALORANT Restore English Text")
    print("By: FocusedSG")
    print("")
    print("This script changes your VALORANT text")
    print("language into English while keeping audio")
    print("language as your current language.")
    print("")
    print("Remember to set your game language first")
    print("and download the update before running")
    print("script.")
    print("")
    print("Press ENTER to continue")
    print("=========================================")
    input() # Press ENTER to continue

# ctypes GUID copied from MSDN sample code
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ] 

    def __init__(self, uuidstr):
        uuid = UUID(uuidstr)
        ctypes.Structure.__init__(self)
        self.Data1, self.Data2, self.Data3, \
            self.Data4[0], self.Data4[1], rest = uuid.fields
        for i in range(2, 8):
            self.Data4[i] = rest>>(8-i-1)*8 & 0xff

SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
SHGetKnownFolderPath.argtypes = [
    ctypes.POINTER(GUID), wintypes.DWORD,
    wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
]

def getDownloadsPath():
    pathptr = ctypes.c_wchar_p()
    guid = GUID("{374DE290-123F-4565-9164-39C4925E467B}")
    if SHGetKnownFolderPath(ctypes.byref(guid), 0, 0, ctypes.byref(pathptr)):
        raise ctypes.WinError()
    return pathptr.value

def downloadFile(url: str, destPath: str):
    if not os.path.isdir(destPath): # Check if the directory exist
        os.mkdir(destPath) # Create path is the directory does not exist

    fileName = url.split('/')[-1].replace(" ", "_")  # Be careful with file names
    filePath = os.path.join(destPath, fileName)

    request = requests.get(url, stream=True)

    if request.ok:
        print("Downloading language file to", os.path.abspath(filePath))
        with open(filePath, 'wb') as file:
            for chunk in request.iter_content(chunk_size=1024 * 8):
                if chunk:
                    file.write(chunk)
                    file.flush()
                    os.fsync(file.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(request.status_code, request.text))

def getDrives():
    drives = []
    bitMask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitMask & 1:
            drives.append(letter)
        bitMask >>= 1
    return drives

def isAdmin():
    try:
        isAdmin = (os.getuid() == 0)
    except AttributeError:
        isAdmin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return isAdmin

def findFile(name, path):
    for root, dir, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def getLanguage(drive):
    languages = ["ja_JP", "ko_KR", "pt_BR", "it_IT", "de_DE", "fr_FR", "en_US"] # Supported languages
    foundLanguage = False
    for language in languages:
        lang = findFile(language + "_Audio-WindowsClient.pak", drive + ":\\Riot Games\\VALORANT\\live\\ShooterGame\\Content\\Paks")
        if lang is not None:
            foundLanguage = True
            return language
    if not foundLanguage:
        return None

def main():
    fileName = "_Text-WindowsClient"
    valorantPath = ":\\Riot Games\\VALORANT\\live\\ShooterGame\\Content\\Paks"
    if not isAdmin(): # Checking if program has administrator permission
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        exit()
    printHeader() # Print header and instructions
    downloadsPath = getDownloadsPath() # Get downloads folder
    path = os.path.join(downloadsPath, "VALORANT_change_lang") # Get downloads location to store the language files
    startTime = round(time.time() * 1000)
    print("Downloading language files...")
    downloadFile("https://github.com/FocusedSG/VALORANT-Restore-English-Text/releases/download/Release/en_US_Text-WindowsClient.pak", destPath=path)
    downloadFile("https://github.com/FocusedSG/VALORANT-Restore-English-Text/releases/download/Release/en_US_Text-WindowsClient.sig", destPath=path)
    timeTaken = round(time.time() * 1000) - startTime
    print("Downloaded 2 language files. Took", str(timeTaken) + "ms.\n")

    drives = getDrives() # Get drives and store them in an array
    valorantDrive = ""
    for drive in drives: # Search for VALORANT installation folder
        if os.path.isdir(drive + valorantPath):
            valorantDrive = drive
            print("Detected VALORANT installation path:", "\"" + drive + ":\\Riot Games\\VALORANT\"\n")

    if valorantDrive != "":
        valorantPath = valorantDrive + valorantPath # Setting absolute path to VALORANT installation
        language = getLanguage(valorantDrive) # Getting VALORANT language
        if language is not None:
            startTime = round(time.time() * 1000)
            print("Copying language files to VALORANT installation directory...")
            os.rename(path + "\\" + "en_US" + fileName + ".pak", path + "\\" + language + fileName + ".pak")
            os.rename(path + "\\" + "en_US" + fileName + ".sig", path + "\\" + language + fileName + ".sig")
            copy2(path + "\\" + language + fileName + ".pak", valorantPath)
            copy2(path + "\\" + language + fileName + ".sig", valorantPath)
            timeTaken = round(time.time() * 1000) - startTime
            print("Done copying files! Took", str(timeTaken) + "ms.\n")
            print("Remember to run this script before starting VALORANT everytime!")
        else:
            print("Sorry, the audio language of your VALORANT is not currently supported.")
    else:
        print("ERROR: No VALORANT installation found.")
    print("\nPress ENTER to quit.")
    input()

main()