#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
****************************************
*        coded by Lululla              *
*           thank's Pcd                *
*             24/04/2022               *
*       skin by MMark                  *
****************************************
Info http://t.me/tivustream
'''
from __future__ import print_function
from . import _
# from Components.HTMLComponent import *
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.FileList import FileList
from Components.Input import Input
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap, MovingPixmap
from Components.PluginComponent import plugins
from Components.PluginList import *
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.SelectionList import SelectionList
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.ServiceList import ServiceList
from Components.Sources.List import List
from Components.Sources.Progress import Progress
from Components.Sources.Source import Source
from Components.Sources.StaticText import StaticText
from Components.config import *
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.InfoBar import InfoBar
from Screens.InfoBar import MoviePlayer
from Screens.InfoBarGenerics import InfoBarShowHide, InfoBarSubtitleSupport, InfoBarSummarySupport, \
	InfoBarNumberZap, InfoBarMenu, InfoBarEPG, InfoBarSeek, InfoBarMoviePlayerSummarySupport, \
	InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.PluginBrowser import PluginBrowser
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop, Standby
from Screens.VirtualKeyBoard import VirtualKeyBoard
from ServiceReference import ServiceReference
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from Tools.Directories import pathExists, fileExists, copyfile
from Tools.Downloader import downloadWithProgress
from Tools.LoadPixmap import LoadPixmap
from enigma import *
from enigma import RT_HALIGN_CENTER, RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT
from enigma import eTimer
from enigma import eListbox, eListboxPythonMultiContent, eConsoleAppContainer
from enigma import iPlayableService
from enigma import iServiceInformation
from enigma import eServiceCenter
from enigma import eServiceReference
from enigma import eSize, ePicLoad
from enigma import loadPNG, gFont
from enigma import quitMainloop
from os.path import splitext
from twisted.web.client import downloadPage, getPage
from xml.dom import Node, minidom
import base64
import glob
import hashlib
import json
import os
import re
import six
import ssl
import sys
import time

PY3 = False
PY3 = sys.version_info.major >= 3
print('Py3: ',PY3)

try:
    import http.cookiejar as cookielib
    from urllib.parse import urlencode
    from urllib.parse import quote
    from urllib.parse import urlparse
    from urllib.request import Request
    from urllib.request import urlopen
    from urllib import request as urllib2
    PY3 = True; unicode = str; unichr = chr; long = int; xrange = range
except:
    import cookielib
    from urllib import urlencode
    from urllib import quote
    from urlparse import urlparse
    from urllib2 import Request
    from urllib2 import urlopen


from . import Utils
if PY3:
    print('six.PY3: True ')

plugin_path = os.path.dirname(sys.modules[__name__].__file__)
global skin_path, revol, pngs, pngl, pngx, file_json, nextmodule, search, pngori, pictmp

search = False
_session = None
UrlSvr = 'aHR0cDov+L3BhdGJ+1d2ViLmN+vbS9pcH+R2Lw=='
UrlSvr = UrlSvr.replace('+', '')
UrlLst = Utils.b64decoder(UrlSvr)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding': 'deflate'}

streamlink = False
if Utils.isStreamlinkAvailable:
    streamlink = True

def trace_error():
    import traceback
    try:
        traceback.print_exc(file=sys.stdout)
        traceback.print_exc(file=open('/tmp/traceback.log', 'a'))
    except:
        pass

def logdata(name = '', data = None):
    try:
        data=str(data)
        fp = open('/tmp/revolution.log', 'a')
        fp.write(str(name) + ': ' + data + "\n")
        fp.close()
    except:
        trace_error()
        pass

def getversioninfo():
    currversion = '1.5'
    version_file = plugin_path + '/version'
    if os.path.exists(version_file):
        try:
            fp = open(version_file, 'r').readlines()
            for line in fp:
                if 'version' in line:
                    currversion = line.split('=')[1].strip()
        except:
            pass
    logdata("Version ", currversion)
    return (currversion)

try:
    from twisted.internet import ssl
    from twisted.internet._sslverify import ClientTLSOptions
    sslverify = True
except:
    sslverify = False

if sslverify:
    class SNIFactory(ssl.ClientContextFactory):
        def __init__(self, hostname=None):
            self.hostname = hostname

        def getContext(self):
            ctx = self._contextFactory(self.method)
            if self.hostname:
                ClientTLSOptions(self.hostname, ctx)
            return ctx

def TvsApi():
    DownUrl = '%s/apigen' %UrlLst
    live = ''
    movie = ''
    series = ''
    other = ''
    try:
        req = Request(DownUrl, None, headers=headers)
        tvs = urlopen(req)
        # print('tvss', str(tvs))
        count = 0
        live = tvs.readline().strip()
        movie = tvs.readline().strip()
        series = tvs.readline().strip()
        other = tvs.readline().strip()
        return live, movie, series, other
    except:
        return live, movie, series, other
        pass

modechoices = [
                ("4097", _("ServiceMp3(4097)")),
                ("1", _("Hardware(1)")),
                ]

if os.path.exists("/usr/bin/gstplayer"):
    modechoices.append(("5001", _("Gstreamer(5001)")))
if os.path.exists("/usr/bin/exteplayer3"):
    modechoices.append(("5002", _("Exteplayer3(5002)")))
if os.path.exists("/usr/sbin/streamlinksrv"):
    modechoices.append(("5002", _("Streamlink(5002)")))
if os.path.exists("/usr/bin/apt-get"):
    modechoices.append(("8193", _("eServiceUri(8193)")))

config.plugins.revolution = ConfigSubsection()
config.plugins.revolution.cachefold = ConfigDirectory(default='/media/hdd/revolution/')
config.plugins.revolution.movie = ConfigDirectory("/media/hdd/movie")
try:
    from Components.UsageConfig import defaultMoviePath
    downloadpath = defaultMoviePath()
    config.plugins.revolution.movie = ConfigDirectory(default=downloadpath)
except:
    if os.path.exists("/usr/bin/apt-get"):
        config.plugins.revolution.movie   = ConfigDirectory(default='/media/hdd/movie/')
config.plugins.revolution.services = ConfigSelection(default='4097', choices = modechoices)
config.plugins.revolution.cachefold = ConfigDirectory("/media/hdd", False)
cfg = config.plugins.revolution

global Path_Movies
Path_Movies             = str(config.plugins.revolution.movie.value)
if Path_Movies.endswith("\/\/"):
    Path_Movies = Path_Movies[:-1]
print('patch movies: ', Path_Movies)

currversion = getversioninfo()
title_plug = '..:: TivuStream Pro Revolution Lite V. %s ::..' % currversion
desc_plug = 'TivuStream Pro Revolution Lite'
ico_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/logo.png".format('revolution'))
no_cover = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/no_coverArt.png".format('revolution'))
res_plugin_path =  resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/".format('revolution'))
pngori = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/fulltop.jpg".format('revolution'))
piccons = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/picons/".format('revolution'))
# ico1_path = res_plugin_path + 'pics/plugin.png'
# ico3_path = res_plugin_path + 'pics/setting.png'
imgjpg = ("nasa1.jpg", "nasa2.jpg", "nasa.jpg", "fulltop.jpg")
piconlive = piccons + 'tv.png'
piconmovie = piccons + 'cinema.png'
piconseries = piccons + 'series.png'
piconsearch = piccons + 'search.png'
piconinter = piccons + 'inter.png'
pixmaps = piccons + 'backg.png'

Path_Tmp = "/tmp"
pictmp = Path_Tmp + "/poster.jpg"
revol = config.plugins.revolution.cachefold.value.strip()
if revol.endswith('\/\/'):
    revol = revol[:-1]
if not os.path.exists(revol):
    try:
        os.makedirs(revol)
    except OSError as e:
        print(('Error creating directory %s:\n%s') % (revol, str(e)))
logdata("path picons: ", str(revol))
if Utils.isFHD():
    skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/skins/fhd/".format('revolution'))
else:
    skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/skins/hd/".format('revolution'))
if Utils.DreamOS():
    skin_path = skin_path + 'dreamOs/'
logdata("path picons: ", str(skin_path))

REGEX = re.compile(
		r'([\(\[]).*?([\)\]])|'
		r'(: odc.\d+)|'
		r'(\d+: odc.\d+)|'
		r'(\d+ odc.\d+)|(:)|'
		r'( -(.*?).*)|(,)|'
		r'!|'
		r'/.*|'
		r'\|\s[0-9]+\+|'
		r'[0-9]+\+|'
		r'\s\d{4}\Z|'
		r'([\(\[\|].*?[\)\]\|])|'
		r'(\"|\"\.|\"\,|\.)\s.+|'
		r'\"|:|'
		r'Премьера\.\s|'
		r'(х|Х|м|М|т|Т|д|Д)/ф\s|'
		r'(х|Х|м|М|т|Т|д|Д)/с\s|'
		r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
		r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
		r'\d{1,3}(-я|-й|\sс-н).+|', re.DOTALL)


class rvList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if Utils.isFHD():
            self.l.setItemHeight(50)
            textfont = int(34)
            self.l.setFont(0, gFont('Regular', textfont))
        else:     
            self.l.setItemHeight(50)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))
        
def rvListEntry(name, idx):
    res = [name]
    if 'radio' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/radio.png".format('revolution'))
    elif 'webcam' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/webcam.png".format('revolution'))
    elif 'music' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/music.png".format('revolution'))
    elif 'sport' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/sport.png".format('revolution'))
    else:
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/tv.png".format('revolution'))
    if Utils.isFHD():
        res.append(MultiContentEntryPixmapAlphaTest(pos =(10, 12), size =(34, 25), png =loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(60, 0), size =(1900, 50), font =0, text=name, color = 0xa6d1fe, flags =RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos =(10, 12), size=(34, 25), png =loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(60, 0), size =(1000, 50), font =0, text =name, color = 0xa6d1fe, flags =RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res

def rvoneListEntry(name):
    res = [name]
    if 'radio' in name.lower():
        pngx = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/radio.png".format('revolution'))
    elif 'webcam' in name.lower():
        pngx = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/webcam.png".format('revolution'))
    elif 'music' in name.lower():
        pngx = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/music.png".format('revolution'))
    elif 'sport' in name.lower():
        pngx = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/sport.png".format('revolution'))
    else:
        pngx = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/tv.png".format('revolution'))
    if Utils.isFHD():
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 12), size=(34, 25), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(60, 0), size=(1900, 50), font=0, text=name, color = 0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 12), size=(34, 25), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(60, 0), size=(1000, 50), font=0, text=name, color = 0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res

def showlist(data, list):
    icount = 0
    plist = []
    for line in data:
        name = data[icount]
        plist.append(rvoneListEntry(name))
        icount = icount+1
        list.setList(plist)

PanelMain = [
 ('SEARCH'),
 ('LIVE'),
 ('MOVIE'),
 ('SERIES'),
 ('INTERNATIONAL'),]

class Revolmain(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        # self.setTitle(title_plug)
        global nextmodule
        nextmodule = 'revolmain'
        self['text'] = rvList([])
        self.setup_title = ('HOME REVOLUTION')
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['poster'] = Pixmap()
        self['desc'] = StaticText()
        self['space'] = Label('')
        self['info'] = Label('')
        self['info'].setText(_('Loading data... Please wait'))
        self['key_green'] = Button(_('Select'))
        self['key_red'] = Button(_('Exit'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['progresstext'].text = ''
        self.currentList = 'text'
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.idx = 0
        self.menulist = []
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['SetupActions', 'DirectionActions', "EPGSelectActions", 'ColorActions', "MenuActions"], {'ok': self.okRun,
         'green': self.okRun,
         'back': self.closerm,
         'red': self.closerm,
         # 'yellow': self.remove,
         # 'blue': self.msgtqm,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'menu': self.goConfig,
         'cancel': self.closerm}, -1)

        self.onLayoutFinish.append(self.updateMenuList)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        # itype = idx
        # name = self.names[itype]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)

        else:
            if idx and (idx != '' or idx > -1):
                text_clear = self.infos[idx]
            else:
                self.session.open(MessageBox, name, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_poster()

    def closerm(self):
        Utils.deletetmp()
        self.close()

    def updateMenuList(self):
        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]
        list = []
        self.idx = 0

        for x in PanelMain:
            list.append(rvListEntry(x, self.idx))
            self.menu_list.append(x)
            self.idx += 1
        self['text'].setList(list)
        self.load_poster()

    def okRun(self):
        self.keyNumberGlobalCB(self['text'].getSelectedIndex())

    def search_text(self, name, url, pic):
        self.namex = name
        self.urlx=url
        self.picx = pic
        self.session.openWithCallback(self.filterChannels, VirtualKeyBoard, title=_("Filter this category..."), text='')

    def filterChannels(self, result):
        if result:
            global search
            search = False
            pic = self.picx
            name = str(result)
            url = self.urlx + str(result)
            try:
                # if nextmodule == 'Videos4':
                    search = True
                    self.session.open(nextvideo4, name, url, pic, nextmodule)
            except:
                return
        else:
            self.resetSearch()

    def resetSearch(self):
        global search
        search = False
        return

    def keyNumberGlobalCB(self, idx):
        i = len(self.menu_list)
        print('iiiiii= ',i)
        if i < 1:
            return

        global nextmodule
        sel = self.menu_list[idx]
        live, movie, series, other = TvsApi()
        if sel == ('SEARCH'):
            name = 'Search'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=movie&query=' #live #all_channel_live
            pic = piconsearch
            nextmodule = "Videos4"
            # self.session.open(search_text, name, url, pic, nextmodule)
            self.search_text(name, url, pic)
        # if 'Search' in str(name):
            # search = True
            # from Screens.VirtualKeyBoard import VirtualKeyBoard
            # print('Search go movie: ', search)
            # self.search_text(name, url, pic)
        elif sel == ('LIVE'):
            name = 'LIVE'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=live&page=1' #live #all_channel_live
            pic = piconlive
            nextmodule = 'live'
            self.session.open(live_stream, name, url, pic, nextmodule)
        elif sel == 'MOVIE':
            name = 'MOVIE'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=listGenMovie&page=1' #movie #all_channel_movie
            pic = piconmovie
            nextmodule = 'movie'
            self.session.open(live_stream, name, url, pic, nextmodule)
        elif sel == ('SERIES'):
            name = 'SERIES'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=listSerie&page=1' #series #all_channel_series
            pic = piconseries
            nextmodule = 'series'
            self.session.open(live_stream, name, url, pic, nextmodule)
        else:
            if sel == ('INTERNATIONAL'):
                name = 'INTERNATIONAL'
                url = other
                pic = piconinter
                nextmodule = 'other'
                self.mbox = self.session.open(MessageBox, _('Use my Plugin Freearhey'), MessageBox.TYPE_INFO, timeout=4)

    def goConfig(self):
        self.session.open(myconfig)

    def up(self):
        self[self.currentList].up()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_poster()

    def load_poster(self):
        sel = self['text'].getSelectedIndex()
        if sel != None or sel != -1:
            if sel == 0:
                pixmaps = piconsearch
            elif sel == 1:
                pixmaps = piconlive
            elif sel == 2:
                pixmaps = piconmovie
            elif sel == 3:
                pixmaps = piconseries
            else:
                pixmaps = piconinter
            size = self['poster'].instance.size()
            if Utils.DreamOS():
                self['poster'].instance.setPixmap(gPixmapPtr())
            else:
                self['poster'].instance.setPixmap(None)
            self.scale = AVSwitch().getFramebufferScale()
            self.picload = ePicLoad()
            self.picload.setPara((size.width(),
             size.height(),
             self.scale[0],
             self.scale[1],
             False,
             1,
             '#FF000000'))
            ptr = self.picload.getData()
            if Utils.DreamOS():
                if self.picload.startDecode(pixmaps, False) == 0:
                    ptr = self.picload.getData()
            else:
                if self.picload.startDecode(pixmaps, 0, 0, False) == 0:
                    ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class live_stream(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        self.type = self.name
        self.downloading = False
        self.currentList = 'text'
        self.idx = 0
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         "epg": self.showIMDB,
         "info": self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(2000, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def readJsonFile(self, name, url, pic):
        global nextmodule
        content = Utils.ReadUrl2(url)
        # if six.PY3:
            # content = six.ensure_str(content)
        print('live_stream content B =', content)
        y = json.loads(content)
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        i = 0
        while i < 100:
            try:
                print('In live_stream y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                # print("In live_stream name =", name)
                url = (y["items"][i]["externallink"])
                url = url.replace("\\", "")
                # print("In live_stream url =", url)
                pic = (y["items"][i]["thumbnail"])
                # print("In live_stream pic =", pic)
                info = (y["items"][i]["info"])
                # print("In live_stream info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            if 'movie' in nextmodule:
                nextmodule = "Videos4"
                self.names.append('Search Movies')
                self.urls.append("https://tivustream.website/php_filter/kodi19/kodi19.php?mode=movie&query=")
                self.pics.append(str(piconsearch))
                self.infos.append(str('Search Movies'))
                i = i+1
            if 'live' in nextmodule:
                nextmodule = "Videos3"
            if 'series' in nextmodule:
                nextmodule = 'Videos1'
            print('=====================')
            print(nextmodule)
            print('=====================')
        showlist(self.names, self['text'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        if 'Search' in str(name):
            search = True
            from Screens.VirtualKeyBoard import VirtualKeyBoard
            print('Search go movie: ', search)
            self.search_text(name, url, pic)
        #live
        if nextmodule == 'Videos3':
            # openCat
            print('Videos3 play next: ', nextmodule)
            self.session.open(video3, name, url, pic, nextmodule)
        #movie
        # if nextmodule == 'Videos4':
        if 'listMovie' in str(url):

            self.session.open(nextvideo4, name, url, pic, nextmodule)
            print('video4 and listMovie : ', nextmodule)
        else:
            if 'movieId' in str(url):
                print('video4 and play : ', nextmodule)
                self.session.open(video5, name, url, pic, nextmodule)
        #series
        # if nextmodule == 'Videos1':
        if '&page' in str(url) and nextmodule == 'Videos1': #work
            self.session.open(nextvideo1, name, url, pic, nextmodule)
        if '&page' not in str(url) and nextmodule == 'Videos1':
            print('video1 and play next: ', nextmodule)
            if 'tvseriesId' in str(url):
                self.session.open(video1, name, url, pic, nextmodule)
                print('video1 and tvseriesId next: ', nextmodule)
            else:
                print('video1 and play next: ', nextmodule)
                self.session.open(Playstream1, name, url, desc)

    def search_text(self, name, url, pic):
        self.namex = name
        self.urlx=url
        self.picx = pic
        self.session.openWithCallback(self.filterChannels, VirtualKeyBoard, title=_("Filter this category..."), text='')

    def filterChannels(self, result):
        if result:
            global search
            search = False
            pic = self.picx
            name = str(result)
            url = self.urlx + str(result)
            try:
                # if nextmodule == 'Videos4':
                    search = True
                    self.session.open(nextvideo4, name, url, pic, nextmodule)
            except:
                return
        else:
            self.resetSearch()

    def resetSearch(self):
        global search
        search = False
        return

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.names)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        # if idx and (idx != '' or idx > -1):
        info = self.infos[idx]
        name = self.names[idx]
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def cancel(self):
        global nextmodule
        if nextmodule == 'Videos3':
            nextmodule = 'live'
        if nextmodule == 'Videos4':
            nextmodule = 'movie'
        if nextmodule == 'Videos1':
            nextmodule = 'series'
        print('cancel nextmodule ', nextmodule)
        self.close(None)

    def up(self):
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        if idx and (idx != '' or idx > -1):
            self[self.currentList].up()
            self.load_infos()
            self.load_poster()
        else:
            return

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = self.pics[idx]
        # pixmaps = six.ensure_binary(self.pics[idx])
        if pixmaps != "" or pixmaps != "n/A" or pixmaps != None or pixmaps != "null" :
            if pixmaps.find('http') == -1:
                self.poster_resize(no_cover)
                return
            else:
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    # print("debug: pixmaps:",pixmaps)
                    # print("debug: pixmaps:",type(pixmaps))
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as ex:
                    print(ex)
                    print("Error: can't find file or read data")
            return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass
            except:
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(ex)
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        if os.path.exists(png):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(png, False)
            else:
                self.picload.startDecode(png, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class video3(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         "epg": self.showIMDB,
         "info": self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        if idx and (idx != '' or idx > -1):
            info = self.infos[idx]
            name = self.names[idx]
        else:
            info = ''
            name = ''
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        i = 0
        while i < 100:
            try:
                print('In Videos3 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                # print("In Videos3 name =", name)
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                # url = (y["items"][i]["link"])
                url = url.replace("\\", "")
                # print("In Videos3 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In Videos3 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In Videos3 info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            showlist(self.names, self['text'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        print('Videos3 nextmodule - is: ', nextmodule)
        if '&page' in str(url) and nextmodule == 'Videos3':
            self.session.open(nextvideo3, name, url, pic, nextmodule)
        else:
            self.session.open(Playstream1, name, url, desc)

    def cancel(self):
        global nextmodule
        if nextmodule == 'Videos3':
            nextmodule = 'Videos3'
        else:
            nextmodule = 'live'
            print('cancel nextmodule ', nextmodule)
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadError(self, raw):
        try:
            if fileExists(pictmp):
                self.poster_resize(pictmp)
        except Exception as ex:
            print(ex)
            print('exe downloadError')

    def downloadPic(self, data, pictmp):
        if fileExists(pictmp):
            self.poster_resize(pictmp)
        else:
            print('logo not found')


    def poster_resize(self, png):
        self["poster"].show()
        pixmaps = png
        if os.path.exists(pixmaps):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            # if self.picload:
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(pixmaps, False)
            else:
                self.picload.startDecode(pixmaps, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class nextvideo3(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        # idx = 0
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)

                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.infos)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        info = self.infos[idx]
        name = self.names[idx]
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        print("nextVideos3 content A =", content)
        y = json.loads(content)
        i = 0
        while i < 100:
            try:
                print('In nextVideos3 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                print("In nextVideos3 name =", name)
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                # url = (y["items"][i]["link"])
                url = url.replace("\\", "")
                # print("In nextVideos3 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In nextVideos3 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In nextVideos3 info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            showlist(self.names, self['text'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('video1 idx: ', idx)
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        print('nextVideos3 nextmodule - is: ', nextmodule)
        if '&page' in str(url) and nextmodule == 'Videos3':
            self.session.open(video3, name, url, pic, nextmodule)
        else:
            self.session.open(Playstream1, name, url, desc)

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos3'

        print('cancel nextvideos3 nextmodule ', nextmodule)
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadError(self, raw):
        try:
            if fileExists(pictmp):
                self.poster_resize(pictmp)
        except Exception as ex:
            print(ex)
            print('exe downloadError')

    def downloadPic(self, data, pictmp):
        if fileExists(pictmp):
            self.poster_resize(pictmp)
        else:
            print('logo not found')

    def poster_resize(self, png):
        self["poster"].show()
        pixmaps = png
        if os.path.exists(pixmaps):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            # if self.picload:
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(pixmaps, False)
            else:
                self.picload.startDecode(pixmaps, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class video4(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.infos)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        info = self.infos[idx]
        name = self.names[idx]
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        print("content Video4 =", content)
        y = json.loads(content)
        # print("y =", y)
        # print('In video4 y["items"] =', y["items"])
        # print('In video4 y["items"][0] =', y["items"][0])
        i = 0
        while i < 50:
            try:
                print('In video4 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                # print("In video4 name =", name)
                url = (y["items"][i]["externallink"])
                url = url.replace("\\", "")
                # print("In video4 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In video4 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In video4 info =", info)
                # info = [x.replace("\r\n","") for x in info]

                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos4"
        showlist(self.names, self['text'])
            # self.load_poster()

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('video4 idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        print('video4 nextmodule is: ', nextmodule)
        if '&page' in str(url):
            self.session.open(nextvideo4, name, url, pic, nextmodule)
        if 'listMovie' in str(url):
            self.session.open(nextvideo4, name, url, pic, nextmodule)
            print('video4 and listMovie : ', nextmodule)
        if 'movieId' in str(url):
                print('video4 and play : ', nextmodule)
                self.session.open(video5, name, url, pic, nextmodule)

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)

        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadError(self, raw):
        try:
            if fileExists(pictmp):
                self.poster_resize(pictmp)
        except Exception as ex:
            print(ex)
            print('exe downloadError')

    def downloadPic(self, data, pictmp):
        if fileExists(pictmp):
            self.poster_resize(pictmp)
        else:
            print('logo not found')

    def poster_resize(self, png):
        self["poster"].show()
        pixmaps = png
        if os.path.exists(pixmaps):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            # if self.picload:
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(pixmaps, False)
            else:
                self.picload.startDecode(pixmaps, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class nextvideo4(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.infos)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        info = self.infos[idx]
        name = self.names[idx]
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        print("content A =", content)
        y = json.loads(content)
        # print("y =", y)
        # print('In nextvideo4 y["items"] =', y["items"])
        # print('In nextvideo4 y["items"][0] =', y["items"][0])
        i = 0
        while i < 100:
            try:
                print('In nextvideo4 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                try:
                    url = (y["items"][i]["externallink"])
                except:
                    url = (y["items"][i]["link"])
                # print("In nextvideo4 name =", name)
                # url = (y["items"][i]["link"])
                url = url.replace("\\", "")
                # print("In nextvideo4 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In nextvideo4 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In nextvideo4 info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos4"
        showlist(self.names, self['text'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('video4 idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        print('nextvideo4 x x nextmodule is: ', nextmodule)
        if '&page' in str(url):
            self.session.open(video4, name, url, pic, nextmodule)
        if 'listMovie' in str(url):
            self.session.open(video4, name, url, pic, nextmodule)
            print('video4 and listMovie : ', nextmodule)
        else:
            if 'movieId' in str(url):
                print('video4 and play : ', nextmodule)
                self.session.open(video5, name, url, pic, nextmodule)

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadError(self, raw):
        try:
            if fileExists(pictmp):
                self.poster_resize(pictmp)
        except Exception as ex:
            print(ex)
            print('exe downloadError')

    def downloadPic(self, data, pictmp):
        if fileExists(pictmp):
            self.poster_resize(pictmp)
        else:
            print('logo not found')

    def poster_resize(self, png):
        self["poster"].show()
        pixmaps = png
        if os.path.exists(pixmaps):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            # if self.picload:
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(pixmaps, False)
            else:
                self.picload.startDecode(pixmaps, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class video1(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.infos)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        if idx and (idx != '' or idx > -1):
            info = self.infos[idx]
            name = self.names[idx]
        else:
            info = ''
            name = ''
            self['desc'].setText(info)
            self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []


        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        print("content Video1 =", content)
        y = json.loads(content)
        # print("y =", y)
        # print('In Video1 y["items"] =', y["items"])
        # print('In Video1 y["items"][0] =', y["items"][0])
        i = 0
        while i < 50:
            try:
                print('In Video1 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                # print("In Video1 name =", name)
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                # url = (y["items"][i]["link"])
                url = url.replace("\\", "")
                # print("In Video1 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In Video1 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In Video1 info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos1"
        showlist(self.names, self['text'])
            # self.load_poster()

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('Video1 idx: ', idx)
        if idx and (idx != '' or idx > -1):
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            desc = self.infos[idx]
            print('Video1 nextmodule is: ', nextmodule)
            if '&page' in str(url) and nextmodule == 'Videos1': #wooork
                self.session.open(nextvideo1, name, url, pic, nextmodule)
            if '&page' not in str(url) and nextmodule == 'Videos1': #in series not appears
                print('video1 and play next: ', nextmodule)
                if 'tvseriesId' in str(url):
                    self.session.open(nextvideo1, name, url, pic, nextmodule)
                    print('video1 and tvseriesId : ', nextmodule)
                else:
                    print('video1 and play : ', nextmodule)
                    self.session.open(Playstream1, name, url, desc)
            else:
                print('bhoo .mp4???')
                return

    def cancel(self):
        # search == False
        global nextmodule
        nextmodule = 'Videos1'
        print('cancel nextmodule ', nextmodule)
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadError(self, raw):
        try:
            if fileExists(pictmp):
                self.poster_resize(pictmp)
        except Exception as ex:
            print(ex)
            print('exe downloadError')

    def downloadPic(self, data, pictmp):
        if fileExists(pictmp):
            self.poster_resize(pictmp)
        else:
            print('logo not found')

    def poster_resize(self, png):
        self["poster"].show()
        pixmaps = png
        if os.path.exists(pixmaps):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            # if self.picload:
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(pixmaps, False)
            else:
                self.picload.startDecode(pixmaps, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class nextvideo1(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self['space'] = Label('')
        self["poster"] = Pixmap()
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        # idx = 0
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.infos)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        info = self.infos[idx]
        name = self.names[idx]
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        print("content nextvideo1 =", content)
        y = json.loads(content)
        # print("y =", y)
        # print('In nextvideo1 y["items"] =', y["items"])
        # print('In nextvideo1 y["items"][0] =', y["items"][0])
        i = 0
        while i < 50:
            try:
                print('In nextvideo1 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                # print("In nextvideo1 name =", name)
                url = (y["items"][i]["externallink"])
                url = url.replace("\\", "")
                # print("In nextvideo1 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In nextvideo1 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In nextvideo1 info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos1"
        showlist(self.names, self['text'])
            # self.load_poster()

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('nextvideo1 idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        print('nextvideo1 nextmodule is: ', nextmodule)
        if '&page' in str(url) and nextmodule == 'Videos1': #wooork
            self.session.open(video1, name, url, pic, nextmodule)
        if '&page' not in str(url) and nextmodule == 'Videos1': #in series not appears
            print('nextvideo1 and play next: ', nextmodule)
            if 'tvseriesId' in str(url):
                self.session.open(video1, name, url, pic, nextmodule)
                print('nextvideo1 and tvseriesId next: ', nextmodule)
            else:
                print('nextvideo1 and play next: ', nextmodule)
                self.session.open(Playstream1, name, url, desc)
        else:
            print('bhoo .mp4???')
            return

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos1'
        print('cancel movie nextmodule ', nextmodule)
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)
        # if i < 1:
            # return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass
            except:
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(ex)
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        if os.path.exists(png):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(png, False)
            else:
                self.picload.startDecode(png, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class video5(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME REVOLUTION')
        self.setTitle(title_plug)
        self.list = []
        self['text'] = self.list
        self['text'] = rvList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self["poster"] = Pixmap()
        self['desc'] = StaticText()
        self['space'] = Label('')
        #self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self['key_green'] = Button(_('Download'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_(''))
        self["key_blue"] = Button(_(''))
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        print('self.name: ', self.name)
        print('self.url: ', self.url)
        print('self.pic: ', self.pic)
        self.downloading = False
        self.currentList = 'text'
        self['title'] = Label(name)
        self['actions'] = ActionMap(['SetupActions', "EPGSelectActions", 'DirectionActions', 'ColorActions'], {'ok': self.okRun,
         # 'green': self.start_download,
         # 'yellow': self.readJsonFile,
         'red': self.cancel,
         'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'cancel': self.cancel}, -2)
        self.readJsonFile(name, url, pic)
        self.timer = eTimer()
        self.timer.start(1000, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        name = self.names[idx]
        text_clear = name
        if is_tmdb:
            try:
                from Plugins.Extensions.tmdb import tmdb
                text = Utils.charRemove(text_clear)
                _session.open(tmdb.tmdbScreen, text, 0)
            except Exception as e:
                print("[XCF] Tmdb: ", e)
        elif is_imdb:
            try:
                from Plugins.Extensions.IMDb.plugin import main as imdb
                text = Utils.charRemove(text_clear)
                imdb(_session, text)
            except Exception as e:
                print("[XCF] imdb: ", e)
        else:
            inf = idx
            if inf and inf != '':
                text_clear = self.infos[inf]
            else:
                text_clear = name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self['info'].setText('Select')
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        i = len(self.infos)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        if idx and (idx != '' or idx > -1):
            info = self.infos[idx]
            name = self.names[idx]
        else:
            info = ''
            name = ''
        self['desc'].setText(info)
        self['space'].setText(str(name))

    def selectionChanged(self):
        if self["text"].getCurrent():
            currentindex = self["text"].getIndex()
            print(currentindex)

    def readJsonFile(self, name, url, pic):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(url)
        if PY3:
            content = six.ensure_str(content)
        print("content A =", content)
        y = json.loads(content)
        # print("y =", y)
        # print('In video5 y["items"] =', y["items"])
        # print('In video5 y["items"][0] =', y["items"][0])
        i = 0
        while i < 100:
            try:
                print('In Videos5 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                # n1 = name.find("]", 0)
                # n2 = name.find("[", n1)
                # name = name[(n1+1):n2]
                name = REGEX.sub('', name.strip())
                # print("In Videos5 name =", name)
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                url = url.replace("\\", "")
                # print("In Videos5 url =", url)
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                # print("In Videos5 pic =", pic)
                info = (y["items"][i]["info"])
                # print("In Videos5 info =", info)
                # info = [x.replace("\r\n","") for x in info]
                info = Utils.checkStr(info)
                info = info.replace("\r\n","")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            showlist(self.names, self['text'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        info = self.infos[idx]
        desc = self.infos[idx]
        print('video5 nextmodule is: ', nextmodule)
        self.session.open(Playstream1, name, url, desc)

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos4'
        print('cancel nextmodule ', nextmodule)
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        i = len(self.pics)
        print('iiiiii= ',i)

        idx = self["text"].getSelectionIndex()
        print('idx: ', idx)
        pixmaps = six.ensure_binary(self.pics[idx])
        print("debug: pixmaps:",pixmaps)
        print("debug: pixmaps:",type(pixmaps))
        global pictmp
        path = urlparse(pixmaps).path
        ext = splitext(path)[1]
        pictmp = '/tmp/posterx' + str(ext)
        if fileExists(pictmp):
            pictmp = '/tmp/posterx' + str(ext)
        else:
            m = hashlib.md5()
            m.update(pixmaps)
            pictmp = m.hexdigest()
        try:
            if pixmaps.startswith(b"https") and sslverify:
                parsed_uri = urlparse(pixmaps)
                domain = parsed_uri.hostname
                sniFactory = SNIFactory(domain)
                # if six.PY3:
                    # pixmaps = pixmaps.encode()
                print('uurrll: ', pixmaps)
                downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
            else:
                downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass
            except:
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(ex)
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        if os.path.exists(png):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()

            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(png, False)
            else:
                self.picload.startDecode(png, 0, 0, False)
            ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class myconfig(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        skin = skin_path + 'myconfig.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.setTitle(title_plug)
        self.setup_title = title_plug
        self.onChangedEntry = []
        self.session = session
        self['description'] = Label('')
        self["paypal"] = Label()
        info = ''
        self['info'] = Label('')
        self['key_yellow'] = Button(_('Choice'))
        self['key_green'] = Button(_('Save'))
        self['key_red'] = Button(_('Back'))
        self["key_blue"] = Button(_('Empty Cache'))
        # self['key_blue'].hide()
        self['title'] = Label(title_plug)
        self["setupActions"] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'VirtualKeyboardActions', 'ActiveCodeActions'], {'cancel': self.extnok,
         'red': self.extnok,
         'back': self.close,
         'left': self.keyLeft,
         'right': self.keyRight,
         "showVirtualKeyboard": self.KeyText,
         'yellow': self.Ok_edit,
         'ok': self.Ok_edit,
         'blue': self.cachedel,
         'green': self.msgok}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
        self.createSetup()
        self.onLayoutFinish.append(self.layoutFinished)
        if self.setInfo not in self['config'].onSelectionChanged:
            self['config'].onSelectionChanged.append(self.setInfo)

    def setInfo(self):
        entry = str(self.getCurrentEntry())
        if entry == _('Set the path to the Cache folder'):
            self['description'].setText(_("Press Ok to select the folder containing the picons files"))
            return

    def setInfo(self):
        entry = str(self.getCurrentEntry())
        if entry == _('Set the path Movie folder'):
            self['description'].setText(_("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required"))
            return
        if entry == _('Set the path to the Cache folder'):
            self['description'].setText(_("Press Ok to select the folder containing the picons files"))
            return
        if entry == _('Services Player Reference type'):
            self['description'].setText(_("Configure Service Player Reference"))
            return
        return

    def paypal2(self):
        conthelp = "If you like what I do you\n"
        conthelp += " can contribute with a coffee\n\n"
        conthelp += "scan the qr code and donate € 1.00"
        return conthelp
    
    def layoutFinished(self):
        paypal = self.paypal2()
        self["paypal"].setText(paypal)  
        self.setTitle(self.setup_title)
        if not os.path.exists('/tmp/currentip'):
            os.system('wget -qO- http://ipecho.net/plain > /tmp/currentip')
        currentip1 = open('/tmp/currentip', 'r')
        currentip = currentip1.read()
        self['info'].setText(_('Config Revolution Panel\nYour current IP is %s') % currentip)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        self.list.append(getConfigListEntry(_("Set the path Movie folder"), config.plugins.revolution.movie,_("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required")))
        self.list.append(getConfigListEntry(_("Set the path to the Cache folder"), config.plugins.revolution.cachefold, _("Press Ok to select the folder containing the picons files")))
        self.list.append(getConfigListEntry(_('Services Player Reference type'), config.plugins.revolution.services, _("Configure Service Player Reference")))
        self["config"].list = self.list
        self["config"].setList(self.list)
        # self.setInfo()

    def cachedel(self):
        fold = config.plugins.revolution.cachefold.value + "/pic"
        cmd = "rm " + fold + "/*"
        os.system(cmd)
        self.mbox = self.session.open(MessageBox, _('All cache fold are empty!'), MessageBox.TYPE_INFO, timeout=5)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        print("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        print("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def msgok(self):
        if self['config'].isChanged():
            for x in self['config'].list:
                x[1].save()
            self.mbox = self.session.open(MessageBox, _('Settings saved correctly!'), MessageBox.TYPE_INFO, timeout=5)
            self.close()
        else:
         self.close()

    def Ok_edit(self):
        ConfigListScreen.keyOK(self)
        sel = self['config'].getCurrent()[1]
        if sel and sel == config.plugins.revolution.cachefold:
            self.setting = 'revol'
            mmkpth = config.plugins.revolution.cachefold.value
            self.openDirectoryBrowser(mmkpth)
        if sel and sel == config.plugins.revolution.movie:
            self.setting = 'moviefold'
            self.openDirectoryBrowser(config.plugins.revolution.movie.value)
        else:
            pass

    def openDirectoryBrowser(self, path):
        try:
            self.session.openWithCallback(
             self.openDirectoryBrowserCB,
             LocationBox,
             windowTitle=_('Choose Directory:'),
             text=_('Choose Directory'),
             currDir=str(path),
             bookmarks=config.movielist.videodirs,
             autoAdd=False,
             editDir=True,
             inhibitDirs=['/bin', '/boot', '/dev', '/home', '/lib', '/proc', '/run', '/sbin', '/sys', '/var'],
             minFree=15)
        except Exception as e:
            print(('openDirectoryBrowser get failed: ', str(e)))

    def openDirectoryBrowserCB(self, path):
        if path != None:
            if self.setting == 'revol':
                config.plugins.revolution.cachefold.setValue(path)
            if self.setting == 'moviefold':
                config.plugins.revolution.revolution.setValue(path)
        return

    def KeyText(self):
        sel = self['config'].getCurrent()
        if sel:
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self['config'].getCurrent()[0], text=self['config'].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback = None):
        if callback != None and len(callback):
            self['config'].getCurrent()[1].value = callback
            self['config'].invalidate(self['config'].getCurrent())
        return

    def restartenigma(self, result):
        if result:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close(True)

    def changedEntry(self):
        sel = self['config'].getCurrent()
        for x in self.onChangedEntry:
            x()
        try:
            if isinstance(self['config'].getCurrent()[1], ConfigEnableDisable) or isinstance(self['config'].getCurrent()[1], ConfigYesNo) or isinstance(self['config'].getCurrent()[1], ConfigSelection):
                self.createSetup()
        except:
            pass
    def getCurrentEntry(self):
        return self['config'].getCurrent() and self['config'].getCurrent()[0] or ''

    def getCurrentValue(self):
        return self['config'].getCurrent() and str(self['config'].getCurrent()[1].getText()) or ''

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def extnok(self):
        if self['config'].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _('Really close without saving the settings?'))
        else:
            self.close()

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self['config'].list:
            x[1].cancel()
        self.close()

class Playstream1(Screen):
    def __init__(self, session, name, url, desc):
        Screen.__init__(self, session)
        self.session = session
        skin = skin_path + 'Playstream1.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        print('self.skin: ', skin)
        f.close()
        self.setup_title = ('Select Player Stream')
        self.list = []
        self['list'] = rvList([])
        self['info'] = Label()
        self['info'].setText(name)
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Select'))
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self.downloading = False
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions', 'InfobarInstantRecord'], {'red': self.cancel,
         'green': self.okClicked,
         'back': self.cancel,
         'cancel': self.cancel,
         "rec": self.runRec,
         "instantRecord": self.runRec,
         "ShortRecord": self.runRec,
         'ok': self.okClicked}, -2)
        self.name1 = name
        self.url = url
        self.desc = desc
        print('In Playstream1 self.url =', url)
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self.onLayoutFinish.append(self.openTest)
        return

    def runRec(self):
        self.namem3u = self.name1
        self.urlm3u = self.url
        if self.downloading == True:
            self.session.open(MessageBox, _('You are already downloading!!!'), MessageBox.TYPE_INFO, timeout=5)
            return
        else:
            if '.mp4' or '.mkv' or '.flv' or '.avi' in self.urlm3u: # or 'm3u8':
                self.session.openWithCallback(self.download_m3u, MessageBox, _("DOWNLOAD VIDEO?\n%s" %self.namem3u ) , type=MessageBox.TYPE_YESNO, timeout = 10, default = False)
            else:
                self.downloading = False
                self.session.open(MessageBox, _('Only VOD Movie allowed or not .ext Filtered!!!'), MessageBox.TYPE_INFO, timeout=5)

    def download_m3u(self, result):
        if result:
            if not 'm3u8' in self.urlm3u:
                path = urlparse(self.urlm3u).path
                ext = '.mp4'
                ext = splitext(path)[1]
                if ext != '.mp4' or ext != '.mkv' or ext != '.avi' or ext != '.flv': # or ext != 'm3u8':
                    ext = '.mp4'
                fileTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', self.namem3u)
                fileTitle = re.sub(r' ', '_', fileTitle)
                fileTitle = re.sub(r'_+', '_', fileTitle)
                fileTitle = fileTitle.replace("(", "_").replace(")", "_").replace("#", "").replace("+", "_").replace("\'", "_").replace("'", "_").replace("!", "_").replace("&", "_")
                fileTitle = fileTitle.lower() + ext
                self.in_tmp = Path_Movies + fileTitle
                self.downloading = True
                self.download = downloadWithProgress(self.urlm3u, self.in_tmp)
                self.download.addProgress(self.downloadProgress)
                self.download.start().addCallback(self.check).addErrback(self.showError)
            else:
                self.downloading = False
                self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_INFO, timeout=5)
        else:
            self.downloading = False

    def downloadProgress(self, recvbytes, totalbytes):
        self["progress"].show()
        self['progress'].value = int(100 * recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (recvbytes / 1024, totalbytes / 1024, 100 * recvbytes / float(totalbytes))

    def check(self, fplug):
        checkfile = self.in_tmp
        if os.path.exists(checkfile):
            # self.downloading = False
            self['progresstext'].text = ''
            self.progclear = 0
            self['progress'].setValue(self.progclear)
            self["progress"].hide()

    def showError(self, error):
        self.downloading = False
        self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_INFO, timeout=5)

    def openTest(self):
        url = self.url
        self.names = []
        self.urls = []
        self.names.append('Play Now')
        self.urls.append(url)
        self.names.append('Download Now')
        self.urls.append(url)
        self.names.append('Play HLS')
        self.urls.append(url)
        self.names.append('Play TS')
        self.urls.append(url)
        self.names.append('Streamlink')
        self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        self.name = self.names[idx]
        self.url = self.urls[idx]
        # if "youtube" in str(self.url):
            # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # return
        if "youtube" in str(self.url):
            desc = self.desc
            try:
                from Plugins.Extensions.revolution.youtube_dl import YoutubeDL
                '''
                ydl_opts = {'format': 'best'}
                ydl_opts = {'format': 'bestaudio/best'}
                '''
                ydl_opts = {'format': 'best'}
                ydl = YoutubeDL(ydl_opts)
                ydl.add_default_info_extractors()
                result = ydl.extract_info(self.url, download=False)
                self.url = result["url"]
            except:
                pass
            self.session.open(Playstream2, self.name, self.url, desc)
        if idx == 0:
            self.name = self.names[idx]
            self.url = self.urls[idx]
            print('In playVideo url D=', self.url)
            self.play()
        elif idx == 1:
            # self.name = self.names[idx]
            self.url = self.urls[idx]
            print('In playVideo url D=', self.url)
            self.runRec()
            # return
        elif idx == 2:
            print('In playVideo url B=', self.url)
            self.name = self.names[idx]
            self.url = self.urls[idx]
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass
            header = ''
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/revolution/resolver/hlsclient.py" "' + self.url + '" "1" "' + header + '" + &'
            print('In playVideo cmd =', cmd)
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            self.play()
        elif idx == 3:
            print('In playVideo url A=', self.url)
            url = self.url
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/revolution/resolver/tsclient.py" "' + url + '" "1" + &'
            print('hls cmd = ', cmd)
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            self.name = self.names[idx]
            self.play()
        else:
            if idx == 4:
                self.name = self.names[idx]
                self.url = self.urls[idx]
                print('In playVideo url D=', self.url)
                self.play2()
        # else:
            # self.name = self.names[idx]
            # self.url = self.urls[idx]
            # print('In playVideo url D=', self.url)
            # self.play()
        return

    def playfile(self, serverint):
        self.serverList[serverint].play(self.session, self.url, self.name)

    def play(self):
        desc = self.desc
        url = self.url
        name = self.name1
        self.session.open(Playstream2, name, url, desc)
        self.close()

    def play2(self):
        if Utils.isStreamlinkAvailable():
            desc = self.desc
            name = self.name1
            # if os.path.exists("/usr/sbin/streamlinksrv"):
            url = self.url
            url = url.replace(':', '%3a')
            print('In revolution url =', url)
            ref = '5002:0:1:0:0:0:0:0:0:0:' + 'http%3a//127.0.0.1%3a8088/' + str(url)
            sref = eServiceReference(ref)
            print('SREF: ', sref)
            sref.setName(name)
            self.session.open(Playstream2, name, sref, desc)
            self.close()
        else:
            self.session.open(MessageBox, _('Install Streamlink first'), MessageBox.TYPE_INFO, timeout=5)

    def cancel(self):
        self.session.nav.stopService()
        self.session.nav.playService(srefInit)
        self.close()

class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed,
         "hide": self.hide}, 1)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
            iPlayableService.evStart: self.serviceStarted,
        })
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
        except:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

    def toggleShow(self):
        if self.skipToggleShow:
            self.skipToggleShow = False
            return
        if self.__state == self.STATE_HIDDEN:
            self.show()
            self.hideTimer.stop()
        else:
            self.hide()
            self.startHideTimer()

    def lockShow(self):
        try:
            self.__locked += 1
        except:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()

    def debug(obj, text = ""):
        print(text + " %s\n" % obj)

class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarAudioSelection, TvInfoBarShowHide, InfoBarSubtitleSupport):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    # screen_timeout = 4000
    def __init__(self, session, name, url, desc):
        global SREF, streaml
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        self.skinName = 'MoviePlayer'
        title = name
        streaml = False
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self, steal_current_service=True)
        TvInfoBarShowHide.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        InfoBarAudioSelection.__init__(self)
        InfoBarSeek.__init__(self, actionmap='InfobarSeekActions')
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        self['actions'] = ActionMap(['MoviePlayerActions',
         'MovieSelectionActions',
         'MediaPlayerActions',
         'EPGSelectActions',
         'MediaPlayerSeekActions',
         'SetupActions',
         'ColorActions',
         'InfobarShowHideActions',
         'InfobarActions',
         'InfobarSeekActions'], {'leavePlayer': self.cancel,
         'epg': self.showIMDB,
         'info': self.showinfo,
         'tv': self.cicleStreamType,
         'stop': self.leavePlayer,
         'red': self.cicleStreamType,
         'cancel': self.cancel,
         'back': self.cancel}, -1)
        # self.allowPiP = False
        self.service = None
        service = None
        # self.pcip = 'None'
        self.name = Utils.decodeHtml(name)
        self.icount = 0
        url = url.replace(':', '%3a')
        self.url = url
        self.desc = desc
        self.state = self.STATE_PLAYING
        SREF = self.session.nav.getCurrentlyPlayingServiceReference()
        # self.onLayoutFinish.append(self.cicleStreamType)
        # self.onClose.append(self.cancel)
		# self.onClose.append(self.__onClose)
        if '8088' in str(self.url):
            # self.onLayoutFinish.append(self.slinkPlay)
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            # self.onLayoutFinish.append(self.cicleStreamType)
            self.onFirstExecBegin.append(self.cicleStreamType)
        self.onClose.append(self.cancel)

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: _('4:3 Letterbox'),
         1: _('4:3 PanScan'),
         2: _('16:9'),
         3: _('16:9 always'),
         4: _('16:10 Letterbox'),
         5: _('16:10 PanScan'),
         6: _('16:9 Letterbox')}[aspectnum]

    def setAspect(self, aspect):
        map = {0: '4_3_letterbox',
         1: '4_3_panscan',
         2: '16_9',
         3: '16_9_always',
         4: '16_10_letterbox',
         5: '16_10_panscan',
         6: '16_9_letterbox'}
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())
        temp = temp + 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showinfo(self):
        sTitle = ''
        sServiceref = ''
        try:
            servicename, serviceurl = getserviceinfo(sref)
            if servicename != None:
                sTitle = servicename
            else:
                sTitle = ''
            if serviceurl != None:
                sServiceref = serviceurl
            else:
                sServiceref = ''
            currPlay = self.session.nav.getCurrentService()
            sTagCodec = currPlay.info().getInfoString(iServiceInformation.sTagCodec)
            sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
            sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
            message = 'stitle:' + str(sTitle) + '\n' + 'sServiceref:' + str(sServiceref) + '\n' + 'sTagCodec:' + str(sTagCodec) + '\n' + 'sTagVideoCodec:' + str(sTagVideoCodec) + '\n' + 'sTagAudioCodec: ' + str(sTagAudioCodec)
            self.mbox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
        except:
            pass
        return

    def showIMDB(self):
        TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
        IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
        if os.path.exists(TMDB):
            from Plugins.Extensions.TMBD.plugin import TMBD
            text_clear = self.name
            text = Utils.charRemove(text_clear)
            self.session.open(TMBD, text, False)
        elif os.path.exists(IMDb):
            from Plugins.Extensions.IMDb.plugin import IMDB
            text_clear = self.name
            text = Utils.charRemove(text_clear)
            self.session.open(IMDB, text)
        else:
            text_clear = self.name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def slinkPlay(self, url):
        name = self.name
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openPlay(self, servicetype, url):
        name = self.name
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference:   ', ref)
        if streaml == True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('streaml reference:   ', ref)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        global streml
        streaml = False
        from itertools import cycle, islice
        # self.servicetype = '4097'
        self.servicetype = str(config.plugins.revolution.services.value)
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(os.path.splitext(url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        # currentindex = 0
        # streamtypelist = ["4097"]
        # # if "youtube" in str(url):
            # # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # # return
        # if Utils.isStreamlinkAvailable():
            # streamtypelist.append("5002") #ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            # streaml = True
        # if os.path.exists("/usr/bin/gstplayer"):
            # streamtypelist.append("5001")
        # if os.path.exists("/usr/bin/exteplayer3"):
            # streamtypelist.append("5002")
        # if os.path.exists("/usr/bin/apt-get"):
            # streamtypelist.append("8193")
        # for index, item in enumerate(streamtypelist, start=0):
            # if str(item) == str(self.servicetype):
                # currentindex = index
                # break
        # nextStreamType = islice(cycle(streamtypelist), currentindex + 1, None)
        # self.servicetype = str(next(nextStreamType))
        print('servicetype2: ', self.servicetype)
        self.openPlay(self.servicetype, url)

    def up(self):
        pass

    def down(self):
        self.up()

    def doEofInternal(self, playing):
        self.close()

    def __evEOF(self):
        self.end = True

    def showVideoInfo(self):
        if self.shown:
            self.hideInfobar()
        if self.infoCallback != None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.isfile('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(SREF)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        streaml = False
        self.close()

    def leavePlayer(self):
        self.close()

class plgnstrt(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = skin_path + '/Plgnstrt.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self["poster"] = Pixmap()
        self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['text'] = StaticText()
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions', 'ColorActions', 'SetupActions'], {'ok': self.clsgo,
         'cancel': self.clsgo,
         'back': self.clsgo,
         'red': self.clsgo,
         'green': self.clsgo}, -1)
        # self.onShown.append(self.checkDwnld)
        self.onFirstExecBegin.append(self.loadDefaultImage)
        self.onLayoutFinish.append(self.checkDwnld)

    def poster_resize(self, pngori):
        pixmaps = pngori
        if Utils.DreamOS():
            self['poster'].instance.setPixmap(gPixmapPtr())
        else:
            self['poster'].instance.setPixmap(None)
        self.scale = AVSwitch().getFramebufferScale()
        self.picload = ePicLoad()
        size = self['poster'].instance.size()
        self.picload.setPara((size.width(),
         size.height(),
         self.scale[0],
         self.scale[1],
         False,
         1,
         '#FF000000'))
        ptr = self.picload.getData()
        if Utils.DreamOS():
            if self.picload.startDecode(pixmaps, False) == 0:
                ptr = self.picload.getData()
        else:
            if self.picload.startDecode(pixmaps, 0, 0, False) == 0:
                ptr = self.picload.getData()
        if ptr != None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        else:
            print('no cover.. error')
        return

    def image_downloaded(self):
        pngori = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/fulltop.jpg".format('revolution'))
        if os.path.exists(pngori):
            print('image pngori: ', pngori)
            try:
                self.poster_resize(pngori)
            except Exception as ex:
                print(ex)
                pass
            except:
                pass

    def loadDefaultImage(self, failure=None):
        import random
        print("*** failure *** %s" % failure)
        global pngori
        fldpng = '/usr/lib/enigma2/python/Plugins/Extensions/revolution/res/pics/'
        npj = random.choice(imgjpg)
        pngori = fldpng + npj
        self.poster_resize(pngori)

    def checkDwnld(self):
        self.icount = 0
        self['text'].setText(_('\n\n\nCheck Connection wait please...'))
        self.timer = eTimer()
        self.timer.start(2000, 1)
        if Utils.DreamOS():
            self.timer_conn = self.timer.timeout.connect(self.OpenCheck)
        else:
            self.timer.callback.append(self.OpenCheck)

    def getinfo(self):
        continfo = _("==========       WELCOME     ============\n")
        continfo += _("=========     SUPPORT ON:   ============\n")
        continfo += _("+WWW.TIVUSTREAM.COM - WWW.CORVOBOYS.COM+\n")
        continfo += _("http://t.me/tivustream\n\n")
        continfo += _("========================================\n")
        continfo += _("NOTA BENE:\n")
        continfo += _("Le liste create ad HOC contengono indirizzi liberamente e gratuitamente\n")
        continfo += _("trovati in rete e non protetti da sottoscrizione o abbonamento.\n")
        continfo += _("Il server di riferimento strutturale ai progetti rilasciati\n")
        continfo += _("non e' fonte di alcun stream/flusso.\n")
        continfo += _("Assolutamente VIETATO utilizzare queste liste senza autorizzazione.\n")
        continfo += _("========================================\n")
        continfo += _("DISCLAIMER: \n")
        continfo += _("The lists created at HOC contain addresses freely and freely found on\n")
        continfo += _("the net and not protected by subscription or subscription.\n")
        continfo += _("The structural reference server for projects released\n")
        continfo += _("is not a source of any stream/flow.\n")
        continfo += _("Absolutely PROHIBITED to use this lists without authorization\n")
        continfo += _("========================================\n")
        return continfo

    def OpenCheck(self):
        try:
            self['text'].setText(self.getinfo())
        except:
            self['text'].setText(_('\n\n' + 'Error downloading News!'))

    def error(self, error):
        self['text'].setText(_('\n\n' + 'Server Off !') + '\n' + _('check SERVER in config'))


    def clsgo(self):
        self.session.openWithCallback(self.close, Revolmain)

def checks():
    from . import Utils
    chekin= False
    if Utils.checkInternet():
        chekin = True
    return chekin

def main(session, **kwargs):
    if checks:
        try:
            from . import Update
            Update.upd_done()
        except:
            pass
        if PY3:
            session.open(Revolmain)
        elif os.path.exists('/var/lib/dpkg/status'):
            session.open(Revolmain)
        else:
            session.open(plgnstrt)
    else:
        session.open(MessageBox, "No Internet", MessageBox.TYPE_INFO)

def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [(desc_plug,
          main,
          title_plug,
          44)]
    return []

def mainmenu(session, **kwargs):
    main(session, **kwargs)

def Plugins(**kwargs):
    ico_path = 'logo.png'
    if not os.path.exists('/var/lib/dpkg/status'):
        ico_path = res_plugin_path + 'pics/logo.png'
    result = [PluginDescriptor(name =desc_plug, description =title_plug, where =[PluginDescriptor.WHERE_PLUGINMENU], icon =ico_path, fnc =main)]
    return result

'''======================================================'''
