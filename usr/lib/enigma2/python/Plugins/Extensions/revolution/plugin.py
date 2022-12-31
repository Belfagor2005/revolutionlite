#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             10/10/2022               *
*       skin by MMark                  *
****************************************
Info http://t.me/tivustream
'''
from __future__ import print_function
# from Screens.VirtualKeyBoard import VirtualKeyBoard
from . import Utils
from . import _
from . import html_conv
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Components.Task import Task, Condition, Job, job_manager
from Components.config import ConfigDirectory, ConfigSubsection
from Components.config import ConfigYesNo, ConfigSelection
from Components.config import config, ConfigEnableDisable
from Components.config import getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.InfoBarGenerics import InfoBarNotifications
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarAudioSelection
from Screens.InfoBarGenerics import InfoBarSubtitleSupport, InfoBarMenu
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.TaskView import JobView
from Tools.Directories import SCOPE_PLUGINS
from Tools.Directories import resolveFilename, fileExists
from Tools.Downloader import downloadWithProgress
from enigma import RT_HALIGN_LEFT
from enigma import RT_VALIGN_CENTER
from enigma import eListboxPythonMultiContent
from enigma import ePicLoad, loadPNG, gFont, gPixmapPtr
from enigma import eServiceReference
from enigma import eTimer
from enigma import iPlayableService
from os.path import splitext
from twisted.web.client import downloadPage
import json
import os
import random
import re
import six
import ssl
import sys
import time
# from .Downloader import downloadWithProgress

PY3 = False
PY3 = sys.version_info.major >= 3
print('Py3: ', PY3)

try:
    from urllib.parse import urlparse
    # from urllib.parse import unquote
    # from urllib.request import urlretrieve
    from urllib.request import urlopen, Request
    from urllib.error import URLError
    PY3 = True
    unicode = str
    unichr = chr
    long = int
except ImportError:
    from urlparse import urlparse
    # from urllib import urlretrieve
    # from urllib2 import Request
    # from urllib import unquote
    from urllib2 import urlopen, Request
    from urllib2 import URLError

if PY3:
    print('six.PY3: True ')

plugin_path = os.path.dirname(sys.modules[__name__].__file__)
global skin_path, revol, pngs, pngl, pngx, file_json, nextmodule, search, pngori, pictmp

search = False
_session = None
_firstStart = True
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


def logdata(name='', data=None):
    try:
        data = str(data)
        fp = open('/tmp/revolution.log', 'a')
        fp.write(str(name) + ': ' + data + "\n")
        fp.close()
    except:
        trace_error()
        pass


def getversioninfo():
    currversion = '1.7'
    version_file = plugin_path + '/version'
    if os.path.exists(version_file):
        try:
            fp = open(version_file, 'r').readlines()
            for line in fp:
                if 'version' in line:
                    currversion = line.split('=')[1].strip()
        except:
            pass
    logdata("Plugin ", plugin_path)
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
    DownUrl = '%s/apigen' % UrlLst
    live = ''
    movie = ''
    series = ''
    other = ''
    try:
        req = Request(DownUrl, None, headers=headers)
        tvs = urlopen(req)
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
        config.plugins.revolution.movie = ConfigDirectory(default='/media/hdd/movie/')
config.plugins.revolution.services = ConfigSelection(default='4097', choices=modechoices)
cfg = config.plugins.revolution

global Path_Movies
Path_Movies = str(config.plugins.revolution.movie.value)
if Path_Movies.endswith("\/\/"):
    Path_Movies = Path_Movies[:-1]
print('patch movies: ', Path_Movies)

currversion = getversioninfo()
title_plug = 'Pro Lite V. %s' % currversion
desc_plug = 'TivuStream Pro Revolution Lite'
ico_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/logo.png".format('revolution'))
# no_cover = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/no_cover.png".format('revolution'))
res_plugin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/".format('revolution'))
pngori = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/fulltop.jpg".format('revolution'))
piccons = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/img/".format('revolution'))
imgjpg = ("nasa.jpg", "nasa1.jpg", "nasa2.jpg")
no_cover = piccons + 'backg.png'
piconlive = piccons + 'tv.png'
piconmovie = piccons + 'cinema.png'
piconseries = piccons + 'series.png'
piconsearch = piccons + 'search.png'
piconinter = piccons + 'inter.png'
pixmaps = piccons + 'backg.png'
nextpng = 'next.png'
prevpng = 'prev.png'
Path_Tmp = "/tmp"
pictmp = Path_Tmp + "/poster.jpg"
pmovies = False
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

REGEX = re.compile(r'([\(\[]).*?([\)\]])|'
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

def returnIMDB(text_clear):
    if Utils.is_tmdb:
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = html_conv.html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as ex:
            print("[XCF] Tmdb: ", str(ex))
        return True
    elif Utils.is_imdb:
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = html_conv.html_unescape(text_clear)
            imdb(_session, text)
        except Exception as ex:
            print("[XCF] imdb: ", str(ex))
        return True
    else:
        text_clear = html_conv.html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True
    return


def piconlocal(name):
    picolocal = 'backg.png'
    if 'tv' in name.lower():
        picolocal = 'movie.png'
    elif 'adult' in name.lower():
        picolocal = 'adult.png'
    elif 'animation' in name.lower():
        picolocal = 'animation.png'
    elif 'biography' in name.lower():
        picolocal = 'biography.png'
    elif 'show' in name.lower():
        picolocal = 'game-show.png'
    elif 'history' in name.lower():
        picolocal = 'history.png'
    elif 'music' in name.lower():
        picolocal = 'music.png'
    elif 'sci-fi' in name.lower():
        picolocal = 'sci-fi.png'
    elif 'family' in name.lower():
        picolocal = 'family.png'
    elif 'short' in name.lower():
        picolocal = 'short.png'
    elif 'uncategorized' in name.lower():
        picolocal = 'uncategorized.png'
    elif 'war' in name.lower():
        picolocal = 'war.png'
    elif 'commedia' in name.lower():
        picolocal = 'commedia.png'
    elif 'comedy' in name.lower():
        picolocal = 'commedia.png'
    elif 'thriller' in name.lower():
        picolocal = 'thriller.png'
    elif 'azione' in name.lower():
        picolocal = 'azione.png'
    elif 'dramma' in name.lower():
        picolocal = 'dramma.png'
    elif 'drama' in name.lower():
        picolocal = 'dramma.png'
    elif 'western' in name.lower():
        picolocal = 'western.png'
    elif 'biografico' in name.lower():
        picolocal = 'biografico.png'
    elif 'romantico' in name.lower():
        picolocal = 'romantico.png'
    elif 'romance' in name.lower():
        picolocal = 'romantico.png'
    elif 'horror' in name.lower():
        picolocal = 'horror.png'
    elif 'musica' in name.lower():
        picolocal = 'musical.png'
    elif 'guerra' in name.lower():
        picolocal = 'guerra.png'
    elif 'bambini' in name.lower():
        picolocal = 'bambini.png'
    elif 'bianco' in name.lower():
        picolocal = 'bianconero.png'
    elif 'tutto' in name.lower():
        picolocal = 'toto.png'
    elif 'cartoni' in name.lower():
        picolocal = 'cartoni.png'
    elif 'bud' in name.lower():
        picolocal = 'budterence.png'
    elif 'documentary' in name.lower():
        picolocal = 'documentary.png'
    elif 'crime' in name.lower():
        picolocal = 'crime.png'
    elif 'mystery' in name.lower():
        picolocal = 'mistery.png'
    elif 'fiction' in name.lower():
        picolocal = 'fiction.png'
    elif 'adventure' in name.lower():
        picolocal = 'mistery.png'
    elif 'action' in name.lower():
        picolocal = 'azione.png'
    elif '007' in name.lower():
        picolocal = '007.png'
    elif 'sport' in name.lower():
        picolocal = 'sport.png'
    elif 'teatr' in name.lower():
        picolocal = 'teatro.png'
    elif 'extra' in name.lower():
        picolocal = 'extra.png'
    elif 'search' in name.lower():
        picolocal = 'search.png'
    elif 'abruzzo' in name.lower():
        picolocal = 'regioni/abruzzo.png'
    elif 'basilicata' in name.lower():
        picolocal = 'regioni/basilicata.png'
    elif 'calabria' in name.lower():
        picolocal = 'regioni/calabria.png'
    elif 'campania' in name.lower():
        picolocal = 'regioni/campania.png'
    elif 'emilia' in name.lower():
        picolocal = 'regioni/emiliaromagna.png'
    elif 'friuli' in name.lower():
        picolocal = 'regioni/friuliveneziagiulia.png'
    elif 'lazio' in name.lower():
        picolocal = 'regioni/lazio.png'
    elif 'liguria' in name.lower():
        picolocal = 'regioni/liguria.png'
    elif 'lombardia' in name.lower():
        picolocal = 'regioni/lombardia.png'
    elif 'marche' in name.lower():
        picolocal = 'regioni/marche.png'
    elif 'mediaset' in name.lower():
        picolocal = 'mediaset.png'
    elif 'molise' in name.lower():
        picolocal = 'regioni/molise.png'
    elif 'nazionali' in name.lower():
        picolocal = 'nazionali.png'
    elif 'news' in name.lower():
        picolocal = 'news.png'
    elif 'piemonte' in name.lower():
        picolocal = 'regioni/piemonte.png'
    elif 'puglia' in name.lower():
        picolocal = 'regioni/puglia.png'
    elif 'rai' in name.lower():
        picolocal = 'rai.png'
    elif 'webcam' in name.lower():
        picolocal = 'relaxweb.png'
    elif 'relax' in name.lower():
        picolocal = 'relaxweb.png'
    elif 'sardegna' in name.lower():
        picolocal = 'regioni/sardegna.png'
    elif 'sicilia' in name.lower():
        picolocal = 'regioni/sicilia.png'
    elif 'toscana' in name.lower():
        picolocal = 'regioni/toscana.png'
    elif 'trentino' in name.lower():
        picolocal = 'regioni/trentino.png'
    elif 'umbria' in name.lower():
        picolocal = 'regioni/umbria.png'
    elif 'veneto' in name.lower():
        picolocal = 'regioni/veneto.png'
    elif 'aosta' in name.lower():
        picolocal = 'regioni/valledaosta.png'
    elif 'vecchi' in name.lower():
        picolocal = 'vecchi.png'
    elif 'italia' in name.lower():
        picolocal = 'movie.png'
    elif 'fantascienza' in name.lower():
        picolocal = 'fantascienza.png'
    elif 'fantasy' in name.lower():
        picolocal = 'fantasy.png'
    elif 'fantasia' in name.lower():
        picolocal = 'fantasia.png'
    elif 'film' in name.lower():
        picolocal = 'movie.png'
    elif 'plutotv' in name.lower():
        picolocal = 'plutotv.png'
    elif 'samsung' in name.lower():
        picolocal = 'samsung.png'
    elif 'prev' in name.lower():
        picolocal = prevpng
    elif 'next' in name.lower():
        picolocal = nextpng
    print('>>>>>>>> ' + str(piccons) + str(picolocal))
    name = str(piccons) + str(picolocal)
    return name


class rvList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if Utils.isFHD():
            self.l.setItemHeight(50)
            textfont = int(30)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(30)
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
    # pngs = piconlocal(name)
    if Utils.isFHD():
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 3), size=(30, 30), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlist(data, list):
    idx = 0
    plist = []
    for line in data:
        name = data[idx]
        plist.append(rvListEntry(name, idx))
        idx = idx + 1
        list.setList(plist)


PanelMain = [
             ('SEARCH'),
             ('LIVE'),
             ('MOVIE'),
             ('SERIES'),
             ('INTERNATIONAL')]


class Revolmain(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'revall.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        global nextmodule
        nextmodule = 'revolmain'
        self['list'] = rvList([])
        self.setup_title = ('HOME REVOLUTION')
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['poster'] = Pixmap()
        self['desc'] = StaticText()
        self['info'] = Label('')
        self['info'].setText('Select')
        self['key_red'] = Button(_('Exit'))
        self.currentList = 'list'
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.idx = 0
        self.menulist = []
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'ButtonSetupActions',
                                     'MenuActions',
                                     'DirectionActions'], {'ok': self.okRun,
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
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_poster()

    def closerm(self):
        # Utils.deletetmp()
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
        self['list'].setList(list)
        self.load_poster()

    def okRun(self):
        self.keyNumberGlobalCB(self['list'].getSelectedIndex())

    def search_text(self, name, url, pic):
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        self.namex = name
        self.urlx = url
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
        print('iiiiii= ', i)
        if i < 1:
            return
        global nextmodule
        sel = self.menu_list[idx]
        live, movie, series, other = TvsApi()
        if sel == ('SEARCH'):
            name = 'Search'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=movie&query='  # live #all_channel_live
            pic = piconsearch
            nextmodule = "Videos4"
            self.search_text(name, url, pic)
        elif sel == ('LIVE'):
            name = 'LIVE'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=live&page=1'  # live #all_channel_live
            pic = piconlive
            nextmodule = 'live'
            self.session.open(live_stream, name, url, pic, nextmodule)
        elif sel == 'MOVIE':
            name = 'MOVIE'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=listGenMovie&page=1'  # movie #all_channel_movie
            pic = piconmovie
            nextmodule = 'movie'
            self.session.open(live_stream, name, url, pic, nextmodule)
        elif sel == ('SERIES'):
            name = 'SERIES'
            url = 'https://tivustream.website/php_filter/kodi19/kodi19.php?mode=listSerie&page=1'  # series #all_channel_series
            pic = piconseries
            nextmodule = 'series'
            self.session.open(live_stream, name, url, pic, nextmodule)
        else:
            if sel == ('INTERNATIONAL'):
                self.zfreearhey()

    def zfreearhey(self):
        freearhey = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/skin".format('freearhey'))
        if os.path.isdir(freearhey):
            from Plugins.Extensions.freearhey.plugin import freearhey
            self.session.open(freearhey)
        else:
            try:
                self.mbox = self.session.open(MessageBox, _('freearhey Plugin Not Installed!!\nUse my Plugin Freearhey'), MessageBox.TYPE_INFO, timeout=4)
            except Exception as e:
                print('error infobox ', str(e))

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
        try:
            sel = self['list'].getSelectedIndex()
            if sel is not None or sel != -1:
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
                if ptr is not None:
                    self['poster'].instance.setPixmap(ptr)
                    self['poster'].show()
                else:
                    print('no cover.. error')
                return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")


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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        # self.names = []
        # self.urls = []
        # self.pics = []
        # self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.type = self.name
        self.downloading = False
        self.currentList = 'list'
        self.idx = 0
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        # self.readJsonFile(name, url, pic)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        # self.onFirstExecBegin.append(self.download)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def readJsonFile(self):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        # if six.PY3:
            # content = six.ensure_str(content)
        y = json.loads(content)
        i = 0
        while i < 100:
            try:
                print('In live_stream y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                url = (y["items"][i]["externallink"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                info = (y["items"][i]["info"])
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                print("In live_stream name =", name)
                # print("In live_stream url =", url)
                print("In live_stream pic =", pic)
                # print("In live_stream info =", info)
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i + 1
            except:
                break
            if 'movie' in nextmodule:
                nextmodule = "Videos4"
                self.names.append('Search')
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
        showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()

        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        if 'Search' in str(name):
            search = True
            print('Search go movie: ', search)
            self.search_text(name, url, pic)
        # live
        if nextmodule == 'Videos3':
            # openCat
            print('Videos3 play next: ', nextmodule)
            self.session.open(video3, name, url, pic, nextmodule)
        # movie
        # if nextmodule == 'Videos4':
        if 'listMovie' in str(url):
            self.session.open(nextvideo4, name, url, pic, nextmodule)
            print('video4 and listMovie : ', nextmodule)
        else:
            if 'movieId' in str(url):
                print('video4 and play : ', nextmodule)
                self.session.open(video5, name, url, pic, nextmodule)
        # series
        # if nextmodule == 'Videos1':
        if '&page' in str(url) and nextmodule == 'Videos1':  # work
            self.session.open(nextvideo1, name, url, pic, nextmodule)
        if '&page' not in str(url) and nextmodule == 'Videos1':
            print('video1 and play next: ', nextmodule)
            if 'tvseriesId' in str(url):
                self.session.open(video1, name, url, pic, nextmodule)
                print('video1 and tvseriesId next: ', nextmodule)
            else:
                print('video1 and play next: ', nextmodule)
                self.session.open(Playstream1, name, url, desc, pic)

    def search_text(self, name, url, pic):
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        self.namex = name
        self.urlx = url
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
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in load_infos")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def cancel(self):
        global nextmodule
        if nextmodule == 'Videos3':
            nextmodule = 'live'
        if nextmodule == 'Videos4':
            nextmodule = 'movie'
        if nextmodule == 'Videos1':
            nextmodule = 'series'
        else:
            nextmodule = 'revolmain'
        print('cancel nextmodule ', nextmodule)

        self.close()

    def up(self):
        idx = self['list'].getSelectionIndex()
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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
            if 'tvseriesId' not in str(url):
                pixmaps = piconlocal(name)
                if 'plutotv' in name.lower():
                    pixmaps = str(piccons) + 'plutotv.png'
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps t:", pixmaps)
                    print("debug pixmaps t:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, 1)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        i = 0
        while i < 100:
            try:
                print('In Videos3 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                print("In Videos3 name =", name)
                # print("In Videos3 url =", url)
                print("In Videos3 pic =", pic)
                # print("In Videos3 info =", info)
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        print('idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        print('Videos3 nextmodule - is: ', nextmodule)
        if '&page' in str(url) and nextmodule == 'Videos3':
            self.session.open(nextvideo3, name, url, pic, nextmodule)
        else:
            self.session.open(Playstream1, name, url, desc, pic)

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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'plutotv' in name.lower():
                pixmaps = str(piccons) + 'plutotv.png'
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps s:", pixmaps)
                    print("debug pixmaps s:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        i = 0
        while i < 100:

            try:
                print('In nextVideos3 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                print("In nextVideos3 name =", name)
                # print("In nextVideos3 url =", url)
                print("In nextVideos3 pic =", pic)
                # print("In nextVideos3 info =", info)
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        print('video1 idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        print('nextVideos3 nextmodule - is: ', nextmodule)
        if '&page' in str(url) and nextmodule == 'Videos3':
            self.session.open(video3, name, url, pic, nextmodule)
        else:
            self.session.open(Playstream1, name, url, desc, pic)

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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)

            name = self.names[idx]
            # url = self.urls[idx]

            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'plutotv' in name.lower():
                pixmaps = str(piccons) + 'plutotv.png'
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # if 'samsung' in name.lower():
                # pixmaps = str(piccons) + 'samsung.png'
                # if os.path.exists(pixmaps):
                    # self.downloadPic(None, pixmaps)
                    # return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps p:", pixmaps)
                    print("debug pixmaps p:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        # print("y =", y)
        # print('In video4 y["items"] =', y["items"])
        # print('In video4 y["items"][0] =', y["items"][0])
        i = 0
        while i < 50:
            try:
                print('In video4 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                url = (y["items"][i]["externallink"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                print("In video4 name =", name)
                # print("In video4 url =", url)
                print("In video4 pic =", pic)
                # print("In video4 info =", info)
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos4"
        showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'plutotv' in name.lower():
                pixmaps = str(piccons) + 'plutotv.png'
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # if 'samsung' in name.lower():
                # pixmaps = str(piccons) + 'samsung.png'
                # if os.path.exists(pixmaps):
                    # self.downloadPic(None, pixmaps)
                    # return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps x:", pixmaps)
                    print("debug pixmaps x:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")

        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        # print("y =", y)
        # print('In nextvideo4 y["items"] =', y["items"])
        # print('In nextvideo4 y["items"][0] =', y["items"][0])
        i = 0
        while i < 100:
            try:
                print('In nextvideo4 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                try:
                    url = (y["items"][i]["externallink"])
                except:
                    url = (y["items"][i]["link"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                print("In nextvideo4 name =", name)
                # print("In nextvideo4 url =", url)
                print("In nextvideo4 pic =", pic)
                # print("In nextvideo4 info =", info)
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos4"
        showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps y:", pixmaps)
                    print("debug pixmaps y:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        # print("y =", y)
        # print('In Video1 y["items"] =', y["items"])
        # print('In Video1 y["items"][0] =', y["items"][0])
        i = 0
        while i < 50:
            try:
                print('In Video1 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                self.names.append(Utils.checkStr(name))
                print("In Video1 name =", name)
                # print("In Video1 url =", url)
                print("In Video1 pic =", pic)
                # print("In Video1 info =", info)
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos1"
        showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        print('Video1 idx: ', idx)
        if idx and (idx != '' or idx > -1):
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            desc = self.infos[idx]
            print('Video1 nextmodule is: ', nextmodule)
            if '&page' in str(url) and nextmodule == 'Videos1':  # wooork
                self.session.open(nextvideo1, name, url, pic, nextmodule)
            if '&page' not in str(url) and nextmodule == 'Videos1':  # in series not appears
                print('video1 and play next: ', nextmodule)
                if 'tvseriesId' in str(url):
                    self.session.open(nextvideo1, name, url, pic, nextmodule)
                    print('video1 and tvseriesId : ', nextmodule)
                else:
                    print('video1 and play : ', nextmodule)
                    self.session.open(Playstream1, name, url, desc, pic)
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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps e:", pixmaps)
                    print("debug pixmaps e:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        global nextmodule
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        # print("y =", y)
        # print('In nextvideo1 y["items"] =', y["items"])
        # print('In nextvideo1 y["items"][0] =', y["items"][0])
        i = 0
        while i < 50:
            try:
                print('In nextvideo1 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                url = (y["items"][i]["externallink"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                # print("In nextvideo1 name =", name)
                # print("In nextvideo1 url =", url)
                # print("In nextvideo1 pic =", pic)
                # print("In nextvideo1 info =", info)
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            nextmodule = "Videos1"
        showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        print('nextvideo1 idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        print('nextvideo1 nextmodule is: ', nextmodule)
        if '&page' in str(url) and nextmodule == 'Videos1':  # wooork
            self.session.open(video1, name, url, pic, nextmodule)
        if '&page' not in str(url) and nextmodule == 'Videos1':  # in series not appears
            print('nextvideo1 and play next: ', nextmodule)
            if 'tvseriesId' in str(url):
                self.session.open(video1, name, url, pic, nextmodule)
                print('nextvideo1 and tvseriesId next: ', nextmodule)
            else:
                print('nextvideo1 and play next: ', nextmodule)
                self.session.open(Playstream1, name, url, desc, pic)
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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps z:", pixmaps)
                    print("debug pixmaps z:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + revol)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ButtonSetupActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'epg': self.showIMDB,
                                                           'info': self.showIMDB,
                                                           'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(200, True)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.left)
        except:
            self.timer.callback.append(self.left)
        self.timer.start(200, 1)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        text_clear = self.names[idx]
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        url = self.url
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        # print("y =", y)
        # print('In video5 y["items"] =', y["items"])
        # print('In video5 y["items"][0] =', y["items"][0])
        i = 0
        while i < 100:
            try:
                print('In Videos5 y["items"][i]["title"] =', y["items"][i]["title"])
                name = (y["items"][i]["title"])
                name = REGEX.sub('', name.strip())
                try:
                    url = (y["items"][i]["link"])
                except:
                    url = (y["items"][i]["yatse"])
                url = url.replace("\\", "")
                pic = (y["items"][i]["thumbnail"])
                pic = pic.replace("\\", "")
                info = (y["items"][i]["info"])
                info = Utils.checkStr(info)
                info = info.replace("\r\n", "")
                # print("In Videos5 name =", name)
                # print("In Videos5 url =", url)
                # print("In Videos5 pic =", pic)
                # print("In Videos5 info =", info)
                self.names.append(Utils.checkStr(name))
                self.urls.append(url)
                self.pics.append(Utils.checkStr(pic))
                self.infos.append(info)
                i = i+1
            except:
                break
            showlist(self.names, self['list'])

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        print('idx: ', idx)
        name = self.names[idx]
        url = self.urls[idx]
        desc = self.infos[idx]
        pic = self.pics[idx]
        print('video5 nextmodule is: ', nextmodule)
        self.session.open(Playstream1, name, url, desc, pic)

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
        try:
            i = len(self.pics)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'next' in name.lower():
                pixmaps = str(piccons) + nextpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if 'prev' in name.lower():
                pixmaps = str(piccons) + prevpng
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps q:", pixmaps)
                    print("debug pixmaps q:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(no_cover)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
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
        self['info'] = Label('')
        self['key_yellow'] = Button(_('Choice'))
        self['key_green'] = Button(_('Save'))
        self['key_red'] = Button(_('Back'))
        self["key_blue"] = Button(_('Empty Cache'))
        self['title'] = Label(title_plug)
        self["setupActions"] = ActionMap(['OkCancelActions',
                                          'DirectionActions',
                                          'ColorActions',
                                          'ButtonSetupActions',
                                          'VirtualKeyboardActions'], {'cancel': self.extnok,
                                                                      'red': self.extnok,
                                                                      'back': self.close,
                                                                      'left': self.keyLeft,
                                                                      'right': self.keyRight,
                                                                      'showVirtualKeyboard': self.KeyText,
                                                                      'yellow': self.Ok_edit,
                                                                      'ok': self.Ok_edit,
                                                                      'blue': self.cachedel,
                                                                      'green': self.msgok}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()
        self.onLayoutFinish.append(self.layoutFinished)
        if self.setInfo not in self['config'].onSelectionChanged:
            self['config'].onSelectionChanged.append(self.setInfo)

    def setInfo(self):
        entry = str(self.getCurrentEntry())
        if entry == _('Set the path to the Cache folder'):
            self['description'].setText(_("Press Ok to select the folder containing the picons files"))
        if entry == _('Set the path Movie folder'):
            self['description'].setText(_("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required"))
        if entry == _('Services Player Reference type'):
            self['description'].setText(_("Configure Service Player Reference"))
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
        self['info'].setText(_('Settings Revolution\nYour current IP is %s') % currentip)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        self.list.append(getConfigListEntry(_("Set the path Movie folder"), config.plugins.revolution.movie, _("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required")))
        self.list.append(getConfigListEntry(_("Set the path to the Cache folder"), config.plugins.revolution.cachefold, _("Press Ok to select the folder containing the picons files")))
        self.list.append(getConfigListEntry(_('Services Player Reference type'), config.plugins.revolution.services, _("Configure Service Player Reference")))
        self["config"].list = self.list
        self["config"].l.setList(self.list)
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
            print('openDirectoryBrowser get failed: ', str(e))

    def openDirectoryBrowserCB(self, path):
        if path is not None:
            if self.setting == 'revol':
                config.plugins.revolution.cachefold.setValue(path)
            if self.setting == 'moviefold':
                config.plugins.revolution.movie.setValue(path)
        return

    def KeyText(self):
        sel = self['config'].getCurrent()
        if sel:
            from Screens.VirtualKeyBoard import VirtualKeyBoard
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self['config'].getCurrent()[0], text=self['config'].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None and len(callback):
            self['config'].getCurrent()[1].value = callback
            self['config'].invalidate(self['config'].getCurrent())
        return

    def restartenigma(self, result):
        if result:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close(True)

    def changedEntry(self):
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
    def __init__(self, session, name, url, desc, pic):
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
        self['title'] = Label(title_plug)
        self['poster'] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Select'))
        self['key_yellow'] = Button(_('Movie'))
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self.downloading = False
        self['actions'] = ActionMap(['MoviePlayerActions',
                                     'MovieSelectionActions',
                                     'MediaPlayerActions',
                                     'EPGSelectActions',
                                     'MediaPlayerSeekActions',
                                     'DirectionActions',
                                     'ButtonSetupActions',
                                     'OkCancelActions',
                                     'InfobarShowHideActions',
                                     'InfobarActions',
                                     'InfobarSeekActions'], {'red': self.cancel,
                                                             'green': self.okClicked,
                                                             'back': self.cancel,
                                                             'cancel': self.cancel,
                                                             'leavePlayer': self.cancel,
                                                             'yellow': self.taskManager,
                                                             'rec': self.runRec,
                                                             'instantRecord': self.runRec,
                                                             'ShortRecord': self.runRec,
                                                             'ok': self.okClicked}, -2)
        self.name1 = self.cleantitle(name)
        self.url = url
        self.desc = desc
        self.pic = pic
        print('In Playstream1 self.url =', url)
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.load_poster)
        except:
            self.leftt.callback.append(self.load_poster)
        self.leftt.start(200, True)
        self.onLayoutFinish.append(self.openTest)
        return

    def cleantitle(self, title):
        cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*\(\)\[\]]', " ", str(title))
        cleanName = re.sub(r"  ", " ", cleanName)
        cleanName = cleanName.strip()
        return cleanName

    def taskManager(self):
        self.session.open(StreamTasks)

    def runRec(self):
        self.namem3u = self.name1
        self.urlm3u = self.url
        print('urlm3u ----> ', self.urlm3u)
        if self.downloading is True:
            self.session.open(MessageBox, _('You are already downloading!!!'), MessageBox.TYPE_INFO, timeout=5)
            return
        else:
            if '.mp4' or '.mkv' or '.flv' or '.avi' or 'm3u8' in self.urlm3u:  #:
                self.session.openWithCallback(self.download_m3u, MessageBox, _("DOWNLOAD VIDEO?\n%s" % self.namem3u), type=MessageBox.TYPE_YESNO, timeout=5, default=False)
            else:
                self.downloading = False
                self.session.open(MessageBox, _('Only VOD Movie allowed or not .ext Filtered!!!'), MessageBox.TYPE_INFO, timeout=5)

    def download_m3u(self, result):
        if result:
            # if 'm3u8' not in self.urlm3u:
                path = urlparse(self.urlm3u).path
                ext = '.mp4'
                ext = splitext(path)[1]
                if ext != '.mp4' or ext != '.mkv' or ext != '.avi' or ext != '.flv':  # or ext != 'm3u8':
                    ext = '.mp4'
                # ext = '.mp4'

                fileTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', self.namem3u)
                fileTitle = re.sub(r' ', '_', fileTitle)
                fileTitle = re.sub(r'_+', '_', fileTitle)
                fileTitle = fileTitle.replace("(", "_").replace(")", "_").replace("#", "").replace("+", "_").replace("\'", "_").replace("'", "_")
                fileTitle = fileTitle.replace(" ", "_").replace(":", "").replace("[", "").replace("]", "").replace("!", "_").replace("&", "_")
                # fileTitle = html_conv.html_unescape(fileTitle)
                fileTitle = fileTitle.lower() + ext
                self.in_tmp = Path_Movies + fileTitle
                # self.urlm3u = self.urlm3u.replace("[", "").replace("]", "")
                # self.urlm3u = self.urlm3u.strip()
                if PY3:
                    self.urlm3u = self.urlm3u.encode()
                self.downloading = True

                try:
                    # self.download = downloadWithProgress(self.urlm3u, self.in_tmp)
                    # self.download.addProgress(self.downloadProgress)
                    # self.download.start().addCallback(self.finish).addErrback(self.showError)

                    # useragent = "--header='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'"
                    # WGET = '/usr/bin/wget'
                    # if Utils.DreamOS():
                        # WGET = '/usr/bin/wget --no-check-certificate'
                    # cmd = WGET + " %s -c '%s' -O '%s'" % (useragent, self.urlm3u, self.in_tmp)
                    # cmd2 = WGET + " -c '%s' -O '%s'" % (self.urlm3u, self.in_tmp)

                    f = open(self.in_tmp, 'wb')
                    f.close()

                    cmd = "wget -U 'Enigma2 - Revolution Plugin' -c '%s' -O '%s'" % (self.urlm3u, self.in_tmp)
                    if "https" in str(self.urlm3u):
                        cmd = "wget --no-check-certificate -U 'Enigma2 - Revolution Plugin' -c '%s' -O '%s'" % (self.urlm3u, self.in_tmp)

                    # try:
                    print('cmd = ', cmd)
                    job_manager.AddJob(downloadJob(self, cmd, self.in_tmp, fileTitle))
                    # except:
                        # print('cmd2 = ', cmd2)
                        # job_manager.AddJob(downloadJob(self, cmd2, self.in_tmp, fileTitle))

                    pmovies = True
                    print('self url is : ', self.urlm3u)
                    print('url type: ', type(self.urlm3u))
                    # self.LastJobView()
                except URLError as e:
                    print("Download failed !!\n%s" % e)
                    self.session.openWithCallback(self.ImageDownloadCB, MessageBox, _("Download Failed !!") + "\n%s" % e, type=MessageBox.TYPE_ERROR)
                    self.downloading = False
                    pmovies = False

            # else:
                # self['info'].setText(_('Download failed!\nType m3u8'))
                # self.downloading = False
                # self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_INFO, timeout=5)
        else:
            self.downloading = False

    def ImageDownloadCB(self, ret):
        if ret:
            return
        if job_manager.active_job:
            job_manager.active_job = None
            self.close()
            return
        if len(job_manager.failed_jobs) == 0:
            # self.flashWithPostFlashActionMode = 'online'
            self.LastJobView()
        else:
            self.downloading = False
            self.session.open(MessageBox, _("Download Failed !!"), type=MessageBox.TYPE_ERROR)

    def downloadProgress(self, recvbytes, totalbytes):
        self['info'].setText(_('Download...'))
        self["progress"].show()
        self['progress'].value = int(100 * float(recvbytes) / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (float(recvbytes) / 1024, float(totalbytes) / 1024, 100 * float(recvbytes) / float(totalbytes))
        print('progress = ok')
        if recvbytes == totalbytes:
            print('progress = FINISH')
            self.downloading = False

    def finish(self, fplug):
        self['info'].setText(_('Please select ...'))
        self['progresstext'].text = ''
        self.progclear = 0
        self['progress'].setValue(self.progclear)
        self["progress"].hide()
        if os.path.exists(self.dest):
            self['info'].setText(_('File Downloaded ...'))
            self.downloading = False
        else:
            self.downloading = False

    def showError(self, error):
        self.downloading = False
        self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_INFO, timeout=5)

    def LastJobView(self):
        currentjob = None
        for job in job_manager.getPendingJobs():
            currentjob = job
        if currentjob is not None:
            self.session.open(JobView, currentjob)
        else:
            self.downloading = False

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
        if idx != '':
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
                print('In playVideo url D=', self.url)
                self.play()
            elif idx == 1:
                # self.name = self.names[idx]
                self.url = self.urls[idx]
                print('In playVideo runRec url D=', self.url)
                self.runRec()
                # return
            elif idx == 2:
                print('In playVideo url B=', self.url)
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
        self.session.nav.playService(self.srefInit)
        self.close()

    def load_poster(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            pixmaps = self.pic
            print('pixmap  : ', pixmaps)
            if str(res_plugin_path) in pixmaps:
                self.downloadPic(None, pixmaps)
                return
            # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pic)
                    # print("debug pixmaps t:", pixmaps)
                    # print("debug pixmaps t:", type(pixmaps))
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
                    print(str(ex))
                    print("Error: can't find file or read data live_to_stream")
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        else:
            print('no cover.. error')
        return


class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed, "hide": self.hide}, 1)
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

    def debug(obj, text=""):
        print(text + " %s\n" % obj)


# class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarAudioSelection, TvInfoBarShowHide, InfoBarSubtitleSupport):
    # STATE_IDLE = 0
    # STATE_PLAYING = 1
    # STATE_PAUSED = 2
    # ENABLE_RESUME_SUPPORT = True
    # ALLOW_SUSPEND = True
    # # screen_timeout = 4000
class Playstream2(
                  InfoBarBase,
                  InfoBarMenu,
                  InfoBarSeek,
                  InfoBarAudioSelection,
                  InfoBarSubtitleSupport,
                  InfoBarNotifications,
                  TvInfoBarShowHide,
                  Screen
                  ):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000

    def __init__(self, session, name, url, desc):
        global streaml
        global _session
        Screen.__init__(self, session)
        self.session = session
        self.skinName = 'MoviePlayer'
        _session = session
        streaml = False
        # InfoBarMenu.__init__(self)
        # InfoBarNotifications.__init__(self)
        # InfoBarBase.__init__(self, steal_current_service=True)
        # TvInfoBarShowHide.__init__(self)
        # InfoBarSubtitleSupport.__init__(self)
        # InfoBarAudioSelection.__init__(self)
        # InfoBarSeek.__init__(self, actionmap='InfobarSeekActions')

        for x in InfoBarBase, \
                InfoBarMenu, \
                InfoBarSeek, \
                InfoBarAudioSelection, \
                InfoBarSubtitleSupport, \
                InfoBarNotifications, \
                TvInfoBarShowHide:
            x.__init__(self)

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
                                     'ColorActions',
                                     'ButtonSetupActions',
                                     'InfobarShowHideActions',
                                     'InfobarActions',
                                     'InfobarSeekActions'], {'leavePlayer': self.cancel,
                                                             'epg': self.showIMDB,
                                                             'info': self.showIMDB,
                                                             'tv': self.cicleStreamType,
                                                             'stop': self.leavePlayer,
                                                             'playpauseService': self.playpauseService,
                                                             'red': self.cicleStreamType,
                                                             'cancel': self.cancel,
                                                             'yellow': self.subtitles,
                                                             'down': self.av,
                                                             'back': self.leavePlayer}, -1)
        self.service = None
        self.name = html_conv.html_unescape(name)
        self.url = url  # .replace(':', '%3a')
        self.desc = desc
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        if '8088' in str(self.url):
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
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

    def showIMDB(self):
        text_clear = self.name
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

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
        if streaml is True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('streaml reference:   ', ref)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def subtitles(self):
        self.session.open(MessageBox, _('Please install script.module.SubSupport.'), MessageBox.TYPE_ERROR, timeout=10)

    def cicleStreamType(self):
        global streml
        streaml = False
        # from itertools import cycle, islice
        # self.servicetype = '4097'
        self.servicetype = str(config.plugins.revolution.services.value)
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(splitext(url)[-1]) == ".m3u8":
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
        if self.infoCallback is not None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
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
        with open(skin, 'r') as f:
            self.skin = f.read()
        print('self.skin: ', skin)
        f.close()
        self["poster"] = Pixmap()
        self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self['list'] = StaticText()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'DirectionActions',
                                     'ColorActions'], {'ok': self.clsgo,
                                                       'cancel': self.clsgo,
                                                       'back': self.clsgo,
                                                       'red': self.clsgo,
                                                       'green': self.clsgo}, -1)
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
        if ptr is not None:
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
                print(str(ex))
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
        self['list'].setText(_('\n\n\nCheck Connection wait please...'))
        self.timer = eTimer()
        if Utils.DreamOS():
            self.timer_conn = self.timer.timeout.connect(self.OpenCheck)
        else:
            self.timer.callback.append(self.OpenCheck)
        self.timer.start(250, 1)

    def getinfo(self):
        continfo = _("========       WELCOME     ==========\n")
        continfo += _("=======     SUPPORT ON:   ==========\n")
        continfo += _("+WWW.TIVUSTREAM.COM - WWW.CORVOBOYS.COM+\n")
        continfo += _("http://t.me/tivustream\n\n")
        continfo += _("===================================\n")
        continfo += _("NOTA BENE:\n")
        continfo += _("Le liste create ad HOC contengono indirizzi liberamente e gratuitamente\n")
        continfo += _("trovati in rete e non protetti da sottoscrizione o abbonamento.\n")
        continfo += _("Il server di riferimento strutturale ai progetti rilasciati\n")
        continfo += _("non e' fonte di alcun stream/flusso.\n")
        continfo += _("Assolutamente VIETATO utilizzare queste liste senza autorizzazione.\n")
        continfo += _("===================================\n")
        continfo += _("DISCLAIMER: \n")
        continfo += _("The lists created at HOC contain addresses freely and freely found on\n")
        continfo += _("the net and not protected by subscription or subscription.\n")
        continfo += _("The structural reference server for projects released\n")
        continfo += _("is not a source of any stream/flow.\n")
        continfo += _("Absolutely PROHIBITED to use this lists without authorization\n")
        continfo += _("===================================\n")
        return continfo

    def OpenCheck(self):
        try:
            self['list'].setText(self.getinfo())
        except:
            self['list'].setText(_('\n\n' + 'Error downloading News!'))

    def error(self, error):
        self['list'].setText(_('\n\n' + 'Server Off !') + '\n' + _('check SERVER in config'))

    def clsgo(self):
        self.session.openWithCallback(self.close, Revolmain)


class StreamTasks(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = skin_path + "/StreamTasks.xml"
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('Filmxy Movies')
        from Components.Sources.List import List
        self["movielist"] = List([])
        self["key_green"] = Label(_("Remove"))
        self["key_red"] = Label(_("Close"))
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'SleepTimerEditorActions',
                                     'ColorActions'], {"ok": self.keyOK,
                                                       "esc": self.keyClose,
                                                       "exit": self.keyClose,
                                                       "green": self.message1,
                                                       "red": self.keyClose,
                                                       "blue": self.keyBlue,
                                                       "cancel": self.keyClose}, -1)
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        self.Timer = eTimer()
        try:
            self.Timer_conn = self.Timer.timeout.connect(self.TimerFire)
        except:
            self.Timer.callback.append(self.TimerFire)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)

    def __onClose(self):
        del self.Timer

    def layoutFinished(self):
        self.Timer.startLongTimer(2)

    def TimerFire(self):
        self.Timer.stop()
        self.rebuildMovieList()

    def rebuildMovieList(self):
        if os.path.exists(Path_Movies):
            self.movielist = []
            self.getTaskList()
            self.getMovieList()
            self["movielist"].setList(self.movielist)
            self["movielist"].updateList(self.movielist)
        else:
            message = "The Movie path not configured or path not exist!!!"
            Utils.web_info(message)
            self.close()

    # def getprogress(self):
        # jobs = job_manager.getPendingJobs()
        # if len(jobs) >= 1:
            # for jobentry in jobs:
                # jobname = str(jobentry.name)
                # for video in self.downloads_all:
                    # title = str(video[1])
                    # if title == jobname:
                        # video[3] = jobentry.getStatustext()
                        # video[4] = jobentry.progress
                        # self.buildList()
                        # break

    def getTaskList(self):
        jobs = job_manager.getPendingJobs()
        if len(jobs) >= 1:
            for job in jobs:
                jobname = str(job.name)
                self.movielist.append((
                    job,
                    jobname,
                    job.getStatustext(),
                    int(100 * float(job.progress) / float(job.end)),
                    str(100 * float(job.progress) / float(job.end)) + "%"))
            if len(self.movielist) >= 1:
                self.Timer.startLongTimer(10)
        return

    def getMovieList(self):
        global filelist, file1
        file1 = False
        filelist = ''
        self.pth = ''
        if os.path.isdir(Path_Movies):
            filelist = os.listdir(Path_Movies)
        path = Path_Movies

        if filelist is not None:
            file1 = True
            filelist.sort()
            for filename in filelist:
                if os.path.isfile(path + filename):
                    if filename.endswith(".meta"):
                        continue
                    if ".m3u" in filename:
                        continue
                    if "autotimer" in filename:
                        continue
                self.movielist.append(("movie", filename, _("Finished"), 100, "100%"))

    def keyOK(self):
        global file1
        current = self["movielist"].getCurrent()
        path = Path_Movies
        desc = 'local'
        pic = ''
        if current:
            if current[0] == "movie":
                if file1 is True:
                    path = Path_Movies
                url = path + current[1]
                name = current[1]
                file1 = False
                isFile = os.path.isfile(url)
                if isFile:
                    self.session.open(Playstream2, name, url, desc)
                else:
                    self.session.open(MessageBox, _("Is Directory or file not exist"), MessageBox.TYPE_INFO, timeout=5)
            else:
                job = current[0]
                self.session.openWithCallback(self.JobViewCB, JobView, job)

    def keyBlue(self):
        pass

    def JobViewCB(self, why):
        pass

    def keyClose(self):
        self.close()

    def message1(self):
        current = self["movielist"].getCurrent()
        sel = Path_Movies + current[1]
        sel2 = self.pth + current[1]
        dom = sel
        dom2 = sel2
        self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def callMyMsg1(self, result):
        if result:
            current = self["movielist"].getCurrent()
            sel = Path_Movies + current[1]
            sel2 = self.pth + current[1]
            from os.path import exists as file_exists
            if file_exists(sel):
                if self.Timer:
                    self.Timer.stop()
                cmd = 'rm -f ' + sel
                os.system(cmd)
                self.session.open(MessageBox, sel + _(" Movie has been successfully deleted\nwait time to refresh the list..."), MessageBox.TYPE_INFO, timeout=5)
            else:
                self.session.open(MessageBox, _("The movie not exist!\nwait time to refresh the list..."), MessageBox.TYPE_INFO, timeout=5)
            self.onShown.append(self.rebuildMovieList)


class downloadJob(Job):
    def __init__(self, toolbox, cmdline, filename, filmtitle):
        print("**** downloadJob init ***")
        Job.__init__(self, filmtitle)
        self.filename = filename
        self.toolbox = toolbox
        self.retrycount = 0
        downloadTask(self, cmdline, filename, filmtitle)

    def retry(self):
        self.retrycount += 1
        self.restart()

    def cancel(self):
        self.abort()
        os.system("rm -f %s" % self.filename)

    def createMetaFile(self, filename, filmtitle):
        try:
            serviceref = eServiceReference(4097, 0, filename)
            with open("%s.meta" % (filename), "w") as f:
                f.write("%s\n%s\n%s\n%i\n" % (serviceref.toString(), filmtitle, "", time.time()))
        except Exception as e:
            print(e)
        return

    def download_finished(self, filename, filmtitle):
        self.createMetaFile(filename, filmtitle)


# class downloadJob(Job):
    # def __init__(self, url, filename, file):
        # Job.__init__(self, _("Downloading %s") % file)
        # downloadTask(self, url, filename)


class DownloaderPostcondition(Condition):
    RECOVERABLE = True

    def check(self, task):
        if task.returncode == 0 or task.error is None:
            return True
        else:
            return False
            return

    def getErrorMessage(self, task):
        return {
            task.ERROR_CORRUPT_FILE: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("DOWNLOADED FILE CORRUPTED:") + '\n%s' % task.error_message,
            task.ERROR_RTMP_ReadPacket: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("COULD NOT READ RTMP PACKET:") + '\n%s' % task.error_message,
            task.ERROR_SEGFAULT: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SEGMENTATION FAULT:") + '\n%s' % task.error_message,
            task.ERROR_SERVER: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SERVER RETURNED ERROR:") + '\n%s' % task.error_message,
            task.ERROR_UNKNOWN: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("UNKNOWN ERROR:") + '\n%s' % task.error_message
        }[task.error]


class downloadTask(Task):
    # def __init__(self, job, cmdline, filename):
    def __init__(self, job, cmdline, filename, filmtitle):
        Task.__init__(self, job, filmtitle)
        self.postconditions.append(DownloaderPostcondition())
        self.job = job
        self.toolbox = job.toolbox
        self.url = cmdline
        self.filename = filename
        self.filmtitle = filmtitle
        self.error_message = ""
        self.last_recvbytes = 0
        self.error_message = None
        self.download = None
        self.aborted = False

    def run(self, callback):
        self.callback = callback
        self.download = downloadWithProgress(self.url, self.filename)
        self.download.addProgress(self.download_progress)
        self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)
        print("[downloadTask] downloading", self.url, "to", self.filename)

    def abort(self):
        self.downloading = False
        print("[downloadTask] aborting", self.url)
        if self.download:
            self.download.stop()
        self.aborted = True

    def download_progress(self, recvbytes, totalbytes):
        if (recvbytes - self.last_recvbytes) > 10000:  # anti-flicker
            self.progress = int(100 * (float(recvbytes) / float(totalbytes)))
            self.name = _("Downloading") + ' ' + _("%d of %d kBytes") % (recvbytes / 1024, totalbytes / 1024)
            self.last_recvbytes = recvbytes

    def download_failed(self, failure_instance=None, error_message=""):
        self.downloading = False
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        Task.processFinished(self, 1)

    def download_finished(self, string=""):
        self.downloading = False
        if self.aborted:
            self.finish(aborted=True)
        else:
            Task.processFinished(self, 0)

    def afterRun(self):
        if self.getProgress() == 0:
            try:
                self.toolbox.download_failed()
            except:
                pass
        elif self.getProgress() == 100:
            try:
                self.toolbox.download_finished()
                self.downloading = False
                message = "Movie successfully transfered to your HDD!" + "\n" + self.filename
                Utils.web_info(message)
            except:
                pass
        pass


class AutoStartTimertvsl:

    def __init__(self, session):
        self.session = session
        global _firstStart
        print("*** running AutoStartTimertvsl ***")
        if _firstStarttvsl:
            self.runUpdate()

    def runUpdate(self):
        print("*** running update ***")
        try:
            from . import Update
            Update.upd_done()
            _firstStarttvsl = False
        except Exception as e:
            print('error tivustream lite', str(e))


def autostart(reason, session=None, **kwargs):
    print("*** running autostart ***")
    global autoStartTimertvsl
    global _firstStarttvsl
    if reason == 0:
        if session is not None:
            _firstStarttvsl = True
            autoStartTimertvsl = AutoStartTimertvsl(session)
    return


def main(session, **kwargs):
    try:
        session.open(Revolmain)
    except:
        import traceback
        traceback.print_exc()


def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [(desc_plug, main, title_plug, 44)]
    else:
        return []


def mainmenu(session, **kwargs):
    main(session, **kwargs)


def Plugins(**kwargs):
    ico_path = 'logo.png'
    if not os.path.exists('/var/lib/dpkg/status'):
        ico_path = res_plugin_path + 'pics/logo.png'
    result = [PluginDescriptor(name=desc_plug, description=title_plug, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=desc_plug, description=title_plug, where=PluginDescriptor.WHERE_PLUGINMENU, icon=ico_path, fnc=main)]
    return result
