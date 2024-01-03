# AndroidRemoteGPT by Jonathan Germain
# Available at https://github.com/compilebunny/androidremoteGPT
# Licensed under version 3 of the GNU General Public License

import os
import time
import json
import re
from subprocess import Popen, PIPE
import sys
try: 
	import termuxgui as tg
except ModuleNotFoundError:
    sys.exit("termuxgui module not found. Please install the Termux:GUI python bindings as described in the tutorial")


def closeconnection(connex):
    connex.close()

def ReadConfigFromDisk(cfname):
	configfile = open(os.path.expanduser(cfname), "r")
	configinfo = configfile.readlines()

	print (f"read {len(configinfo)} lines")

	# remove all comments flagged with '#' and all whitespace before '='
	for i in range(len(configinfo)):
		if ('=' in configinfo[i]): configinfo[i]=re.sub(r' +=', '=', configinfo[i])
		if ('#' in configinfo[i]): configinfo[i]=configinfo[i][:configinfo[i].index('#')]

	# remove whitespace at beginning and end of line and all config commands fewer than 3 non-whitespace characters long 
	configinfo=list(map(str.rstrip, configinfo))
	configinfo=list(map(str.lstrip, configinfo))
	configinfo = [line for line in configinfo if len(line)>3]

	# Convert the array into a dict structure; keys are made lowercase automatically
	infopackage = {'server':'', 'port': '22', 'user':'', 'password':'', 'sequence':'', 'logfile':'', 'next_cmd_indicator':'⇢'}
	for i in range(len(configinfo)): 
		if ('=' in configinfo[i]): infopackage[str.lower(configinfo[i].split('=')[0])] = configinfo[i].split('=')[1]

	return infopackage

def WriteConfigToDisk(cfdata):
	with open(os.path.expanduser(configfilename), "w") as f:
		for k in cfdata.keys():
			f.write("{}={}\n".format(k,cfdata[k]))
		f.close()

def ConfigPageTextObject(activity,layout,text,size):
	output = tg.TextView(activity, text, layout)
	output.setlinearlayoutparams(0)
	output.settextsize(size)
	output.setheight(tg.View.WRAP_CONTENT)
	return output	

def MainPageTextObject(activity,layout,text,size):
	output = tg.TextView(activity, text, layout)
	output.setlinearlayoutparams(0)
	output.settextsize(size)
	output.setheight(tg.View.WRAP_CONTENT)
	return output	

def ConfigPageEditBox(activity,layout,text,size):
	output = tg.EditText(activity, text, layout)
	output.setlinearlayoutparams(0)
	output.setdimensions("wrap_content", size)
	output.setheight(tg.View.WRAP_CONTENT)
	output.sendtextevent(True)
	return output

def MainPageEditBox(activity,layout,text,size):
	output = tg.EditText(activity, text, layout)
	output.setlinearlayoutparams(0)
	output.setdimensions("wrap_content", size)
	output.setheight(tg.View.WRAP_CONTENT)
	output.sendtextevent(True)
	return output

def doConfigPage(connection):
	# create a new Activity for the config screen. By default, a new Task as created under configactivity.t
	configactivity = tg.Activity(connection,canceloutside=False)

	# Create a layout for the config screen
	configlayout = tg.LinearLayout(configactivity)

	# create a TextView page title
	title = tg.TextView(configactivity, "Configuration",configlayout)
	title.setlinearlayoutparams(0)
	title.settextsize(20)
	title.setmargin(5)

	# create entry points for all necessary config data
	recommendation_message = ConfigPageTextObject(configactivity, configlayout,"For security, passwords are disallowed. Please set up key-based authentication in ~/.ssh/config.",12)
	
	serverask = ConfigPageTextObject(configactivity, configlayout,"host (server name or as defined in .ssh/config)",12)
	getservername = ConfigPageEditBox(configactivity, configlayout, configdata['server'],60)

	portask = ConfigPageTextObject(configactivity, configlayout,"port number (default: 22)",12)
	# the port number requires special treatment because it should allow numbers only
	getportnum = tg.EditText(configactivity, configdata['port'], configlayout, inputtype='number')
	getportnum.setlinearlayoutparams(0)
	getportnum.setdimensions("wrap_content", 10)
	getportnum.setheight(tg.View.WRAP_CONTENT)
	getportnum.sendtextevent(True)

	userask = ConfigPageTextObject(configactivity, configlayout,"user",12)
	getusername = ConfigPageEditBox(configactivity, configlayout, configdata['user'],60)

