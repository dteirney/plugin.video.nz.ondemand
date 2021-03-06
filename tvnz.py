import tools, urllib, urllib2, htmllib, string, unicodedata, os, re, sys, time, urlparse, cgi, xbmc, xbmcgui, xbmcplugin, xbmcaddon
from datetime import date
from xml.dom import minidom

addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])
localize = addon.getLocalizedString

BASE_URL = 'http://tvnz.co.nz'
FANART_URL = 'resources/images/TVNZ.jpg'
MIN_BITRATE = 400000

def INDEX():
 link = tools.gethtmlpage("%s/content/ps3_navigation/ps3_xml_skin.xml" % (BASE_URL), "ps3")
 if link:
  count = 0
  node = tools.getxmldocument(link)
  if node:
   for stat in node.getElementsByTagName('MenuItem'):
    type = stat.attributes["type"].value
    if type in ('shows', 'alphabetical'): #, 'distributor'
     m = re.search('/([0-9]+)/',stat.attributes["href"].value)
     if m:
      info = tools.defaultinfo(1)
      info["Title"] = stat.attributes["title"].value
      info["Count"] = count
      count += 1
      info["FileName"] = "%s?ch=TVNZ&type=%s&id=%s" % (sys.argv[0], type, m.group(1))
      tools.addlistitem(int(sys.argv[1]), info, FANART_URL, 1)

