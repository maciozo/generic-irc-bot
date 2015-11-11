from datetime import datetime

def about():
    return "Handles core functions of the bot, such as server registration and PING responses."

def onPING(config, data, keepAlive):
    response = {}
    if config["Core"]["showpings"] == "True":
        response["echo"] = [str(datetime.now())[:-7] + " >> PING :" + data.split(":")[1], str(datetime.now())[:-7] + " >> PONG :" + data.split(":")[1]]
    pong = "PONG :" + data.split(":")[1]
    response["send_raw"] = pong
    return response
    
def onPRIVMSG(config, data, keepAlive):
    response = {}
    if data["isPM"]:
        print(str(datetime.now())[:-7] + " >> PM from " + data["recvNick"] + ": " + data["message"])
    else:
        print(str(datetime.now())[:-7] + " >> " + data["recvNick"] + " @ " + data["destination"] + ": " + data["message"])
        
    if data["message"].lower() == "!%s" % config["Bot"]["nick"].lower():
        response = info(config, data)
    
    if data["message"].lower() == ".help plugins":
        response = pluginHelp(config, data)
        
    return response
        
def onNickInUse(config, currentNick, keepAlive):
    response = {}
    response["setNICK"] = currentNick + "_"
    return response
    
def onNOTICE(config, data, keepAlive):
    response = {}
    response["echo"] = str(datetime.now())[:-7] + " >> NOTICE from " + data["recvNick"] + ": " + data["message"]
    if data["recvNick"] == "SERVER":
        if "*** You are connected to" in data["message"]:
            response["JOIN"] = config["Bot"]["mainchannel"]
            #response["PRIVMSG"] = {"destination" : config["Bot"]["mainchannel"], "message" : config["title"] + " v" + config["version"]}
    return response
    
def onAllRegistration(config, command, keepAlive):
    response = {}
    welcome = command.split(":")[2].replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    response["echo"] = str(datetime.now())[:-7] + " >> " + welcome
    response["JOIN"] = config["Bot"]["mainchannel"]
    response["PRIVMSG"] = info(config, {"isPM" : True, "recvNick" : config["Bot"]["mainchannel"]})["PRIVMSG"]
    if config["Bot"]["oper"].lower() == "true":
        response["send_raw"] = "oper %s %s" % (config["Bot"]["operuser"], config["Bot"]["operpass"])
    return response
    
def onCTCP(config, data, keepAlive):
    response = {}
    if data["command"] == "TIME":
        time = str(datetime.now())
        response["NOTICE"] = {"destination" : data["recvNick"], "message" : "TIME %s" % time}
    elif data["command"] == "PING":
        response["NOTICE"] = {"destination" : data["recvNick"], "message" : "PING %s" % data["arguments"][0]}
    elif data["command"] == "FINGER":
        response["NOTICE"] = {"destination" : data["recvNick"], "message" : "FINGER どうしよう も ない 変態 ね！"}
    return response
    
def info(config, data):
    response = {}
    action = "NOTICE"
    if data["isPM"]:
        action = "PRIVMSG"
    response[action] = []
    response[action].append({"destination" : data["recvNick"], "message" : config["title"] + " v" + config["version"] + " by maciozo"})
    response[action].append({"destination" : data["recvNick"], "message" : "%s plugins loaded | .help plugins" % str(len(config["Plugins"]))})
    return response
    
def pluginHelp(config, data):
    response = {}
    action = "NOTICE"
    if data["isPM"]:
        action = "PRIVMSG"
    response[action] = []
    for pluginName, description in config["Plugins"].items():
        response[action].append({"destination" : data["recvNick"], "message" : "%s >> %s" % (pluginName, description)})
    return response
