# coding=utf8
import re
import json
from itertools import izip

splitter = re.compile(u'§(.)')

styles = {
	'0':('<span style="color:#000000;">','</span>'),
	'1':('<span style="color:#0000aa;">','</span>'),
	'2':('<span style="color:#00aa00;">','</span>'),
	'3':('<span style="color:#00aaaa;">','</span>'),
	'4':('<span style="color:#aa0000;">','</span>'),
	'5':('<span style="color:#aa00aa;">','</span>'),
	'6':('<span style="color:#ffaa00;">','</span>'),
	'7':('<span style="color:#aaaaaa;">','</span>'),
	'8':('<span style="color:#555555;">','</span>'),
	'9':('<span style="color:#5555ff;">','</span>'),
	'a':('<span style="color:#55ff55;">','</span>'),
	'b':('<span style="color:#55ffff;">','</span>'),
	'c':('<span style="color:#ff5555;">','</span>'),
	'd':('<span style="color:#ff55ff;">','</span>'),
	'e':('<span style="color:#ffff55;">','</span>'),
	#'f':('<span style="color:#ffffff;">','</span>'),

	#'k':('<span style="color:#ffffff;">','</span>')
	'l':('<b>','</b>'),
	'm':('<span style="text-decoration: line-through;">','</span>'),
	'n':('<u>','</u>'),
	'o':('<i>','</i>'),
	'black':('<span style="color:#000000;">','</span>'),
	'dark_blue':('<span style="color:#0000aa;">','</span>'),
	'dark_green':('<span style="color:#00aa00;">','</span>'),
	'dark_aqua':('<span style="color:#00aaaa;">','</span>'),
	'dark_red':('<span style="color:#aa0000;">','</span>'),
	'dark_purple':('<span style="color:#aa00aa;">','</span>'),
	'gold':('<span style="color:#ffaa00;">','</span>'),
	'gray':('<span style="color:#aaaaaa;">','</span>'),
	'dark_gray':('<span style="color:#555555;">','</span>'),
	'blue':('<span style="color:#5555ff;">','</span>'),
	'green':('<span style="color:#55ff55;">','</span>'),
	'aqua':('<span style="color:#55ffff;">','</span>'),
	'red':('<span style="color:#ff5555;">','</span>'),
	'light_purple':('<span style="color:#ff55ff;">','</span>'),
	'yellow':('<span style="color:#ffff55;">','</span>'),
	#'white':('<span style="color:#ffffff;">','</span>'),

	#'obfuscated':('<span style="color:#ffffff;">','</span>')
	'bold':('<b>','</b>'),
	'strikethrough':('<span style="text-decoration: line-through;">','</span>'),
	'underline':('<u>','</u>'),
	'italic':('<i>','</i>'),
}

def format_json(string):
	try:
		obj = json.loads(string)
		return format_jsonobj(obj)
	except ValueError:
		raise
	return convert_to_html(string)

def format_jsonobj(obj):
	if isinstance(obj,basestring):
		return convert_to_html(obj)
	val = convert_to_html(obj['text']) if 'text' in obj else ''
	if 'color' in obj and obj['color'] in styles:
		head, tail = styles[obj['color']]
		val = head + val + tail
	if 'extra' in obj:
		val += ''.join(format_jsonobj(x) for x in obj['extra'])
	return val
	

def grouped(iterable, n):
	"s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
	return izip(*[iter(iterable)]*n)

def escape(string):
	return string.replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")

def strip_codes(msg):
	return splitter.sub('',unicode(msg))

def convert_to_html(msg):
	l = splitter.split(msg)
	r = [escape(l[0])]
	stack = []
	for style, text in grouped(l[1:],2):
		if style not in 'klmno':
			r.extend(reversed(stack))
			stack = []
		if style in styles:
			open, end = styles[style]
			r.append(open)
			stack.append(end)
		r.append(escape(text))
	r.extend(reversed(stack))
	return ''.join(r)
