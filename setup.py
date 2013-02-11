from distutils.core import setup
import py2exe

setup(
	windows=['minicraft_qt.py'],
	zipfile=None,
	options={ "py2exe": { 
		"bundle_files": 1,
		"dll_excludes": ["MSVCP90.dll", "HID.DLL", "w9xpopen.exe"],
		"includes": ["sip",'platform']
	}}
)