#	passask = ConfigPageTextObject(configactivity, configlayout,"password (leave blank if using an ssh key)",12)
#	getpassword = ConfigPageEditBox(configactivity, configlayout, configdata['password'],60)

	nextask = ConfigPageTextObject(configactivity, configlayout,"next command indicator - important - tells the interface when the bot response is complete and the system is ready for a new query",12)
	getnextcmd = ConfigPageEditBox(configactivity, configlayout, configdata['next_cmd_indicator'],1)

	sequenceask = ConfigPageTextObject(configactivity, configlayout,"setup sequence: commands to execute after logging in. Separate multiple unix shell commands with semicolons.",12)
	getsequence = ConfigPageEditBox(configactivity, configlayout, configdata['sequence'],60)

	logfileask = ConfigPageTextObject(configactivity, configlayout,"logfile name",12)
	getlogfile = ConfigPageEditBox(configactivity, configlayout, configdata['logfile'],60)

	buttons = tg.LinearLayout(configactivity, configlayout, False)
	buttons.setlinearlayoutparams(0)
	savebutton = tg.Button(configactivity, "save", buttons)
	cancelbutton = tg.Button(configactivity, "cancel", buttons)

	for eventmanager in connection.events():
		if eventmanager.type == tg.Event.destroy and eventmanager.value["finishing"]:
			print (f"exiting config screen: {configdata}")			
			configactivity.finish()
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == savebutton:
			configdata["server"] = getservername.gettext()
			configdata["port"] = getportnum.gettext()
			configdata["user"] = getusername.gettext()
#			configdata["password"] = getpassword.gettext()
			configdata["sequence"] = getsequence.gettext()
			configdata["logfile"] = getlogfile.gettext()
			configdata["next_cmd_indicator"] = getnextcmd.gettext()
			WriteConfigToDisk(configdata)
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == cancelbutton:
			configactivity.finish()
#			doMainPage(connection)
			tg.Event.destroy
			print (f"exiting config screen: {configdata}")			
			return
			
# Finished with doConfigPage

def doMainPage(connection):

	mainscreen = tg.Activity(connection,canceloutside=False)
	latestcommand = "blank"
	lastresponse = "no response yet"
	
	speakstate=False
	logstate=False
	
	# Create a set of layouts
	first_layout = tg.LinearLayout(mainscreen) 
	horizdivide = tg.LinearLayout(mainscreen, first_layout, False)
	query_side = tg.LinearLayout(mainscreen, horizdivide)
	control_side = tg.LinearLayout(mainscreen, horizdivide)
#	control_side.setwidth(80)

	# create a TextView page title for the query/response side of the screen
	title = tg.TextView(mainscreen, "Query/Response",query_side)
	title.setlinearlayoutparams(0)
	title.settextsize(20)
	title.setmargin(5)
	
	nextcommand = MainPageEditBox(mainscreen,query_side,latestcommand,12)	
	response = MainPageTextObject(mainscreen,query_side,"no response yet",12)	

	requestbutton = tg.Button(mainscreen, "request", query_side)
	requestbutton.setlinearlayoutparams(0)
	requestbutton.setheight(tg.View.WRAP_CONTENT)

	# create a TextView page title for the control side of the screen
	title = tg.TextView(mainscreen, "Control", control_side)
	title.setlinearlayoutparams(0)
	title.settextsize(20)
	title.setmargin(5)

	configbutton = tg.Button(mainscreen, "configuration", control_side)
	configbutton.setlinearlayoutparams(0)
	configbutton.setheight(tg.View.WRAP_CONTENT)

	connectbutton = tg.Button(mainscreen, "connect", control_side)
	connectbutton.setlinearlayoutparams(0)
	connectbutton.setheight(tg.View.WRAP_CONTENT)

	disconnectbutton = tg.Button(mainscreen, "disconnect", control_side)
	disconnectbutton.setlinearlayoutparams(0)
	disconnectbutton.setheight(tg.View.WRAP_CONTENT)

	speak = tg.Checkbox(mainscreen,"speak?",control_side,False)
	speak.setlinearlayoutparams(0)
	speak.setheight(tg.View.WRAP_CONTENT)

	logcheckbox = tg.Checkbox(mainscreen,"log?",control_side,False)
	logcheckbox.setlinearlayoutparams(0)
	logcheckbox.setheight(tg.View.WRAP_CONTENT)

	exitbutton = tg.Button(mainscreen, "exit", control_side)
	exitbutton.setlinearlayoutparams(0)
	exitbutton.setheight(tg.View.WRAP_CONTENT)

	errorstate_text = MainPageTextObject(mainscreen,control_side,"no state",12)
	logstate_text = MainPageTextObject(mainscreen,control_side,"not logging",12)
	speakstate_text = MainPageTextObject(mainscreen,control_side,"not speaking",12)

	
	for eventmanager in connection.events():
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == speak:
			if (speakstate): 
				speakstate=False
				speakstate_text.settext("speech off")
			else: 
				speakstate=True
				speakstate_text.settext("speech on")
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == logcheckbox:
			if (logstate): 
				logstate=False
				logstate_text.settext("logging off")
			else: 
				logstate=True
				logstate_text.settext("logging on")
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == configbutton:
			doConfigPage(c)
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == connectbutton:
			errorstate_text.settext("waiting for connection")
			ssh_connection=MakeSSHConnection()
			lastresponse=printthrough(ssh_connection,False)
			response.settext(lastresponse)
			errorstate_text.settext("connected")
