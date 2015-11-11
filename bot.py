#!/usr/bin/env python

"""A generic IRC bot with plugin capabilities"""

import socket, threading, configparser, glob, os, sys, time, queue, ast, select, OpenSSL
from pluginbase import PluginBase
from colorama import init as colorinit
from datetime import datetime
from traceback import format_exc

__title__ = "Generic IRC Bot"
__version__ = "0.2"

colorinit()
if sys.platform == "win32":
    os.system("chcp 65001")
print("Loading plugins...")
plugin_base = PluginBase(package='plugins')
plugin_source = plugin_base.make_plugin_source(searchpath=["./plugins"])
modules = glob.glob(os.getcwd()+"/plugins/*.py")
plugins = []
global pluginThread
pluginThread = {}
orderQueue = queue.Queue()
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
config = {}
keepThreads = queue.Queue()
for f in modules:
    #print(os.path.basename(f)[:-3])
    plugins.append(os.path.basename(f)[:-3])
    with plugin_source:
        exec("from plugins import " + os.path.basename(f)[:-3])


def init():
    if sys.platform == "win32":
        os.system("title %s v%s" % (__title__, __version__))
        os.system("cls")
    else:
        os.system("clear")
    print(__title__ + ' ' + __version__)
    print("Initializing...")
    profile_files = glob.glob(os.getcwd() + "/profiles/*.ini")
    profiles = {}
    goodProfile = 0
    if len(profile_files) > 1:
        while not goodProfile:
            n = 1
            print("\nFound %s profiles:" % str(len(profile_files)))
            for file in profile_files:
                profiles[n] = file
                print("%s (%s)" % (os.path.basename(file), str(n)))
                n += 1
            profile = input("\nSelect profile: ")
            try:
                int(profile)
                choseNumber = 1
            except:
                choseNumber = 0
            if choseNumber and (int(profile) >= 1 and int(profile) <= n):
                profile = profiles[int(profile)]
                goodProfile = 1
            elif os.path.isfile(os.getcwd() + "/" + profile):
                profile = os.getcwd() + "/" + profile
                goodProfile = 1
    config = {}
    config["version"] = __version__
    config["title"] = __title__
    configreader = configparser.ConfigParser()
    print("\nReading config...")
    configreader.read(profile)
    # Puts all the variables from config.ini into dictionary config
    # E.g. a variable under [Connection] is stored as config["Connection"][variable]
    for category in configreader:
        #print('\n[' + category + ']')
        if category not in config:
            config[category] = {}
        for value in configreader[category]:
            config[category][value] = configreader[category][value]
            #print(value + ": " + configreader[category][value])
    currentNick = config["Bot"]["nick"]
    if sys.platform == "win32":
        os.system("title %s v%s - %s" % (__title__, __version__, config["Profile"]["name"]))
        os.system("cls")
    else:
        os.system("clear")
    config["Plugins"] = {}
    for plugin in plugins:
        exec('config["Plugins"][os.path.basename(plugin)] = ' + plugin + '.about()')
    connect(config, currentNick)


