import threading, os, time, urllib.request, json, glob, urllib.parse
from traceback import format_exc
from datetime import datetime

def about():
    return "Gets various data on last.fm users. !lastfm"

def onRegistration(config, welcome, keepAlive):
    if config["lastfm_rss"]["autoannounce"].lower() == "true":
        if " " in config["lastfm_rss"]["username"]:
            usernames = config["lastfm_rss"]["username"].split()
        else:
            usernames = [config["lastfm_rss"]["username"]]
        apikey = config["lastfm_rss"]["apikey"]
        threads = []
        for username in usernames:
            threads.append(threading.Thread(target = dataLoop, args = (config, username, apikey, keepAlive), daemon = True))
        for thread in threads:
            thread.start()
        
def dataLoop(config, username, apikey, keepAlive):
    while 1:
        try:
            response = urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=" + username + "&api_key=" + apikey + "&limit=1&format=json")
            unparsed = response.read()
            parsed = json.loads(unparsed.decode("utf-8"))
            if type(parsed["recenttracks"]["track"]) == list:
                currenttrack = parsed["recenttracks"]["track"][1]["artist"]["#text"] + " - "  + parsed["recenttracks"]["track"][1]["name"]
            else:
                currenttrack = parsed["recenttracks"]["track"]["artist"]["#text"] + " - "  + parsed["recenttracks"]["track"]["name"]
            if not os.path.exists(os.getcwd() + "/plugins/data/" + config["Profile"]["name"]):
                os.makedirs(os.getcwd() + "/plugins/data/" + config["Profile"]["name"])
            if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_pasttracks_" + username):
                datafile = open("plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_pasttracks_" + username, "w", encoding="utf-8")
                datafile.close()
            if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username):
                datafile = open("plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username, "w", encoding="utf-8")
                datafile.close()
            else:
                with open("plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_pasttracks_" + username, "r", encoding="utf-8") as datafile:
                    lasttrack = datafile.read()
                    #print("last: " + lasttrack)
                    
            if currenttrack != lasttrack:
                #print("new: " + currenttrack)
                with open("plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_pasttracks_" + username, "w", encoding="utf-8") as datafile:
                    datafile.write(currenttrack)
                with open("plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username, "w", encoding="utf-8") as datafile:
                    datafile.write(currenttrack)
        except KeyError:
            print(parsed)
        except:
            if "WinError 10060" in str(format_exc()):
                print("Connection to last.fm timed out.")
            else:
                print(str(format_exc()))
                print(parsed)
            pass
        if keepAlive.empty():
            break
        time.sleep(15)
    
def on10Tick(config, data, keepAlive):
    if config["lastfm_rss"]["autoannounce"].lower() == "true":
        time.sleep(1)
        if " " in config["lastfm_rss"]["username"]:
            usernames = config["lastfm_rss"]["username"].split()
        else:
            usernames = [config["lastfm_rss"]["username"]]
        response = {}
        response["PRIVMSG"] = []
        toAnnounce = []
        if not os.path.exists(os.getcwd() + "/plugins/data/" + config["Profile"]["name"]):
            os.makedirs(os.getcwd() + "/plugins/data/" + config["Profile"]["name"])
        announceFiles = glob.glob(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_*")
        #print(announceFiles)
        for username in usernames:
            #print(username)
            if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username):
                datafile = open("plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username, "w", encoding="utf-8")
                datafile.close()
            elif os.path.getsize(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username) > 2:
                with open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username, "r", encoding="utf-8") as datafile:
                    #print("announce: " + username + " just listened to " + datafile.read()) 
                    response["PRIVMSG"].append({"destination" : config["Bot"]["mainchannel"], "message" : "11" + username + " just listened to " + datafile.read()})
                datafile = open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/lastfm_rss_announce_" + username, "w", encoding="utf-8")
                datafile.close()
        if response["PRIVMSG"] == []:
            return None
        else:
            return response
            
def onPRIVMSG(config, data, keepThreads):
    recvNick = data["recvNick"]
    error = 0
    active = 0
    toChannel = 0
    
    if data["message"] == "!help lastfm" or data["message"] == "!lastfm":
        active = 1
        lines_to_send = []
        lines_to_send.append("=======last.fm======================================================================")
        lines_to_send.append("11!lastfm <username> >> Returns what the user is currently listening to.")
        lines_to_send.append("11!lastfm <username> info >> Returns profile info of a user.")
        lines_to_send.append("11!lastfm <username> toptracks [7day|1month|3month|6month|12month] >> Returns a user's top 10 most listened to tracks.")
        lines_to_send.append("11!lastfm <username> topartists [7day|1month|3month|6month|12month] >> Returns a user's top 10 most listened to artists.")
        lines_to_send.append("11!lastfm <username> topalbums [7day|1month|3month|6month|12month] >> Returns a user's top 10 most listened to albums.")
        lines_to_send.append("11!lastfm <username> recenttracks >> Returns a user's top 10 most recently listened to tracks.")
        if config["lastfm_rss"]["aliases"].lower() == "true":
            lines_to_send.append("11!lastfm set <username> >> Associate your nickname with a Last.fm username.")
        lines_to_send.append("All time periods are optional. Default is 7day.")
        lines_to_send.append("====================================================================================")
        
    message = data["message"].split(" ")
    apikey = config["lastfm_rss"]["apikey"]
    
    if len(message) == 2 and message[0].lower() == "!lastfm": # Now playing of user requested.
        active = 1
        nick = message[1]
        username = check_aliases(config, nick)
        url = ("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=" + username + "&api_key=" + apikey + "&format=json&limit=1")
        response = urllib.request.urlopen(url)
        unparsed = response.read()
        parsed = json.loads(unparsed.decode("utf-8"))
        lines_to_send = []
        try:
                lines_to_send.append("11Error %s: %s" % (str(parsed["error"]), parsed["message"]))
                error = 1
        except KeyError:
            try:
                if parsed["recenttracks"]["total"] == "0":
                    lines_to_send.append("11%s has never scrobbled a song." % username)
            except:
                if parsed["recenttracks"]["@attr"]["total"] != "0":
                    if type(parsed["recenttracks"]["track"]) == list:
                        track = parsed["recenttracks"]["track"][0]
                    else:
                        track = parsed["recenttracks"]["track"]
                    try:
                        np = track["@attr"]["nowplaying"]
                        np = 1
                    except KeyError:
                        np = 0
                    artist = track["artist"]["#text"]
                    title = track["name"]
                    if not np:
                        lastlisten = track["date"]["#text"]
                    response = urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?method=track.getinfo&username=" + username + "&api_key=" + apikey + "&format=json&artist=" + urllib.parse.quote_plus(artist) + "&track=" + urllib.parse.quote_plus(title))
                    unparsed = response.read()
                    parsed = json.loads(unparsed.decode("utf-8"))
                    try:
                        lines_to_send.append("11Error %s: %s" % (str(parsed["error"]), parsed["message"]))
                        error = 1
                    except KeyError:
                        toChannel = 1
                        seconds = int(parsed["track"]["duration"])/1000
                        hours = str(int(seconds/3600))
                        minutes = str(int((seconds - 3600*int(hours))/60))
                        seconds = str(int((seconds - 3600*int(hours) - 60*int(minutes))))
                        if len(minutes) == 1:
                            minutes = "0" + minutes
                        if len(seconds) == 1:
                            seconds = "0" + seconds
                        if hours == "0":
                            duration = "%s:%s" % (minutes, seconds)
                        else:
                            if len(hours) == 1:
                                hours = "0" + hours
                            duration = "%s:%s:%s" % (hours, minutes, seconds)
                        tags = []
                        try:
                            if type(parsed["track"]["toptags"]["tag"]) == list:
                                for tag in parsed["track"]["toptags"]["tag"]:
                                    tags.append(tag["name"])
                                tags = "/".join(tags)
                            elif type(parsed["track"]["toptags"]["tag"]) == dict:
                                tags = parsed["track"]["toptags"]["tag"]["name"]
                            else:
                                tags = "no tags"
                        except TypeError:
                            tags = "no tags"
                        loved = int(parsed["track"]["userloved"])
                        try:
                            playcount = parsed["track"]["userplaycount"]
                        except KeyError:
                            playcount = "0"
                        if playcount != "1":
                            playcount = playcount + " plays"
                        else:
                            playcount = playcount + " play"
                    if np and loved:
                        lines_to_send.append("11%s is currently listening to: 14%s - %s 8[13♥8 - %s - %s - %s]" % (nick, artist, title, duration, playcount, tags))
                    elif np:
                        lines_to_send.append("11%s is currently listening to: 14%s - %s 8[%s - %s - %s]" % (nick, artist, title, duration, playcount, tags))
                    elif loved:
                        lines_to_send.append("11%s last listened to: 14%s - %s 8[13♥8 - %s - %s - %s - %s]" % (nick, artist, title, duration, playcount, tags, lastlisten))
                    else:
                        lines_to_send.append("11%s last listened to: 14%s - %s 8[%s - %s - %s - %s]" % (nick, artist, title, duration, playcount, tags, lastlisten))
    
    if len(message) == 3 and message[0].lower() == "!lastfm" and message[2].lower() == "info": # General info about a user requested
        active = 1
        username = check_aliases(config, message[1])
        response = urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user=" + username + "&api_key=" + apikey + "&format=json")
        unparsed = response.read()
        parsed = json.loads(unparsed.decode("utf-8"))
        lines_to_send = []
        try:
            lines_to_send.append("11Error %s: %s" % (str(parsed["error"]), parsed["message"]))
            error = 1
        except KeyError:
            lines_to_send.append("=======last.fm info for: %s%s" % (nick, "=" * (59 - len(nick))))
            lines_to_send.append("11Username: %s" % parsed["user"]["name"])
            # Loads of KeyErrors may occur if the profile is not fully filled in, or hidden.
            try:
                lines_to_send.append("11Real name: %s" % parsed["user"]["realname"])
            except KeyError:
                pass
            lines_to_send.append("11ID: %s" % parsed["user"]["id"])
            try:
                lines_to_send.append("11Country: %s" % parsed["user"]["country"])
            except KeyError:
                pass
            try:
                lines_to_send.append("11Age: %s" % parsed["user"]["age"])
            except KeyError:
                pass
            try:
                if parsed["user"]["gender"] == "m":
                    gender = "Male"
                else:
                    gender = "Female" # No, there are no other options. Go back to Tumblr.
                lines_to_send.append("11Gender: %s" % gender)
            except KeyError:
                pass
            try:
                lines_to_send.append("11Play count: %s" % parsed["user"]["playcount"])
            except KeyError:
                pass
            try:
                lines_to_send.append("11Playlists: %s" % parsed["user"]["playlists"])
            except KeyError:
                pass
            try:
                lines_to_send.append("11Registered since: %s" % parsed["user"]["registered"]["#text"])
            except KeyError:
                pass
            try:
                not0 = ""
                if parsed["user"]["subscriber"] == "0":
                    not0 = "not "
                lines_to_send.append("11%s is %sa subscriber." % (parsed["user"]["name"], not0))
            except KeyError:
                pass
            try:
                lines_to_send.append("11%s" % parsed["user"]["url"])
            except KeyError:
                pass
            lines_to_send.append("====================================================================================")
            
    elif len(message) >= 3 and message[0].lower() == "!lastfm" and message[1].lower() != "set":
        active = 1
        periods = {"overall" : None, "7day" : "week", "1month" : "month", "3month" : "3 months", "6month" : "6 months", "12month" : "year"}
        username = check_aliases(config, message[1])
        lines_to_send = []
        options = {"toptracks" : "track", "topartists" : "artist", "topalbums" : "album"}
        option = message[2].lower()
        if len(message) == 4 and message[3] in periods:
                period = message[3]
        else:
            period = "7day"
        if option in options:
            response = urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.get%s&user=%s&period=%s&limit=10&api_key=%s&format=json" % (option, username, period, apikey))
            unparsed = response.read()
            parsed = json.loads(unparsed.decode("utf-8"))
            try:
                lines_to_send.append("11Error %s: %s" % (str(parsed["error"]), parsed["message"]))
                error = 1
            except KeyError:
                songs = {}
                if parsed[option]["@attr"]["total"] != "0":
                    try:
                        lines_to_send.append("=======last.fm======================================================================")
                        for track in parsed[option][options[option]]:
                            if option == "topartists":
                                songs[int(track["@attr"]["rank"])] = "11%s - %s plays" % (track["name"], track["playcount"])
                            else:
                                songs[int(track["@attr"]["rank"])] = "11%s - %s - %s plays" % (track["artist"]["name"], track["name"], track["playcount"])
                        ordered = []
                        if period == "overall":
                            lines_to_send.append("11%s's top %s since they first used last.fm:" % (parsed[option]["@attr"]["user"], options[option] + "s"))
                        else:
                            lines_to_send.append("11%s's top %s over the last %s:" % (parsed[option]["@attr"]["user"], options[option] + "s", periods[period]))
                        for n in range(1, len(songs) + 1):
                            lines_to_send.append("11%s. %s" % (n, songs[n]))
                        lines_to_send.append("====================================================================================")
                    except KeyError:
                        print(format_exc())
                        lines_to_send.append("11Error: failed to retrieve list.")
                        error = 1
                else:
                    lines_to_send.append("11Error: last.fm returned no %ss." % options[option])
                    
        elif option == "recenttracks":
            response = urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&period=%s&limit=10&api_key=%s&format=json" % (username, period, apikey))
            print("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&limit=10&api_key=%s&format=json" % (username, apikey))
            unparsed = response.read()
            parsed = json.loads(unparsed.decode("utf-8"))
            try:
                lines_to_send.append("11Error %s: %s" % (str(parsed["error"]), parsed["message"]))
                error = 1
            except KeyError:
                songs = {}
                if parsed[option]["@attr"]["total"] != "0":
                    try:
                        lines_to_send.append("=======last.fm======================================================================")
                        for track in parsed["recenttracks"]["track"]:
                            np = ""
                            try:
                                np = track["@attr"]["nowplaying"]
                                np = " - Now playing!"
                                songs[0] = "11%s - %s%s" % (track["artist"]["#text"], track["name"], np)
                            except KeyError:
                                songs[int(track["date"]["uts"])] = "11%s - %s%s" % (track["artist"]["#text"], track["name"], np)
                        ordered = []
                        for time in songs.keys():
                            ordered.append(time)
                        ordered.sort(reverse=True)
                        if 0 in ordered:
                            del ordered[-1]
                            ordered = [0] + ordered
                        print(ordered)
                        lines_to_send.append("11%s most recently listened to:" % parsed[option]["@attr"]["user"])
                        for n in range(1, len(songs) + 1):
                            lines_to_send.append("11%s. %s" % (n, songs[ordered[n-1]]))
                        lines_to_send.append("====================================================================================")
                    except KeyError:
                        print(format_exc())
                        lines_to_send.append("11Error: failed to retrieve list.")
                        error = 1
                else:
                    lines_to_send.append("11Error: last.fm returned no %ss." % options[option])
                    
    elif len(message) == 3 and message[0].lower() == "!lastfm" and message[1].lower() == "set":
        lines_to_send = []
        toChannel = True
        active = 1
        status = add_alias(config, recvNick, message[2])
        if status == 0:
            lines_to_send.append("11%s can now be referred to as %s." % (message[2], recvNick))
        elif status == 1:
            toChannel = False
            lines_to_send.append("11Error: aliases are not enabled.")

    if active == 1:
        if data["isPM"] or toChannel:
            action = "PRIVMSG"
        else:
            action = "NOTICE"
        if toChannel:
            recvNick = data["destination"]
        if error == 1:
            respond = {}
            respond[action] = {"destination" : recvNick, "message" : lines_to_send[0]}
        else:
            respond = {}
            respond[action] = []
            for line in lines_to_send:
                respond[action].append({"destination" : recvNick, "message" : line})
        return respond
        
def check_aliases(config, name):
    if config["lastfm_rss"]["aliases"].lower() == "true":
        if not os.path.exists(os.getcwd() + "/plugins/data/" + config["Profile"]["name"]):
            os.makedirs(os.getcwd() + "/plugins/data/" + config["Profile"]["name"])
        if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases"):
            open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases", "w").close()
            return name
        
        aliases = {}
        with open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases", "r") as file:
            for line in file.readlines():
                aliases[line.split("=")[0]] = line.split("=")[1][:-1]
        if name in aliases:
            return aliases[name]
        else:
            return name
    else:
        return name
        
def add_alias(config, alias, username):
    if config["lastfm_rss"]["aliases"].lower() == "true":
        if not os.path.exists(os.getcwd() + "/plugins/data/" + config["Profile"]["name"]):
            os.makedirs(os.getcwd() + "/plugins/data/" + config["Profile"]["name"])
        if not os.path.isfile(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases"):
            open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases", "w").close()
        
        aliases = {}
        with open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases", "r") as file:
            for line in file.readlines():
                aliases[line.split("=")[0]] = line.split("=")[1]
                
        aliases[alias] = username
        
        with open(os.getcwd() + "/plugins/data/" + config["Profile"]["name"] + "/aliases", "w") as file:
            for i, j in aliases.items():
                file.write("%s=%s\n" % (i, j))
        return 0
    else:
        return 1
