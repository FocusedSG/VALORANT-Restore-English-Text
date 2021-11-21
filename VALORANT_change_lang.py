import os
import ctypes
import string
import sys
from ctypes import windll, wintypes
from uuid import UUID
import requests
from shutil import copy2

def printHeader():
    print("=========================================")
    print("This script changes your VALORANT display")
    print("language into English while keeping audio")
    print("language as Korean.")
    print("")
    print("Remember to set your game language to")
    print("Korean and download the update before")
    print("running this script.")
    print("")
    print("Press ENTER to continue")
    print("=========================================")

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
    if not os.path.isdir(path): # Check if the directory exist
        os.mkdir(path) # Create path is the directory does not exist

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

if not isAdmin(): # Checking if program has administrator permission
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    exit()

printHeader() # Print instructions
input() # Press ENTER to continue
downloadsPath = getDownloadsPath() # Get downloads folder
path = os.path.join(downloadsPath, "VALORANT_change_lang") # Get downloads location to store the language files
downloadFile("https://github.com/FocusedSG/VALORANT_Lang/releases/download/Release/ko_KR_Text-WindowsClient.pak", destPath=path)
downloadFile("https://github.com/FocusedSG/VALORANT_Lang/releases/download/Release/ko_KR_Text-WindowsClient.sig", destPath=path)
fileName = "ko_KR_Text-WindowsClient"
drives = getDrives() # Get drives and store them in an array
valorantPath = "Riot Games\\VALORANT\\live\\ShooterGame\\Content\\Paks"
foundValorant = False
for drive in drives: # Search for VALORANT installation folder
    if os.path.isdir(drive + ":\\" + valorantPath):
        foundValorant = True
        print("\nDetected VALORANT installation path:", "\"" + drive + ":\\Riot Games\\VALORANT\"\n")
        copy2(path + "\\" + fileName + ".pak", drive + ":\\" + valorantPath)
        copy2(path + "\\" + fileName + ".sig", drive + ":\\" + valorantPath)
if foundValorant:
    print("All done! Remember to run this script before starting VALORANT everytime!")
else:
    print("ERROR: No VALORANT installation found.")
print("\nPress ENTER to quit.")
input()