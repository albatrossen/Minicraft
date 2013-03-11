from distutils.core import setup
import py2exe

setup(
	windows=[{'script':'minicraft_qt.py','icon_resources': [(1, "minecraft/ui/icon.ico")]}],
	zipfile=None,
	options={ "py2exe": { 
		"bundle_files": 1,
		"dll_excludes": ["MSVCP90.dll", "HID.DLL", "w9xpopen.exe"],
		"includes": ["sip",'platform']
	}}
)
