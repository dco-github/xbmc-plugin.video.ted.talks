import sys
import urllib
import ted_talks_scraper
import ted_talks_rss
from talkDownloader import Download
import fetcher
import user
import menu_util
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.ted.talks')
getLS = __settings__.getLocalizedString

#getLS = xbmc.getLocalizedString
Fetcher = fetcher.Fetcher(xbmc.translatePath)

class UI:

    def __init__(self, ted_talks, settings, args):
        self.ted_talks = ted_talks
        self.settings = settings
        self.args = args
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

    def endofdirectory(self, sortMethod = 'title'):
        # set sortmethod to something xbmc can use
        if sortMethod == 'title':
            sortMethod = xbmcplugin.SORT_METHOD_LABEL
        elif sortMethod == 'date':
            sortMethod = xbmcplugin.SORT_METHOD_DATE
        #Sort methods are required in library mode.
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod)
        #let xbmc know the script is done adding items to the list.
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]), updateListing = True)

    def addItem(self, info, isFolder = True):
        #Defaults in dict. Use 'None' instead of None so it is compatible for quote_plus in parseArgs
        info.setdefault('url', 'None')
        info.setdefault('Thumb', 'None')
        info.setdefault('Icon', info['Thumb'])
        #create params for xbmcplugin module
        u = sys.argv[0]+\
            '?url='+urllib.quote_plus(info['url'])+\
            '&mode='+urllib.quote_plus(info['mode'])+\
            '&name='+urllib.quote_plus(info['Title'].encode('ascii','ignore'))+\
            '&icon='+urllib.quote_plus(info['Thumb'])            
        #create list item
        if info['Title'].startswith(" "):
            title = info['Title'][1:]
        else:
            title = info['Title']  
        li = xbmcgui.ListItem(label = title, iconImage = info['Icon'], thumbnailImage = info['Thumb'])
        li.setInfo(type='Video', infoLabels = info)
        #for videos, replace context menu with queue and add to favorites
        if not isFolder:
            li.setProperty("IsPlayable", "true")#let xbmc know this can be played, unlike a folder.
            context_menu = menu_util.create_context_menu(getLS = getLS)
            li.addContextMenuItems(context_menu, replaceItems = True)
        else:
            #for folders, completely remove contextmenu, as it is totally useless.
            li.addContextMenuItems([], replaceItems = True)
        #add item to list
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=isFolder)

    def addItems(self, items):
        """
        items Iterable of 2-tuples, first value is whether this is a folder, second is a string->string dict of attributes
        """
        for item in items:
            self.addItem(item[1], isFolder = item[0])
        #end the list
        self.endofdirectory(sortMethod = 'date')

    def playVideo(self):
        video = self.ted_talks.getVideoDetails(self.args.url)
        li=xbmcgui.ListItem(video['Title'],
                            iconImage = self.args.icon,
                            thumbnailImage = self.args.icon,
                            path = video['url'])
        li.setInfo(type='Video', infoLabels=video)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

    def navItems(self, navItems, mode):
        if navItems['next']:
            self.addItem({'Title': getLS(30020), 'url':navItems['next'], 'mode':mode})
        if navItems['previous']:
            self.addItem({'Title': getLS(30021), 'url':navItems['previous'], 'mode':mode})

    def showCategories(self):
        self.addItem({'Title':getLS(30001) + ' (deprecated old style)', 'mode':'newTalks', 'Plot':getLS(30031)})#new
        self.addItem({'Title':getLS(30001), 'mode':'newTalksRss', 'Plot':getLS(30031)})#new RSS
        self.addItem({'Title':getLS(30002), 'mode':'speakers', 'Plot':getLS(30032)})#speakers
        self.addItem({'Title':getLS(30003), 'mode':'themes', 'Plot':getLS(30033)})#themes
        #self.addItem({'Title':getLS(30004), 'mode':'search', 'Plot':getLS(30034)})#search
        if self.settings['username']:
            self.addItem({'Title':getLS(30005), 'mode':'favorites', 'Plot':getLS(30035)})#favorites
        self.endofdirectory()

    def newTalks(self):
        newTalks = ted_talks_scraper.NewTalks(Fetcher.getHTML, getLS)
        talks = newTalks.getNewTalks(self.args.url)
        self.addItems(talks)
        
    def newTalksRss(self):
        newTalks = ted_talks_rss.NewTalksRss()
        for talk in newTalks.getNewTalks():
            li = xbmcgui.ListItem(label = talk['title'], iconImage = talk['thumb'], thumbnailImage = talk['thumb'])
            li.setProperty("IsPlayable", "true")
            li.setInfo('video', {'date':talk['date'], 'duration':talk['duration'], 'plot':talk['plot']})
            favorites_action = None
            if self.settings['username'] != None:
                favorites_action = "add"
            context_menu = menu_util.create_context_menu(getLS = getLS, url = talk['link'], favorites_action = favorites_action, talkID = talk['id'])
            li.addContextMenuItems(context_menu, replaceItems = True)
            xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = talk['link'], listitem = li)
        self.endofdirectory(sortMethod = 'date')

    def speakers(self):
        newMode = 'speakerVids'
        speakers = self.ted_talks.Speakers(Fetcher, self.args.url)
        #add speakers to the list
        for speaker in speakers.getAllSpeakers():
            speaker['mode'] = newMode
            self.addItem(speaker, isFolder = True)
        #add nav items to the list
        self.navItems(speakers.navItems, self.args.mode)
        #end the list
        self.endofdirectory()

    def speakerVids(self):
        newMode = 'playVideo'
        speakers = self.ted_talks.Speakers(Fetcher, self.args.url)
        for talk in speakers.getTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        #end the list
        self.endofdirectory()

    def themes(self):
        newMode = 'themeVids'
        themes = self.ted_talks.Themes(Fetcher, self.args.url)
        #add themes to the list
        for theme in themes.getThemes():
            theme['mode'] = newMode
            self.addItem(theme, isFolder = True)
        #end the list
        self.endofdirectory()

    def themeVids(self):
        newMode = 'playVideo'
        themes = self.ted_talks.Themes(Fetcher, self.args.url)
        for talk in themes.getTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        self.endofdirectory()

    def favorites(self):
        newMode = 'playVideo'
        #attempt to login
        if self.isValidUser():
            for talk in self.ted_talks.Favorites(Fetcher, self.logger).getFavoriteTalks(self.main.user):
                talk['mode'] = newMode
                self.addItem(talk, isFolder = False)
            self.endofdirectory()