def connect(config, currentNick):    
    keepThreads.put(1)
    reconnection = False
    while catgirls_do_not_exist:
        goodData = 0
        runPlugins("beforeConnection", config, None, keepThreads)
        #time.sleep(1)
        while catgirls_do_not_exist:
            connection_success = 0
            try:
                registered = False
                print(str(datetime.now())[:-7] + " >> Connecting to IRC...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if config["Connection"]["ssl"].lower() == "true":
                    context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
                    mainSocket = OpenSSL.SSL.Connection(context, sock)
                else:
                    mainSocket = sock
                mainSocket.connect((config["Connection"]["hostname"], int(config["Connection"]["port"])))
                print(str(datetime.now())[:-7] + " >> Connected.\n")
                mainSocket.setblocking(0)
                if config["Connection"]["ssl"].lower() == "true":
                    while True:
                        try:
                            mainSocket.do_handshake()
                            break
                        except OpenSSL.SSL.WantReadError:
                            pass
                ready = select.select([mainSocket], [], [], 1)
                mainSocket.send(b"NICK " + str.encode(currentNick) + b"\n")
                mainSocket.send(b"USER " + str.encode(config["Bot"]["username"]) + b" 0 * :...\n")
                #keepThreads.put(1)
                runPlugins("afterConnection", config, None, keepThreads)
                connection_success = 1
            except TimeoutError:
                print(str(datetime.now())[:-7] + " >> Connection failed: connection timed out")
                time.sleep(1)
                pass
            except:
                print(str(datetime.now())[:-7] + " >> Connection failed")
                print(str(format_exc()))
                time.sleep(1)
                #runPlugins("failedConnection", config, format_exc(), keepThreads)
                pass
            readbuffer = ""
            lines = []
            spill = ""
            tick = 0
            while connection_success:
                try:
                    #print(mainSocket.recv)
                    runPlugins("onTick", config, None, keepThreads)
                    tick += 1
                    if tick % 10 == 0:
                        runPlugins("on10Tick", config, None, keepThreads)
                    if tick/float(config["Bot"]["tickrate"]) > 30 and not registered:
                        print(str(datetime.now())[:-7] + " >> Registration failed")
                        time.sleep(1)
                        break
                    while not orderQueue.empty():
                        orders = orderQueue.get()
                        if type(orders) != None:
                            try:
                                for order in orders.keys():
                                    if type(orders[order]) == list:
                                        for line in orders[order]:
                                            #exec(order + "(mainSocket, " + line + ")")
                                            if type(orders[order]) == str:
                                                exec(order + "(mainSocket, '" + line + "', config)")                                    
                                            else:
                                                exec(order + "(mainSocket, '" + str(line).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"') + "', config)")
                                    else:
                                        if type(orders[order]) == str:
                                            exec(order + "(mainSocket, '" + orders[order] + "', config)")
                                        else:
                                            exec(order + "(mainSocket, '" + str(orders[order]).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"') + "', config)")
                            except AttributeError:
                                pass
                    try:
                        readbuffer = ""
                        lines = []
                        try:
                            if ready[0]:
                                goodData = 0
                                readbuffer = readbuffer + mainSocket.recv(4096).decode("utf-8").replace("\r", "")
                                goodData = 1
                        except ConnectionResetError:
                            print("Connection reset by host.")
                            connection_success = 0
                            #keepThreads.get()
                            break
                        except ConnectionAbortedError:
                            print("An established connection was aborted by the software in your host machine.")
                            connection_success = 0
                            #keepThreads.get()
                            break
                        except BlockingIOError:
                            goodData = 0
                            pass
                        except OpenSSL.SSL.WantReadError:
                            pass
                        except:
                            print(str(format_exc()))
                        lines = readbuffer.split("\n") # All data recieved from the IRC server will be split in to lines - this is how IRC commands are separated
                        if goodData:
                            if spill != "":
                                lines[0] = spill + lines[0]
                            if readbuffer[-1] != "\n": # If the last character from the server was not a newline, the entire command was not recieved. Store it in spill for joining on the next loop.
                                spill = lines[-1]
                                del lines[-1]
                            #print(lines)
                            runPlugins("onRawData", config, lines, keepThreads)
                    except:
                        print(str(format_exc()))
                        pass
                    for command in lines:
                        if command != "":
                            if command[:4].upper() == "PING": # If the server is pinging the bot to make sure it's still connected
                                command = command.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                                runPlugins("onPING", config, command, keepThreads)
                                break 
                                
                            elif command.split(" ")[1] == "001": # Registration complete
                                if not reconnection:
                                    runPlugins("onRegistration", config, command, keepThreads)
                                    runPlugins("onAllRegistration", config, command, keepThreads)
                                    reconnection = True
                                    registered = True
                                else:
                                    runPlugins("onAllRegistration", config, command, keepThreads)
                                
                            elif command.split(" ")[1] == "433": # Chosen nick is already in use
                                currentNick = command.split(" ")[3]
                                runPlugins("onNickInUse", config, currentNick, keepThreads)
                                
                            elif command.split(" ")[1].upper() == "PRIVMSG": # format: ":<remote_nick>!<remote_username>@<remote_host> PRIVMSG <destination> :<message>"
                                recvNick = command.split(" ")[0].split("!")[0][1:]
                                recvUsername = command.split(" ")[0].split("!")[1].split("@")[0]
                                recvHost = command.split(" ")[0].split("!")[1].split("@")[1]
                                destination = command.split(" ")[2]
                                message = command.split("PRIVMSG " + destination + " :")[1]
                                message = message.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                                if message[0] == "" and message[-1] == "":                            
                                    message = message[1:][:-1]
                                    command = message.split(" ")[0]
                                    arguments = message.split(" ")
                                    del arguments[0]
                                    data = {"recvNick" : recvNick,
                                        "recvUsername" : recvUsername,
                                        "recvHost" : recvHost,
                                        "destination" : destination,
                                        "command" : command,
                                        "arguments" : arguments}
                                    if command != "VERSION":
                                        runPlugins("onCTCP", config, data, keepThreads)
                                    else:
                                        orderQueue.put({"NOTICE" : {"destination" : recvNick, "message" : "VERSION %s v%s by maciozo" % (__title__, __version__)}})
                                else:
                                    data = {"recvNick" : recvNick,
                                        "recvUsername" : recvUsername,
                                        "recvHost" : recvHost,
                                        "destination" : destination,
                                        "isPM" : destination[0].isalnum(),
                                        "message" : message}
                                    runPlugins("onPRIVMSG", config, data, keepThreads)
                                    
                            elif command.split(" ")[1].upper() == "NOTICE": # format: ":<remote_nick>!<remote_username>@<remote_host> NOTICE <destination> :<message>"
                                if "@" in command:
                                    recvNick = command.split(" ")[0].split("!")[0][1:]
                                    try:
                                        recvUsername = command.split(" ")[0].split("!")[1].split("@")[0]
                                    except IndexError:
                                        recvUsername = "GLOBAL"
                                    try:
                                        recvHost = command.split(" ")[0].split("!")[1].split("@")[1]
                                    except IndexError:
                                        recvHost = config["Connection"]["hostname"]
                                else:
                                    recvNick = "SERVER"
                                    recvUsername = "SERVER"
                                    recvHost = command.split(" ")[0][1:]
                                destination = command.split(" ")[2]
                                message = command.split("NOTICE " + destination + " :")[1]#.replace("'", "\'").replace('"', '\"').replace("\\", "\\\\")
                                message = message.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                                data = {"recvNick" : recvNick,
                                    "recvUsername" : recvUsername,
                                    "recvHost" : recvHost,
                                    "destination" : destination,
                                    "message" : message}
                                runPlugins("onNOTICE", config, data, keepThreads)
                    time.sleep(1/float(config["Bot"]["tickrate"]))
                except KeyboardInterrupt:
                    runPlugins("onQUIT", config, 0, keepThreads)
                    print("Shutting down in 3 seconds...")
                    time.sleep(3)
                    send_raw(mainSocket, "quit Terminated by bot operator.\n", config)
                    sys.exit(0)

def runPlugins(event, config, data, keepThreads):
    for plugin in plugins:        
        pluginThread[plugin] = threading.Thread(target = pluginWorker, name = plugin + " worker", args = (str(event), config, data, plugin, keepThreads), daemon = False)
        pluginThread[plugin].start()

def pluginWorker(event, config, data, plugin, keepThreads):
    try:        
        global response
        exec("response = " + plugin + "." + event + "(config, data, keepThreads)\norderQueue.put(response)")
    except AttributeError:
        pass # If the plugin doesn't listen for the event, just move on to the next plugin
    except:
        print(str(format_exc()))
        pass
    
def send_raw(mainSocket, data, config):
    string_to_send = str.encode(data) + b"\n"
    runPlugins("onDataSend", config, string_to_send, keepThreads)
    mainSocket.send(string_to_send)
    
def echo(mainSocket, data, config):
    print(data)
    
def setNICK(mainSocket, nick, config):
    currentNick = nick
    config["Bot"]["nick"] = nick
    string_to_send = b"NICK " + str.encode(nick) + b"\n"
    runPlugins("onDataSend", config, string_to_send, keepThreads)
    mainSocket.send(string_to_send)
    
def JOIN(mainSocket, channel, config):
    string_to_send = b"JOIN :" + str.encode(channel) + b"\n"
    runPlugins("onDataSend", config, string_to_send, keepThreads)
    mainSocket.send(string_to_send)
    
def PRIVMSG(mainSocket, data, config):
    data = ast.literal_eval(data)
    string_to_send = b"PRIVMSG " + str.encode(data["destination"]) + b" :" + str.encode(data["message"]) + b"\n"
    runPlugins("onDataSend", config, string_to_send, keepThreads)
    mainSocket.send(string_to_send)
    
def NOTICE(mainSocket, data, config):
    data = ast.literal_eval(data)
    string_to_send = b"NOTICE " + str.encode(data["destination"]) + b" :" + str.encode(data["message"]) + b"\n"
    runPlugins("onDataSend", config, string_to_send, keepThreads)
    mainSocket.send(string_to_send)
    
catgirls_do_not_exist = True # :(

if __name__ == "__main__":
    init()
