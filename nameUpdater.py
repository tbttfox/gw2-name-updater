import telnetlib
from threading import Lock
import ctypes
import time
import mmap
import json

ts3Escapes = [
	 (chr(92), r'\\'),	 # \
	 (chr(47), r"\/"),	 # /
	 (chr(32), r'\s'),	 # Space
	 (chr(124), r'\p'),  # |
	 (chr(7), r'\a'),	 # Bell
	 (chr(8), r'\b'),	 # Backspace
	 (chr(12), r'\f'),	 # Form Feed
	 (chr(10), r'\n'),	 # Newline
	 (chr(13), r'\r'),	 # Carriage Return
	 (chr(9), r'\t'),	 # Horizontal Tab
	 (chr(11), r'\v'),	 # Vertical tab
]

class Link(ctypes.Structure):
	_fields_ = [
		("uiVersion",		ctypes.c_uint32),
		("uiTick",			ctypes.c_ulong),
		("fAvatarPosition", ctypes.c_float * 3),
		("fAvatarFront",	ctypes.c_float * 3),
		("fAvatarTop",		ctypes.c_float * 3),
		("name",			ctypes.c_wchar * 256),
		("fCameraPosition", ctypes.c_float * 3),
		("fCameraFront",	ctypes.c_float * 3),
		("fCameraTop",		ctypes.c_float * 3),
		("identity",		ctypes.c_wchar * 256),
		("context_len",		ctypes.c_uint32),
		("context",			ctypes.c_uint32 * (256/4)), # is actually 256 bytes of whatever
		("description",		ctypes.c_wchar * 2048)
	]

def getGW2Name():
	memfile = mmap.mmap(0, ctypes.sizeof(Link), "MumbleLink")
	#data = memfile.read(ctypes.sizeof(Link))
	time.sleep(1)
	memfile.seek(0)
	data = memfile.read(ctypes.sizeof(Link))

	cstring = ctypes.create_string_buffer(data)
	result = ctypes.cast(ctypes.pointer(cstring), ctypes.POINTER(Link)).contents
	ID = result.identity

	try:
		toon = json.loads(ID)['name']
	except Exception as e:
		#print e
		print u"Can't find GW2 name, Retrying in 10 sec..."
		toon = None

	memfile.close()
	return toon

def sendTS3Command(server, command):
	cmd = command.encode('utf-8') + b'\n\r'
	#cmd = command + b'\n\r'
	server.write(cmd)
	time.sleep(1)
	res = server.read_very_eager()
	res = res.replace(r'\n\r', ' ').split()
	res = dict([i.split("=") for i in res if "=" in i])
	return res

def ts3UpdateNick(newNick):
	ip='127.0.0.1'
	port=25639
	lock = Lock()
	nickKey = "client_nickname"

	with lock:
		try:
			server = telnetlib.Telnet(ip, port)
		except telnetlib.socket.error:
			raise RuntimeError("Cannot Connect")

		time.sleep(1)
		data = server.read_very_eager()
		if not data.startswith("TS3 Client"):
			raise RuntimeError("Cannot Connect")
		
		time.sleep(1)
		rawclid = sendTS3Command(server, 'whoami')
		clid = rawclid['clid']

		rawNick = sendTS3Command(server, u'clientvariable clid={0} {1}'.format(clid, nickKey))
		nick = rawNick[nickKey].decode('utf-8')
		for k,v in ts3Escapes:
			nick = nick.replace(v,k)

		if nick != newNick:
			print "Setting Nick to:", newNick
			for k,v in ts3Escapes:
				newNick = newNick.replace(k,v)
			sendTS3Command(server, u'clientupdate {0}={1}'.format(nickKey, newNick))

def looper(defName):
	gw2Name = ""
	while True:
		currName = getGW2Name()
		if gw2Name != currName:
			gw2Name = currName
			if currName is None:
				dispName = defName
			else:
				if defName == currName:
					dispName = defName
				else:
					dispName = defName + u" ({0})".format(currName)
			ts3UpdateNick(dispName)
		time.sleep(10)

if __name__ == "__main__":
	looper(u"Wrinn Ped")