class Main:

    def __init__(self, logger, args_map):
        self.logger = logger
        self.args_map = args_map
        self.user = None
        self.getSettings()
        self.ted_talks = ted_talks_scraper.TedTalks(Fetcher.getHTML)

    def getSettings(self):
        self.settings = dict()
        self.settings['username'] = __settings__.getSetting('username')
        self.settings['password'] = __settings__.getSetting('password')
        self.settings['downloadMode'] = __settings__.getSetting('downloadMode')
        self.settings['downloadPath'] = __settings__.getSetting('downloadPath')

    def isValidUser(self):
        self.user = user.User(Fetcher.getHTML, self.settings['username'], self.settings['password'])
        if self.user:
            return True
        else:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
            return False

    def addToFavorites(self, talkID):
        if self.isValidUser():
            successful = self.ted_talks.Favorites(self.logger).addToFavorites(self.user, talkID)
            if successful:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30091)))
            else:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30092)))

    def removeFromFavorites(self, talkID):
        if self.isValidUser():
            successful = self.ted_talks.Favorites(self.logger).removeFromFavorites(self.user, talkID)
            if successful:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30094)))
            else:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30095)))

    def downloadVid(self, url):
        video = self.ted_talks.getVideoDetails(url)
        if self.settings['downloadMode'] == 'true':
            downloadPath = xbmcgui.Dialog().browse(3, getLS(30096), 'files')
        else:
            downloadPath = self.settings['downloadPath']
        if downloadPath:
            Download(video['Title'], video['url'], downloadPath)

    def run(self):
        if 'addToFavorites' in self.args_map:
            self.addToFavorites(self.args_map['addToFavorites'])
        if 'removeFromFavorites' in self.args_map:
            self.removeFromFavorites(self.args_map['removeFromFavorites'])
        if 'downloadVideo' in self.args_map:
            self.downloadVid(self.args_map('downloadVideo'))
        
        ui = UI(self.ted_talks, self.settings, self.args_map)
        if 'mode' not in self.args_map:
            ui.showCategories()
        else:
            mode = self.args_map['mode']
            if mode == 'playVideo':
                ui.playVideo()
            elif mode == 'newTalks':
                ui.newTalks()
            elif mode == 'newTalksRss':
                ui.newTalksRss()
            elif mode == 'speakers':
                ui.speakers()
            elif mode == 'speakerVids':
                ui.speakerVids()
            elif mode == 'themes':
                ui.themes()
            elif mode == 'themeVids':
                ui.themeVids()
            elif mode == 'favorites':
                ui.favorites()