#			control_side.setwidth(80)
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == disconnectbutton:
			try:
				if ssh_connection.poll() is None: ssh_connection.terminate()
			except NameError: nothing=1	
			errorstate_text.settext("disconnected")
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == exitbutton:
			mainscreen.finish()
			try:
				if ssh_connection.poll() is None: ssh_connection.terminate()
			except NameError: nothing=1	
			connection.close()
			sys.exit(0)
		if eventmanager.type == tg.Event.click and eventmanager.value["id"] == requestbutton:
			try:
				if ssh_connection.poll() is None:
					ssh_connection.stdin.write(nextcommand.gettext()+"\n")
					ssh_connection.stdin.flush()  # important
					errorstate_text.settext("awaiting response")
					lastresponse=printthrough(ssh_connection,False)
					response.settext(lastresponse)
					errorstate_text.settext("connected")
					# Log the result
					if (logstate): logresult(nextcommand.gettext(),lastresponse)
					if (speakstate): voicespeak(lastresponse)
#					control_side.setwidth(80)
			except NameError: errorstate_text.settext("disconnected")	



def printthrough(handle,debug):	
# Read the source until the next command indicator is reached and return the result
	response = ""
	if (debug==True): print ("debug mode")	
	while True:
		newchar = handle.stdout.read(1)
		if (debug==True): print (f":{newchar}:")
		response = response + newchar
		if configdata["next_cmd_indicator"] in newchar:
			break
	if (debug==True): print ("printthrough complete")	
	return response

def logresult(query,response):
	with open(configdata["logfile"],'a') as logf: logf.write("[query] "+query+"\n\n"+"[response] "+response+"\n\n")
	logf.close()

def voicespeak(text):
	speakhandle= Popen(['espeak','--stdin'],stdin=PIPE,stdout=PIPE,stderr=PIPE, encoding="UTF8")
	speakhandle.communicate(text)
	speakhandle.terminate()

def MakeSSHConnection():
	if len(configdata["port"])<1: configdata["port"]="22" 
#	p= Popen([ssh_location,'-p',configdata["port"],configdata["server"]],stdin=PIPE,stdout=PIPE,stderr=PIPE, encoding="UTF8")
	if len(configdata["user"])<1: p= Popen(['ssh','-p',configdata["port"],configdata["server"]],stdin=PIPE,stdout=PIPE,stderr=PIPE, encoding="UTF8")
	if len(configdata["user"])>1: 
		descrip=configdata["user"]+"@"+configdata["server"]
		p= Popen(['ssh','-p',configdata["port"],descrip],stdin=PIPE,stdout=PIPE,stderr=PIPE, encoding="UTF8")
	if len(configdata["sequence"])>1: 
		p.stdin.write(configdata["sequence"]+"\n")
		p.stdin.flush()  # important
		
	return(p)


# Start program
print ("AndroidRemoteGPT by Jonathan Germain\nAvailable at https://github.com/compilebunny/androidremoteGPT\nLicensed under version 3 of the GNU General Public License")


# Variable definitions
configfilename = '~/.androidGPT'
python_location="/data/data/com.termux/files/usr/bin/python"
ssh_location="/data/data/com.termux/fjiles/usr/bin/ssh"

print ("starting")
configdata = ReadConfigFromDisk(configfilename)
print (f"{configdata}")


print (f"About to make TermuxGUI connection")
with tg.Connection() as c:
	#Load the front page of the app
	lastresponse="no response"
	doMainPage(c)