def SHOW_LIST(id):
 link = tools.gethtmlpage("%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id), "ps3")
 node = tools.getxmldocument(link)
 if node:
  urls = list()
  count = 0
  infoitems = {}
  for show in node.getElementsByTagName('Show'):
   se = re.search('/content/(.*)_(episodes|extras)_group/ps3_xml_skin.xml', show.attributes["href"].value)
   if se:
    if se.group(2) == "episodes":
     #videos = int(show.attributes["videos"].value)
     #channel = show.attributes["channel"].value
     info = tools.defaultinfo(1)
     info["FileName"] = "%s?ch=TVNZ&type=singleshow&id=%s_episodes_group" % (sys.argv[0], se.group(1))
     info["Title"] = show.attributes["title"].value
     info["Count"] = count
     count += 1
     infoitems[info["Title"]] = info
  tools.addlistitems(int(sys.argv[1]), infoitems, FANART_URL, 1)


def SHOW_DISTRIBUTORS(id):
 link = tools.gethtmlpage("%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id), "ps3")
 if link:
  node = tools.getxmldocument(link)
  if node:
   print node.toxml().encode('latin1')
   urls = list()
   for distributor in node.getElementsByTagName('Distributor'):
    url,liz = getShow(distributor)
    if not urls.count(url):
     xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=True )
     urls.append(url)

def SHOW_EPISODES(id):
 getEpisodes(id, "%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id))
 link = tools.gethtmlpage("%s/content/%s_extras_group/ps3_xml_skin.xml" % (BASE_URL, id[:-15]), "ps3")
 if link:
  node = tools.getxmldocument(link)
  if node:
   info = tools.defaultinfo(1)
   info["FileName"] = "%s?ch=TVNZ&type=shows&id=%s_extras_group" % (sys.argv[0], id[:-15])
   info["Title"] = "Extras"
   tools.addlistitem(int(sys.argv[1]), info, FANART_URL, 1)
 return

def getEpisodes(id, url):
 link = tools.gethtmlpage(url, "ps3")
 if link:
  node = tools.getxmldocument(link)
  if node:
   for ep in node.getElementsByTagName('Episode'):
    addEpisode(ep)
   for ep in node.getElementsByTagName('Extra'):
    addEpisode(ep)

def EPISODE_LIST(id):
 getEpisodes(id, "%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id,))

def getDuration(dur):
 # Durations are formatted like 0:43:15
 minutes = 0
 parts = dur.split(":")
 if len(parts) == 3:
  minutes = int(parts[0]) * 60 + int(parts[1])
 return str(minutes)

def getDate(str):
 # Dates are formatted like 23 Jan 2010 OR 23 Jan 11
 # Can't use datetime.strptime as that wasn't introduced until Python 2.6
 months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
 months2 = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
 str = str.encode('ascii', 'replace') # Part of the dates include the NO BREAK character \xA0 instead of a space
 str = str.replace("?", " ")
 parts = str.split(" ")
 if len(parts) == 3:
  if parts[1] in months:
   month = months.index(parts[1])
  elif parts[1] in months2:
   month = months2.index(parts[1])
  if month:
   year = int(parts[2])
   if year < 99: # in case the year is just 2 digits assuming 20xx.
    year += 2000
   d = date(year, month + 1, int(parts[0]))
   return d.strftime("%d.%m.%Y")
 return ""

def getShow(show):
 se = re.search('/content/(.*)_(episodes|extras)_group/ps3_xml_skin.xml', show.attributes["href"].value)
 if se:
  info = tools.defaultinfo(1)
  info["FileName"] = "%s?ch=TVNZ&type=singleshow&id=%s_episodes_group" % (sys.argv[0], se.group(1))
  info["Title"] = show.attributes["title"].value
  #if "videos" in show.attributes.keys():
  # videos = int(show.attributes["videos"].value)
  #else:
  # videos = 0
  #channel = show.attributes["channel"].value
  #url = "%s?ch=TVNZ&type=singleshow&id=%s_episodes_group" % (sys.argv[0],show_id)
  tools.addlistitem(int(sys.argv[1]), info, FANART_URL, 1)

def getEpisode(ep):
 info = tools.defaultinfo(0)
 
 title = ep.attributes["title"].value
 subtitle = ep.attributes["sub-title"].value
 if len(subtitle) == 0:
  titleparts = title.split(': ') # Some Extras have the Title and Subtitle put into the title attribute separated by ': '
  if len(titleparts) == 2:
   title = titleparts[0]
   subtitle = titleparts[1]

 season = 0
 episode = 1
 episodeparts = string.split(ep.attributes["episode"].value, '|')
 if len(episodeparts) == 3:
  se = re.search('Series ([0-9]+), Episode ([0-9]+)', episodeparts[0].strip())
  if se:
   season = int(se.group(1))
   episode = int(se.group(2))
   # Adjust the subtitle to include the season and episode numbers.
   if len(subtitle):
    subtitle = str(season) + "x" + str(episode) + " " + subtitle
   else:
    subtitle = str(season) + "x" + str(episode)
  elif len(subtitle) == 0:
    subtitle = episodeparts[0].strip() # E.g. "Coming Up" or "Catch Up"
  info["Date"] = getDate(episodeparts[1].strip())
  info["Premiered"] = episodeparts[1].strip()
  info["Duration"] = getDuration(episodeparts[2].strip())

 info["TVShowTitle"] = title
 info["Title"] = subtitle
 info["Season"]  = season
 info["Episode"] = episode
 
 #channel = ep.attributes["channel"].value
 info["Thumb"] = ep.attributes["src"].value

 if len(info["Title"]):
  label = "%s - \"%s\"" % (info["TVShowTitle"], info["Title"],)
 else:
  label = info["TVShowTitle"]
 info["Title"] = label
 if ep.firstChild:
  info["Plot"] = ep.firstChild.data
 info["FileName"] = "%s?ch=TVNZ&type=video&id=%s&info=%s" % (sys.argv[0], ep.attributes["href"].value, urllib.quote(str(info)))
 return(info)

def addEpisode(ep):
 #url,liz = getEpisode(ep)
 #xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
 tools.addlistitem(int(sys.argv[1]), getEpisode(ep), FANART_URL, 0)

def getAdvert(chapter):
 advert = chapter.getElementsByTagName('ref')
 if len(advert):
  # fetch the link - it'll return a .asf file
  link = tools.gethtmlpage(advert[0].attributes['src'].value, "ps3")
  if link:
   node = tools.getxmldocument(link)
   if node:
    # grab out the URL to the actual flash ad
    for flv in node.getElementsByTagName('FLV'):
     if flv.firstChild and len(flv.firstChild.wholeText):
      return(flv.firstChild.wholeText)

def RESOLVE(id, info):
 link = tools.gethtmlpage("%s/content/%s/ta_ent_smil_skin.smil?platform=PS3" % (BASE_URL, id), "ps3")
 if link:
  node = tools.getxmldocument(link)
  if node:
   urls=list()
   for chapter in node.getElementsByTagName('seq'):
    # grab out the advert link
    if addon.getSetting('TVNZ_showads') == 'true':
     ad = getAdvert(chapter)
     if len(ad) > 0:
      urls.append(ad)
    maxbitrate = 0
    minbitrate = 9999999999
    for video in chapter.getElementsByTagName('video'):
     bitrate = int(video.attributes["systemBitrate"].value)
     if bitrate > maxbitrate:
      maxbitrate = bitrate
     if bitrate < minbitrate:
      minbitrate = bitrate
    requiredbitrate = 700000 #Medium = 700000
    if addon.getSetting('TVNZ_quality') == "High": #High = 1500000
     requiredbitrate = maxbitrate
    elif addon.getSetting('TVNZ_quality') == "Low": #Low = 300000
     requiredbitrate = minbitrate
    for video in chapter.getElementsByTagName('video'):
     bitrate = int(video.attributes["systemBitrate"].value)
     if bitrate == requiredbitrate:
      url = video.attributes["src"].value
      if url[:7] == 'http://':
       # easy case - we have an http URL
       urls.append(url)
       sys.stderr.write("HTTP URL: " + url)
      elif url[:5] == 'rtmp:':
       # rtmp case
       rtmp_url = "rtmpe://fms-streaming.tvnz.co.nz/tvnz.co.nz"
       playpath = " playpath=" + url[5:]
       flashversion = " flashVer=MAC%2010,0,32,18"
       swfverify = " swfurl=http://tvnz.co.nz/stylesheets/tvnz/entertainment/flash/ondemand/player.swf swfvfy=true"
       conn = " conn=S:-720"
       urls.append(rtmp_url + playpath + flashversion + swfverify + conn)
       sys.stderr.write("RTMP URL: " + rtmp_url + playpath + flashversion + swfverify + conn)
   if len(urls) == 0:
    sys.stderr.write("No playback URLs found!")
    return
  
   if len(urls) == 1:
    uri = urls[0]
   elif len(urls) > 1:
    uri = tools.constructStackURL(urls)
   tools.addlistitem(int(sys.argv[1]), info, FANART_URL, 0, 1, uri)
