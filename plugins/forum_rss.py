import threading, os, time, urllib.request, feedparser, glob, urllib.parse
import xml.etree.ElementTree as etree  
from traceback import format_exc
from datetime import datetime

def about():
    return "Posts new forum threads in to the IRC channel."
    
def onRegistration(config, welcome, keepAlive):
    if config["forum_rss"]["enable"].lower() == "true":
        urls = config["forum_rss"]["urls"].split(",")
        channel = config["Bot"]["mainchannel"]
        if config["forum_rss"]["shrinkurls"].lower() == "true":
            shrink = True
        else:
            shrink = False
        threads = []
        threads.append(threading.Thread(target = dataLoop, args = (config, urls, shrink, keepAlive), daemon = True))
        for thread in threads:
            thread.start()

def dataLoop(config, urls, shrink, keepAlive):
    while 1:
        threads = {}
        lines_to_send = []
        for url in urls:
            parsed = feedparser.parse(url)
            for thread in parsed["entries"]:
                threads[thread["title"]] = thread["link"]
        if not os.path.exists(os.getcwd() + "/plugins/data/" + config["Profile"]["name"]):
            os.makedirs(os.getcwd() + "/plugins/data/" + config["Profile"]["name"])
        if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/forum_rss_past"):
                datafile = open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_past", "w", encoding="utf-8")
                datafile.close()
        if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/forum_rss_announce"):
                datafile = open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_announce", "w", encoding="utf-8")
                datafile.close()
                
        pastThreads = []
        with open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_past", "r") as datafile:
            for line in datafile.readlines():
                pastThreads.append(line[:-1])
        with open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_announce", "r") as datafile:
            for line in datafile.readlines():
                if line != "" and line != "\n":
                    pastThreads.append(line.split("	")[1][:-1])
                
        for title, threadurl in threads.items():
            if threadurl not in pastThreads:
                link = threadurl
                if shrink:
                    shortenerURL = "http://is.gd/create.php?format=simple&url=%s" % urllib.parse.quote_plus(threadurl)
                    slink = urllib.request.urlopen(shortenerURL)
                    link = slink.read()
                #lines_to_send.append("New forum thread: %s [%s]	%s" % (title, link, threadurl))
                with open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_past", "a", encoding="utf-8") as datafile:
                    datafile.write(threadurl + "\n")
                with open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_announce", "a", encoding="utf-8") as datafile:
                    datafile.write("4New forum thread: 14%s 8[%s]	%s\n" % (title, link.decode(), threadurl))
        time.sleep(30)
        
def on10Tick(config, data, keepAlive):
    response = None
    if config["forum_rss"]["enable"].lower() == "true":
        lines_to_send = []
        response = {"PRIVMSG" : []}
        with open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_announce", "r") as datafile:
            for line in datafile:
                if line != "\n" and line != "":
                    lines_to_send.append(line.split("	")[0])
        f = open("plugins/data/" + config["Profile"]["name"] + "/forum_rss_announce", "w", encoding="utf-8")
        f.close()
        for line in lines_to_send:
            #print(line)
            response["PRIVMSG"].append({"destination" : config["Bot"]["mainchannel"], "message" : line})
    return response
