#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             04/07/2023               *
*       skin by MMark                  *
****************************************
Info http://t.me/tivustream
'''
from __future__ import print_function
from . import (
    _,
    logdata,
    paypal,
    isDreamOS,
    installer_url,
    developer_url,
    b64decoder,
    UrlLst,
)
from .resolver import Utils
from .resolver import html_conv
from .resolver.Console import Console as xConsole

from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import (MultiContentEntryPixmapAlphaTest, MultiContentEntryText)
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import (ServiceEventTracker, InfoBarBase)
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Components.Task import (Task, Condition, Job, job_manager)
from Components.config import (
    ConfigEnableDisable,
    ConfigDirectory,
    ConfigSelection,
    getConfigListEntry,
    configfile,
    config,
    ConfigYesNo,
    ConfigSubsection,
)
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import (
    InfoBarSubtitleSupport,
    InfoBarSeek,
    InfoBarAudioSelection,
    InfoBarMenu,
    InfoBarNotifications,
)
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.TaskView import JobView
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists, SCOPE_PLUGINS, resolveFilename
from Tools.Downloader import downloadWithProgress
from enigma import (
    RT_HALIGN_LEFT,
    RT_VALIGN_CENTER,
    eListboxPythonMultiContent,
    ePicLoad,
    eServiceReference,
    eTimer,
    gFont,
    gPixmapPtr,
    getDesktop,
    iPlayableService,
    loadPNG,
)
from os.path import splitext
from requests import get, exceptions
from requests.exceptions import HTTPError
from twisted.internet.reactor import callInThread
from twisted.web.client import downloadPage
from datetime import datetime
import codecs
import json
import os
import re
import six
import sys
import time

global nextmodule, search, pngori, pictmp, Path_Movies, Path_Cache

PY3 = False
PY3 = sys.version_info.major >= 3

if PY3:
    print('six.PY3: True ')
try:
    from urllib.parse import urlparse
    from urllib.request import urlopen, Request
    from urllib.error import URLError
    PY3 = True
except ImportError:
    from urlparse import urlparse
    from urllib2 import urlopen, Request
    from urllib2 import URLError


search = False
_session = None
streamlink = False


if Utils.isStreamlinkAvailable:
    streamlink = True


def threadGetPage(url=None, file=None, key=None, success=None, fail=None, *args, **kwargs):
    print('[threadGetPage] url, file, key, args, kwargs', url, "   ", file, "   ", key, "   ", args, "   ", kwargs)
    try:
        url = url.replace('https', 'http')
        response = get(url, verify=False)
        response.raise_for_status()
        if file is None:
            success(response.content)
        elif key is not None:
            success(response.content, file, key)
        else:
            success(response.content, file)
    except HTTPError as httperror:
        print('[threadGetPage] Http error: ', httperror)
        # fail(error)  # E0602 undefined name 'error'
    except exceptions.RequestException as error:
        print(error)


currversion = '2.1'  # getversioninfo()
Path_Tmp = "/tmp"
plugin_path = '/usr/lib/enigma2/python/Plugins/Extensions/revolution'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding': 'deflate'}

title_plug = 'TVS Pro Lite V. %s' % currversion
desc_plug = 'TVS Pro Lite Revolution'
ico_path = os.path.join(plugin_path, 'logo.png')
pictmp = os.path.join(Path_Tmp, "poster.jpg")
res_plugin_path = os.path.join(plugin_path, 'res/')
pngori = os.path.join(plugin_path, 'res/pics/fulltop.jpg')
piccons = os.path.join(plugin_path, 'res/img/')
imgjpg = ("nasa.jpg", "nasa1.jpg", "nasa2.jpg")
no_cover = os.path.join(piccons, 'backg.png')
piconinter = os.path.join(piccons, 'inter.png')
piconlive = os.path.join(piccons, 'tv.png')
piconmovie = os.path.join(piccons, 'cinema.png')
piconsearch = os.path.join(piccons, 'search.png')
piconseries = os.path.join(piccons, 'series.png')
nextpng = 'next.png'
prevpng = 'prev.png'

PanelMain = [('SEARCH'), ('LIVE'), ('MOVIE'), ('SERIES'), ('INTERNATIONAL')]


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


sslverify = False
try:
    from twisted.internet import ssl
    from twisted.internet._sslverify import ClientTLSOptions
    sslverify = True
except ImportError:
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


screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    path_skin = os.path.join(plugin_path, 'res/skins/uhd')
elif screenwidth.width() == 1920:
    path_skin = os.path.join(plugin_path, 'res/skins/fhd')
else:
    path_skin = os.path.join(plugin_path, 'res/skins/hd')
if isDreamOS:
    path_skin = os.path.join(path_skin, 'dreamOs')

logdata("path picons: ", str(path_skin))
VIDEO_ASPECT_RATIO_MAP = {0: "4:3 Letterbox", 1: "4:3 PanScan", 2: "16:9", 3: "16:9 Always", 4: "16:10 Letterbox", 5: "16:10 PanScan", 6: "16:9 Letterbox"}
VIDEO_FMT_PRIORITY_MAP = {"38": 1, "37": 2, "22": 3, "18": 4, "35": 5, "34": 6}


def piconlocal(name):

    pngs = [
        ["tv", "movie"],
        ["commedia", "commedia"],
        ["comedy", "commedia"],
        ["thriller", "thriller"],
        ["family", "family"],
        ["famiglia", "family"],
        ["azione", "azione"],
        ["dramma", "dramma"],
        ["drama", "dramma"],
        ["western", "western"],
        ["biografico", "biografico"],
        ["storia", "biografico"],
        ["documentario", "biografico"],
        ["romantico", "romantico"],
        ["romance", "romantico"],
        ["horror", "horror"],
        ["musica", "musical"],
        ["show", "musical"],
        ["guerra", "guerra"],
        ["bambini", "bambini"],
        ["bianco", "bianconero"],
        ["tutto", "toto"],
        ["cartoni", "cartoni"],
        ["bud", "budterence"],
        ["documentary", "documentary"],
        ["crime", "crime"],
        ["mystery", "mistery"],
        ["mistero", "mistery"],
        ["giallo", "mistery"],
        ["fiction", "fiction"],
        ["adventure", "mistery"],
        ["action", "azione"],
        ["007", "007"],
        ["sport", "sport"],
        ["teatr", "teatro"],
        ["variet", "teatro"],
        ["giallo", "teatro"],
        ["extra", "extra"],
        ["sexy", "fantasy"],
        ["erotic", "fantasy"],
        ["animazione", "bambini"],
        ["search", "search"],

        ["abruzzo", "regioni/abruzzo"],
        ["basilicata", "regioni/basilicata"],
        ["calabria", "regioni/calabria"],
        ["campania", "regioni/campania"],
        ["emilia", "regioni/emiliaromagna"],
        ["friuli", "regioni/friuliveneziagiulia"],
        ["lazio", "regioni/lazio"],
        ["liguria", "regioni/liguria"],
        ["lombardia", "regioni/lombardia"],
        ["marche", "regioni/marche"],
        ["molise", "regioni/molise"],
        ["piemonte", "regioni/piemonte"],
        ["puglia", "regioni/puglia"],
        ["sardegna", "regioni/sardegna"],
        ["sicilia", "regioni/sicilia"],
        ["toscana", "regioni/toscana"],
        ["trentino", "regioni/trentino"],
        ["umbria", "regioni/umbria"],
        ["veneto", "regioni/veneto"],
        ["aosta", "regioni/valledaosta"],
        ["mediaset", "mediaset"],
        ["nazionali", "nazionali"],
        ["news", "news"],
        ["rai", "rai"],
        ["webcam", "relaxweb"],
        ["relax", "relaxweb"],
        ["vecchi", "vecchi"],
        ["muto", "vecchi"],
        ["'italiani", "movie"],
        ["fantascienza", "fantascienza"],
        ["fantasy", "fantasy"],
        ["fantasia", "fantasia"],
        ["film", "movie"],
        ["samsung", "samsung"],
        ["plutotv", "plutotv"]
    ]

    for png in pngs:
        piconlocal = 'backg.png'
        if png[0] in str(name).lower():
            piconlocal = str(png[1]) + ".png"
            break

    if 'prev' in name.lower():
        piconlocal = prevpng
    elif 'next' in name.lower():
        piconlocal = nextpng
    path = os.path.join(piccons, piconlocal)
    print('>>>>>>>> ' + path)
    return str(path)


EXTDOWN = {
    ".avi": "movie",
    ".divx": "movie",
    ".mpg": "movie",
    ".mpeg": "movie",
    ".mkv": "movie",
    ".mov": "movie",
    ".m4v": "movie",
    ".flv": "movie",
    ".m3u8": "movie",
    ".relinker": "movie",
    ".mp4": "movie",
}


class rvList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if screenwidth.width() == 2560:
            self.l.setItemHeight(60)
            textfont = int(42)
            self.l.setFont(0, gFont('Regular', textfont))
        elif screenwidth.width() == 1920:
            self.l.setItemHeight(50)
            textfont = int(30)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(50)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))

    def __len__(self):
        if hasattr(self.l, 'getItems'):
            return len(self.l.getItems())
        elif hasattr(self.l, 'list'):
            return len(self.l.list)
        else:
            return 0


def rvListEntry(name, url, idx='None'):
    res = [(name, url, idx)]  # Aggiungi l'URL alla tupla
    pngs = os.path.join(plugin_path, 'res/pics/tv.png')
    if any(s in name.lower() for s in EXTRAD):
        pngs = os.path.join(plugin_path, 'res/pics/radio.png')
    elif any(s in name.lower() for s in EXTCAM):
        pngs = os.path.join(plugin_path, 'res/pics/webcam.png')
    elif any(s in name.lower() for s in EXTMUS):
        pngs = os.path.join(plugin_path, 'res/pics/music.png')
    elif any(s in name.lower() for s in EXTSPOR):
        pngs = os.path.join(plugin_path, 'res/pics/sport.png')

    if screenwidth.width() == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(50, 50), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(90, 0), size=(1200, 60), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 8), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))

    return res


def showlist(data, list):
    idx = 0
    plist = []
    for line in data:
        name = data[idx]
        print('Nameee=', name)
        url = 'None'
        plist.append(rvListEntry(str(name), url, idx))
        idx += 1
    list.setList(plist)


modechoices = [("4097", _("IPTV(4097)")),
               ("1", _("Dvb(1)"))]

if os.path.exists("/usr/bin/gstplayer"):
    modechoices.append(("5001", _("Gstreamer(5001)")))
if os.path.exists("/usr/bin/exteplayer3"):
    modechoices.append(("5002", _("Exteplayer3(5002)")))
if os.path.exists("/usr/sbin/streamlinksrv"):
    modechoices.append(("5002", _("Streamlink(5002)")))
if os.path.exists("/usr/bin/apt-get"):
    modechoices.append(("8193", _("isDreamOS GStreamer(8193)")))

config.plugins.revolution = ConfigSubsection()
cfg = config.plugins.revolution
cfg.services = ConfigSelection(default='4097', choices=modechoices)
cfg.cachefold = ConfigDirectory(default='/media/hdd')
cfg.movie = ConfigDirectory("/media/hdd/movie")

try:
    from Components.UsageConfig import defaultMoviePath
    downloadpath = defaultMoviePath()
    cfg.movie = ConfigDirectory(default=downloadpath)
except:
    if os.path.exists("/usr/bin/apt-get"):
        cfg.movie = ConfigDirectory(default='/media/hdd/movie')


Path_Movies = str(cfg.movie.value)
Path_Cache = str(cfg.cachefold.value)


if not os.path.exists(Path_Cache):
    try:
        os.makedirs(Path_Cache)
    except OSError as e:
        print(('Error creating directory %s:\n%s') % (Path_Cache, e))
logdata("path picons: ", str(Path_Cache))


def returnIMDB(text_clear):
    TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
    tmdb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('tmdb'))
    IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
    text = html_conv.html_unescape(text_clear)
    if os.path.exists(TMDB):
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", str(e))
        return True

    elif os.path.exists(tmdb):
        try:
            from Plugins.Extensions.tmdb.plugin import tmdb
            _session.open(tmdb.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", str(e))
        return True

    elif os.path.exists(IMDb):
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            imdb(_session, text)
        except Exception as e:
            print("[XCF] imdb: ", str(e))
        return True
    else:
        _session.open(MessageBox, text, MessageBox.TYPE_INFO)
        return True
    return False


EXTRAD = "radio", "radyo", "mix", "fm", "kbit", "rap", "metal", "alternative"
EXTXXX = "adult", "xxx"
EXTCAM = "webcam", "webcams"
EXTMUS = "music", "mtv", "deluxe", "djing", "fashion", "kiss", "mpeg", "sluhay", "stingray", "techno", "viva", "country", "vevo"
EXTSPOR = "spor", "boxing", "racing", "fight", "golf", "knock", "harley", "futbool", "motor", "nba", "nfl", "bull", "poker", "billiar", "fite"
EXTRLX = "relax", "nature", "escape"
EXTMOV = "movie", "film"


class myconfig(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(path_skin, 'myconfig.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = title_plug
        self.setTitle(title_plug)
        self.onChangedEntry = []
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('- - - -'))
        self['key_yellow'] = Button(_('Choice'))
        self["key_blue"] = Button(_('Empty Cache'))
        self["paypal"] = Label()
        self['info'] = Label()
        self['title'] = Label(title_plug)
        self['description'] = Label()
        self["setupActions"] = ActionMap(['OkCancelActions',
                                          'DirectionActions',
                                          'ColorActions',
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
        self.createSetup()
        self.onLayoutFinish.append(self.layoutFinished)
        if self.setInfo not in self['config'].onSelectionChanged:
            self['config'].onSelectionChanged.append(self.setInfo)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)
        self.setTitle(self.setup_title)
        if not os.path.exists('/tmp/currentip'):
            os.system('wget -qO- http://ipecho.net/plain > /tmp/currentip')
        currentip1 = open('/tmp/currentip', 'r')
        currentip = currentip1.read()
        self['info'].setText(_('Settings Revolution\nYour current IP is %s') % currentip)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None and len(callback):
            self['config'].getCurrent()[1].value = callback
            self['config'].invalidate(self['config'].getCurrent())

    def KeyText(self):
        sel = self['config'].getCurrent()
        if sel:
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self['config'].getCurrent()[0], text=self['config'].getCurrent()[1].value)

    def cachedel(self):
        fold = os.path.join(str(cfg.cachefold.value), "revolution/pic")
        Utils.cachedel(fold)
        self.mbox = self.session.open(MessageBox, _('All cache fold are empty!'), MessageBox.TYPE_INFO, timeout=5)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        self.list.append(getConfigListEntry(_("Set the path Movie folder"), cfg.movie, _("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required")))
        self.list.append(getConfigListEntry(_("Set the path to the Cache folder"), cfg.cachefold, _("Press Ok to select the folder containing the picons files")))
        self.list.append(getConfigListEntry(_('Services Player Reference type'), cfg.services, _("Configure Service Player Reference")))
        self['config'].list = self.list
        self["config"].l.setList(self.list)
        self.setInfo()

    def setInfo(self):
        try:
            sel = self['config'].getCurrent()[2]
            if sel:
                self['description'].setText(str(sel))
            else:
                self['description'].setText(_('SELECT YOUR CHOICE'))
            return
        except Exception as e:
            print("Error ", e)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.createSetup()

    def msgok(self):
        if self['config'].isChanged():
            for x in self['config'].list:
                x[1].save()
            self.mbox = self.session.open(MessageBox, _('Settings saved correctly!'), MessageBox.TYPE_INFO, timeout=5)
            self.close()
        else:
            self.close()

    def restartenigma(self, result):
        if result:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close(True)

    def changedEntry(self):
        self['key_green'].instance.setText(_('Save') if self['config'].isChanged() else '- - - -')
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

    def Ok_edit(self):
        sel = self['config'].getCurrent()[1]
        if sel and sel == cfg.cachefold:
            self.setting = 'cachefold'
            self.openDirectoryBrowser(cfg.cachefold.value)
        if sel and sel == cfg.movie:
            self.setting = 'moviefold'
            self.openDirectoryBrowser(cfg.movie.value)
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
                minFree=15
            )
        except Exception as e:
            print('openDirectoryBrowser get failed: ', e)

    def openDirectoryBrowserCB(self, path=None):
        if path is not None:
            if self.setting == 'cachefold':
                cfg.cachefold.setValue(path)
            if self.setting == 'moviefold':
                cfg.movie.setValue(path)
        return

    def save(self):
        if self['config'].isChanged():
            for x in self['config'].list:
                x[1].save()
            self.mbox = self.session.open(MessageBox, _('Settings saved correctly!'), MessageBox.TYPE_INFO, timeout=5)
            cfg.save()
            configfile.save()
        self.close()

    def extnok(self, answer=None):
        from Screens.MessageBox import MessageBox
        if answer is None:
            if self["config"].isChanged():
                self.session.openWithCallback(self.extnok, MessageBox, _("Really close without saving settings?"))
            else:
                self.close()
        elif answer:
            for x in self["config"].list:
                x[1].cancel()
            self.close()
        return


class Revolmain(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        global nextmodule
        nextmodule = 'Revolmain'
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = ('HOME REVOLUTION')
        self['title'] = Label(title_plug)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['poster'] = Pixmap()
        self['desc'] = StaticText()
        self['info'] = Label()
        self['info'].setText('Select')
        self['key_red'] = Button(_('Exit'))
        self['key_yellow'] = Button(_('Update'))
        self['key_yellow'].hide()
        self.currentList = 'list'
        self.Update = False

        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'HotkeyActions',
                                     'InfobarEPGActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'left': self.left,
                                                           'right': self.right,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
                                                           'showEventInfoPlugin': self.update_dev,
                                                           'menu': self.goConfig,
                                                           'info_long': self.update_dev,
                                                           'infolong': self.update_dev,
                                                           'yellow': self.update_me,
                                                           'yellow_long': self.update_dev,
                                                           'green': self.okRun,
                                                           'cancel': self.closerm,
                                                           'red': self.closerm}, -1)
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/status'):
            self.timer_conn = self.timer.timeout.connect(self.check_vers)
        else:
            self.timer.callback.append(self.check_vers)
        self.timer.start(500, 1)
        self.onLayoutFinish.append(self.updateMenuList)
        self.onLayoutFinish.append(self.__layoutFinished)

    def check_vers(self):
        remote_version = '0.0'
        remote_changelog = ''
        req = Request(b64decoder(installer_url), headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req).read()
        if PY3:
            data = page.decode("utf-8")
        else:
            data = page.encode("utf-8")
        if data:
            lines = data.split("\n")
            for line in lines:
                if line.startswith("version"):
                    remote_version = line.split("=")
                    remote_version = line.split("'")[1]
                if line.startswith("changelog"):
                    remote_changelog = line.split("=")
                    remote_changelog = line.split("'")[1]
                    break
        self.new_version = remote_version
        self.new_changelog = remote_changelog
        if currversion < remote_version:
            self.Update = True
            self['key_yellow'].show()
            self.session.open(MessageBox, _('New version %s is available\n\nChangelog: %s\n\nPress info_long or yellow_long button to start force updating.') % (self.new_version, self.new_changelog), MessageBox.TYPE_INFO, timeout=5)

    def update_me(self):
        if self.Update is True:
            self.session.openWithCallback(self.install_update, MessageBox, _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (self.new_version, self.new_changelog), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _("Congrats! You already have the latest version..."),  MessageBox.TYPE_INFO, timeout=4)

    def update_dev(self):
        try:
            req = Request(b64decoder(developer_url), headers={'User-Agent': 'Mozilla/5.0'})
            page = urlopen(req).read()
            data = json.loads(page)
            remote_date = data['pushed_at']
            strp_remote_date = datetime.strptime(remote_date, '%Y-%m-%dT%H:%M:%SZ')
            remote_date = strp_remote_date.strftime('%Y-%m-%d')
            self.session.openWithCallback(self.install_update, MessageBox, _("Do you want to install update ( %s ) now?") % (remote_date), MessageBox.TYPE_YESNO)
        except Exception as e:
            print('error xcons:', e)

    def install_update(self, answer=False):
        if answer:
            cmd1 = 'wget -q "--no-check-certificate" ' + b64decoder(installer_url) + ' -O - | /bin/sh'
            self.session.open(xConsole, 'Upgrading...', cmdlist=[cmd1], finishedCallback=self.myCallback, closeOnSuccess=False)
        else:
            self.session.open(MessageBox, _("Update Aborted!"),  MessageBox.TYPE_INFO, timeout=3)

    def myCallback(self, result=None):
        print('result:', result)
        return

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.load_poster()

    def closerm(self):
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
        self.keyNumberGlobalCB(self['list'].getSelectionIndex())

    def keyNumberGlobalCB(self, idx):
        i = len(self.menu_list)
        if i < 0:
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
                print('error infobox ', e)

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
            sel = self['list'].getSelectionIndex()
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
                if os.path.exists('/var/lib/dpkg/status'):
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
                if os.path.exists('/var/lib/dpkg/status'):
                    if self.picload.startDecode(pixmaps, False) == 0:
                        ptr = self.picload.getData()
                else:
                    if self.picload.startDecode(pixmaps, 0, 0, False) == 0:
                        ptr = self.picload.getData()
                if ptr is not None:
                    self['poster'].instance.setPixmap(ptr)
                    self['poster'].show()
                return
        except Exception as e:
            print(e)

    def search_text(self, name, url, pic):
        self.namex = name
        self.urlx = url
        self.picx = pic
        self.session.openWithCallback(self.filterChannels, VirtualKeyBoard, title=_("Filter this category..."), text='')

    def filterChannels(self, result=None):
        if result:
            global search
            pic = self.picx
            name = str(result)
            url = self.urlx + str(result)
            try:
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


class live_stream(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self["poster"].hide()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()

        self.name = name
        self.url = url
        self.pic = pic
        self.type = self.name
        self.downloading = False
        self.currentList = 'list'

        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
        name = self.name
        url = self.url
        pic = self.pic
        info = ""
        content = Utils.ReadUrl2(url, referer)
        if PY3:
            content = six.ensure_str(content)
        y = json.loads(content)
        i = 0
        while i < 50:

            try:
                if 'movie' in nextmodule:
                    nextmodule = "Videos4"
                    self.names.append('Search')
                    self.urls.append("https://tivustream.website/php_filter/kodi19/kodi19.php?mode=movie&query=")
                    self.pics.append(str(piconsearch))
                    self.infos.append(str('Search Movies'))
                    i += 1
                if 'live' in nextmodule:
                    nextmodule = "Videos3"
                if 'series' in nextmodule:
                    nextmodule = 'Videos1'
                print('=====================')
                print(nextmodule)
                print('=====================')
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = str(y["items"][i]["externallink"])
                pic = str(y["items"][i]["thumbnail"])
                if _('serie') not in self.name.lower():
                    pic = piconlocal(name)
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                info = info.replace('---', ' ')

                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))

                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break
        showlist(self.names, self['list'])
        self.__layoutFinished()

    def okRun(self):
        global search
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        # if idx is not None or idx != -1:
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        if 'Search' in str(name):
            search = True
            self.search_text(name, url, pic)
        # live
        if nextmodule == 'Videos3':
            # openCat
            self.session.open(video3, name, url, pic, nextmodule)
        # movie
        if 'listMovie' in str(url):
            self.session.open(nextvideo4, name, url, pic, nextmodule)
        else:
            if 'movieId' in str(url):
                self.session.open(video5, name, url, pic, nextmodule)
        # series
        if '&page' in str(url) and nextmodule == 'Videos1':
            self.session.open(nextvideo1, name, url, pic, nextmodule)

        if '&page' not in str(url) and nextmodule == 'Videos1':
            if 'tvseriesId' in str(url):
                self.session.open(video6, name, url, pic, nextmodule)
            else:
                print('self.list=', self.menu_list)
                self.session.open(Playstream1, name, url, desc, pic, idx, self.menu_list)

    def search_text(self, name, url, pic):
        self.namex = name
        self.urlx = url
        self.picx = pic
        self.session.openWithCallback(self.filterChannels, VirtualKeyBoard, title=_("Filter this category..."), text='')

    def filterChannels(self, result=None):
        if result:
            global search
            pic = self.picx
            name = str(result)
            url = self.urlx + str(result)
            try:
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        if idx and (idx != '' or idx > -1):
            self[self.currentList].up()
            self.__layoutFinished()
        else:
            return

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def download(self, link, name):
        if PY3:
            link = link.encode()
        callInThread(threadGetPage, url=link, file=None, success=name, fail=self.downloadError)

    def getPoster1(self, output):
        with open(pictmp, 'wb') as f:
            f.write(output)
        self.showPoster1(pictmp)

    def showPoster1(self, poster1):
        if fileExists(poster1):
            self["poster"].instance.setPixmapFromFile(poster1)
            self['poster'].show()
        return

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            pixmaps = self.pics[idx]
            if 'series' not in str(url):
                pixmaps = piconlocal(name)
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    return
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    self.download(pixmaps, self.getPoster1)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

    def downloadPic(self, data, pixmaps):
        if os.path.exists(pixmaps):
            try:
                self.showPoster1(pixmaps)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(no_cover):
                self.showPoster1(no_cover)
        except Exception as e:
            print(e)


class video6(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()

        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'

        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        i = 0
        while i < 50:
            try:
                name = ""
                url = ""
                pic = ""
                info = ''

                print('=====================')
                print(nextmodule)
                print('=====================')
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = (y["items"][i]["link"])
                pic = (y["items"][i]["thumbnail"])
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break

            nextmodule = "Videos1"
            showlist(self.names, self['list'])
            self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        if idx and (idx != '' or idx > -1):
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            desc = self.infos[idx]
            if '&page' in str(url) and nextmodule == 'Videos1':  # wooork
                self.session.open(nextvideo1, name, url, pic, nextmodule)
            if '&page' not in str(url) and nextmodule == 'Videos1':  # in series not appears
                if 'tvseriesId' in str(url):
                    self.session.open(nextvideo1, name, url, pic, nextmodule)
                else:
                    print('self.list=', self.menu_list)
                    self.session.open(Playstream1, name, url, desc, pic, idx, self.menu_list)
            else:
                print('bhoo .mp4???')
                return

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos1'
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
        except Exception as e:
            self.poster_resize(no_cover)
            print(e)

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class nextvideo3(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()

        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'

        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

    def readJsonFile(self):

        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        referer = 'https://tivustream.website'
        content = Utils.ReadUrl2(self.url, referer)
        if PY3:
            content = six.ensure_str(content)

        y = json.loads(content)
        i = 0
        while i < 50:
            name = ""
            url = ""
            pic = ""
            info = ''
            try:
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = (y["items"][i]["link"])
                pic = (y["items"][i]["thumbnail"])
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break
        showlist(self.names, self['list'])
        self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()

        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        if '&page' in str(url) and nextmodule == 'Videos3':
            self.session.open(video3, name, url, pic, nextmodule)
        else:
            print('self.list=', self.list)
            self.session.open(Playstream1, name, url, desc, pic, idx, self.menu_list)

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos3'

        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
            print(ex)

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
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class nextvideo1(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()

        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'

        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        i = 0
        while i < 50:
            name = ""
            url = ""
            pic = ""
            info = ''
            try:
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = str(y["items"][i]["externallink"])
                pic = str(y["items"][i]["thumbnail"])
                if _('serie') not in self.name.lower():
                    pic = piconlocal(name)
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break
        nextmodule = "Videos1"
        showlist(self.names, self['list'])
        self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        if '&page' in str(url) and nextmodule == 'Videos1':  # wooork
            self.session.open(video6, name, url, pic, nextmodule)
        if '&page' not in str(url) and nextmodule == 'Videos1':  # in series not appears
            if 'tvseriesId' in str(url):
                self.session.open(video6, name, url, pic, nextmodule)
            else:
                print('self.list=', self.menu_list)
                self.session.open(Playstream1, name, url, desc, pic, idx, self.menu_list)
        else:
            print('bhoo .mp4???')
            return

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos1'
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
            print(ex)

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class video3(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        while i < 50:
            name = ""
            url = ""
            pic = ""
            try:
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = (y["items"][i]["link"])
                pic = (y["items"][i]["thumbnail"])
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break

        showlist(self.names, self['list'])
        # self.list = [(item[0], item[1]) for item in self.list]

        self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        desc = self.infos[idx]
        if '&page' in str(url) and nextmodule == 'Videos3':
            self.session.open(nextvideo3, name, url, pic, nextmodule)
        else:
            print('self.list=', self.list)
            self.session.open(Playstream1, name, url, desc, pic, idx, self.menu_list)

    def cancel(self):
        global nextmodule
        if nextmodule == 'Videos3':
            nextmodule = 'Videos3'
        else:
            nextmodule = 'live'
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
            print(ex)

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
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class video4(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        i = 0
        while i < 50:
            name = ""
            url = ""
            pic = ""
            info = ''
            try:
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = str(y["items"][i]["externallink"])
                pic = str(y["items"][i]["thumbnail"])
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break
        nextmodule = "Videos4"
        showlist(self.names, self['list'])
        self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        if '&page' in str(url):
            self.session.open(nextvideo4, name, url, pic, nextmodule)
        if 'listMovie' in str(url):
            self.session.open(nextvideo4, name, url, pic, nextmodule)
        if 'movieId' in str(url):
            self.session.open(video5, name, url, pic, nextmodule)

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
            print(ex)

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class nextvideo4(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        i = 0
        while i < 50:
            name = ""
            url = ""
            pic = ""
            info = ""
            try:
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = str(y["items"][i]["externallink"])
                pic = str(y["items"][i]["thumbnail"])
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break
        nextmodule = "Videos4"
        showlist(self.names, self['list'])
        self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        pic = self.pics[idx]
        if '&page' in str(url):
            self.session.open(video4, name, url, pic, nextmodule)
        if 'listMovie' in str(url):
            self.session.open(video4, name, url, pic, nextmodule)
        else:
            if 'movieId' in str(url):
                self.session.open(video5, name, url, pic, nextmodule)

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
            print(ex)

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class video5(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'revall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []

        self.menu_list = []
        self.list = rvList([])
        self['list'] = self.list

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['info'] = Label(name)
        self['pth'] = Label()
        self['pth'].setText(_('Cache folder ') + Path_Cache)
        self['desc'] = StaticText()
        self["poster"] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()
        self.name = name
        self.url = url
        self.pic = pic
        self.downloading = False
        self.currentList = 'list'
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'ChannelSelectBaseActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'red': self.cancel,
                                                           'up': self.up,
                                                           'down': self.down,
                                                           'prevBouquet': self.down,
                                                           'nextBouquet': self.up,
                                                           'channelDown': self.down,
                                                           'channelUp': self.up,
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
        # self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
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
            if i > -1:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                self['desc'].setText(info)
        except Exception as e:
            print(e)

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
        while i < 10:
            name = self.name
            url = self.url
            pic = self.pic
            info = ''
            try:
                name = str(y["items"][i]["title"])
                name = re.sub(r'\[.*?\]', "", name)
                name = Utils.cleanName(name)
                url = (y["items"][i]["link"])
                pic = (y["items"][i]["thumbnail"])
                info = str(y["items"][i]["info"])
                info = re.sub(r'\r\n', '', info)
                self.names.append(name)
                self.urls.append(url)
                self.pics.append(pic)
                self.infos.append(html_conv.html_unescape(info))
                i += 1

                self.menu_list.append((name, url, i))

            except Exception as e:
                print(e)
                break

        showlist(self.names, self['list'])
        self.__layoutFinished()

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        desc = self.infos[idx]
        pic = self.pics[idx]
        print('self.list=', self.menu_list)
        self.session.open(Playstream1, name, url, desc, pic, idx, self.menu_list)

    def cancel(self):
        global nextmodule
        nextmodule = 'Videos4'
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.__layoutFinished()

    def down(self):
        self[self.currentList].down()
        self.__layoutFinished()

    def left(self):
        self[self.currentList].pageUp()
        self.__layoutFinished()

    def right(self):
        self[self.currentList].pageDown()
        self.__layoutFinished()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            pixmaps = self.pics[idx]
            pixmaps = six.ensure_binary(self.pics[idx])
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
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
        except Exception as e:
            self.poster_resize(no_cover)
            print(e)

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
        # if self.picload:
        self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
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
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {
            "toggleShow": self.OkPressed,
            "hide": self.hide
        }, 0)

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
            self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            self.hideTimer.start(3000, True)
        elif hasattr(self, "pvrStateDialog"):
            self.hideTimer.stop()
        self.skipToggleShow = False

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


class Playstream1(Screen):
    def __init__(self, session, name, url, desc, pic, idx, menu_list):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(path_skin, 'Playstream1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.setup_title = (title_plug)
        self['title'] = Label(title_plug)
        self['list'] = rvList([])
        self['info'] = Label()
        self['info'].setText(name)
        self['poster'] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Select'))
        self['key_yellow'] = Button(_('Movie'))
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()

        self.name1 = name
        self.url = url
        self.desc = desc
        self.pic = pic
        self.index = idx
        self.menu_list = menu_list

        self.downloading = False
        self['actions'] = ActionMap(['MoviePlayerActions',
                                     'MovieSelectionActions',
                                     'MediaPlayerActions',
                                     'EPGSelectActions',
                                     'MediaPlayerSeekActions',
                                     'DirectionActions',
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

        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.load_poster)
        except:
            self.leftt.callback.append(self.load_poster)
        self.leftt.start(200, True)
        self.onLayoutFinish.append(self.openTest)
        return

    def taskManager(self):
        self.session.open(StreamTasks)

    def runRec(self):
        self.namem3u = self.name1
        self.urlm3u = self.url
        if self.downloading is True:
            self.session.open(MessageBox, _('You are already downloading!!!'), MessageBox.TYPE_INFO, timeout=5)
            return
        else:
            if '.mp4' or '.mkv' or '.flv' or '.avi' in self.urlm3u:
                self.session.openWithCallback(self.download_m3u, MessageBox, _("DOWNLOAD VIDEO?\n%s" % self.namem3u), type=MessageBox.TYPE_YESNO, timeout=5, default=False)
            else:
                self.downloading = False
                self.session.open(MessageBox, _('Only VOD Movie allowed or not .ext Filtered!!!'), MessageBox.TYPE_INFO, timeout=5)

    def download_m3u(self, result=None):
        if result:
            path = urlparse(self.urlm3u).path
            ext = splitext(path)[1]
            if ext != '.mp4' or ext != '.mkv' or ext != '.avi' or ext != '.flv':  # or ext != 'm3u8':
                ext = '.mp4'
            fileTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', self.namem3u)
            fileTitle = re.sub(r' ', '_', fileTitle)
            fileTitle = re.sub(r'_+', '_', fileTitle)
            fileTitle = fileTitle.replace("(", "_").replace(")", "_").replace("#", "").replace("+", "_").replace("\'", "_").replace("'", "_").replace("!", "_").replace("&", "_")
            fileTitle = fileTitle.replace(" ", "_").replace(":", "").replace("[", "").replace("]", "").replace("!", "_").replace("&", "_")
            fileTitle = fileTitle.lower() + ext
            self.in_tmp = os.path.join(Path_Movies, fileTitle)
            self.downloading = True
            try:
                f = open(self.in_tmp, 'wb')
                f.close()
                cmd = "wget -U 'Enigma2 - Revolution Plugin' -c '%s' -O '%s'" % (self.urlm3u, self.in_tmp)
                if "https" in str(self.urlm3u):
                    cmd = "wget --no-check-certificate -U 'Enigma2 - Revolution Plugin' -c '%s' -O '%s'" % (self.urlm3u, self.in_tmp)
                job_manager.AddJob(downloadJob(self, cmd, self.in_tmp, fileTitle))

            except URLError as e:
                self.session.openWithCallback(self.ImageDownloadCB, MessageBox, _("Download Failed !!") + "\n%s" % e, type=MessageBox.TYPE_ERROR)
                self.downloading = False
        else:
            self.downloading = False

    def ImageDownloadCB(self, ret=None):
        if ret:
            return
        if job_manager.active_job:
            job_manager.active_job = None
            self.close()
            return
        if len(job_manager.failed_jobs) == 0:
            self.LastJobView()
        else:
            self.downloading = False
            self.session.open(MessageBox, _("Download Failed !!"), type=MessageBox.TYPE_ERROR)

    def downloadProgress(self, recvbytes, totalbytes):
        self['info'].setText(_('Download...'))
        self["progress"].show()
        self['progress'].value = int(100 * float(recvbytes) / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (float(recvbytes) / 1024, float(totalbytes) / 1024, 100 * float(recvbytes) / float(totalbytes))
        if recvbytes == totalbytes:
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
        if idx is not None or idx != -1:
            self.name = self.names[idx]
            self.url = self.urls[idx]
            if idx == 0:
                print('In playVideo url D=', self.url)
                self.play()
            elif idx == 1:
                print('In playVideo runRec url D=', self.url)
                self.runRec()
            elif idx == 2:
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
                self.play()
            else:
                if idx == 4:
                    print('In playVideo url D=', self.url)
                    self.play2()
            return

    def playfile(self, serverint):
        self.serverList[serverint].play(self.session, self.url, self.name)

    def play(self):
        from urllib.parse import quote
        desc = self.desc
        name = self.name1
        url = self.url
        url = quote(url, safe=":/?&=")
        selection = self['list'].getCurrent()
        if selection is not None:
            item = selection
        else:
            print("Error: No item selected.")
            return
        self.session.open(Playstream2, name, url, desc, self.index, item, self.menu_list)
        self.close()

    def play2(self):
        if Utils.isStreamlinkAvailable():
            from urllib.parse import quote
            desc = self.desc
            name = self.name1
            url = self.url

            url = quote(url, safe=":/?&=")

            selection = self['list'].getCurrent()
            if selection is not None:
                item = selection
                desc = self.desc
                name = self.name1
                url = self.url
                if isinstance(url, bytes):
                    url = url.decode("utf-8")
                url = url.replace(':', '%3a')
                ref = '5002:0:1:0:0:0:0:0:0:0:' + 'http%3a//127.0.0.1%3a8088/' + str(url)
                sref = eServiceReference(ref)
                sref.setName(name)

            else:
                print("Error: No item selected.")
                return

            self.session.open(Playstream2, name, url, desc, self.index, item, self.menu_list)
            self.close()
        else:
            self.session.open(MessageBox, _('Install Streamlink first'), MessageBox.TYPE_INFO, timeout=5)

    def cancel(self):
        try:
            self.session.nav.stopService()
            self.session.nav.playService(self.srefInit)
            self.close()
        except:
            pass

    def load_poster(self):
        try:
            i = len(self.names)
            if i < 0:
                return
            pixmaps = self.pic
            if str(res_plugin_path) in pixmaps:
                self.downloadPic(None, pixmaps)
                return
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    parsed = urlparse(pixmaps)
                    domain = parsed.hostname
                    scheme = parsed.scheme
                    if scheme == "https" and sslverify:
                        sniFactory = SNIFactory(domain)
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
            print(ex)

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
        if os.path.exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class Playstream2(InfoBarBase, TvInfoBarShowHide, InfoBarSeek,  InfoBarNotifications, InfoBarAudioSelection, InfoBarSubtitleSupport, InfoBarMenu, Screen):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000

    def __init__(self, session, name, url, desc, index, item, menu_list):
        global streaml, _session
        Screen.__init__(self, session)
        self.session = session
        _session = session
        self.skinName = 'MoviePlayer'

        self.name = name
        self.url = url
        self.desc = desc
        self.currentindex = index
        self.item = item
        self.menu_list = menu_list
        self.itemscount = len(self.menu_list) if self.menu_list else 0

        streaml = False
        InfoBarBase.__init__(self, steal_current_service=True)
        TvInfoBarShowHide.__init__(self)
        InfoBarSeek.__init__(self, actionmap="InfobarSeekActions")
        InfoBarAudioSelection.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['actions'] = ActionMap(
            [
                'ButtonSetupActions',
                'ChannelSelectBaseActions',
                'ColorActions',
                'DirectionActions',
                'EPGSelectActions',
                'InfobarActions',
                'InfobarSeekActions',
                'InfobarShowHideActions',
                'MediaPlayerActions',
                'MediaPlayerSeekActions',
                'MoviePlayerActions',
                'MovieSelectionActions',
                'OkCancelActions',
            ],
            {
                'epg': self.showIMDB,
                'info': self.showIMDB,
                'stop': self.cancel,
                'leavePlayer': self.cancel,
                'back': self.cancel,
                'prevBouquet': self.previousitem,
                'nextBouquet': self.nextitem,
                'channelDown': self.previousitem,
                'channelUp': self.nextitem,
                'down': self.previousitem,
                'up': self.nextitem,
                'cancel': self.cancel,
            },
            -1
        )

        if '8088' in str(self.url):
            streaml = True
            # self.onLayoutFinish.append(self.slinkPlay)
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            self.onFirstExecBegin.append(self.openTest)
        self.onClose.append(self.cancel)

    def nextitem(self):
        try:
            currentindex = int(self.currentindex) + 1
            if currentindex == self.itemscount:
                currentindex = 0
            self.currentindex = currentindex
            item = self.menu_list[self.currentindex]
            self.name = item[0]
            self.url = item[1]
            self.openTest()
        except Exception as e:
            print("Error in nextitem:", str(e))

    def previousitem(self):
        try:
            currentindex = int(self.currentindex) - 1
            if currentindex < 0:
                currentindex = self.itemscount - 1
            self.currentindex = currentindex
            item = self.menu_list[self.currentindex]
            self.name = item[0]
            self.url = item[1]
            self.openTest()
        except Exception as e:
            print("Error in previousitem:", str(e))

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: '4:3 Letterbox',
                1: '4:3 PanScan',
                2: '16:9',
                3: '16:9 always',
                4: '16:10 Letterbox',
                5: '16:10 PanScan',
                6: '16:9 Letterbox'}[aspectnum]

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
        self.new_aspect += 1
        if self.new_aspect > 6:
            self.new_aspect = 0
        try:
            AVSwitch.getInstance().setAspectRatio(self.new_aspect)
            return VIDEO_ASPECT_RATIO_MAP[self.new_aspect]
        except Exception as error:
            print(error)
            return _("Resolution Change Failed")

    def showIMDB(self):
        text_clear = self.name
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def slinkPlay(self):
        name = self.name
        url = self.url
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(str(name))
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openTest(self):
        servicetype = '4097'
        name = self.name
        url = self.url

        if isinstance(url, tuple):
            url = url[0] if len(url) > 0 and isinstance(url[0], str) else None

        if not isinstance(url, str):
            print("Error: URL is not valid. Found:", type(url), "Value:", url)
            return

        try:
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(
                servicetype,
                url.replace(":", "%3a"),
                name.replace(":", "%3a")
            )
            print('reference:', ref)

            if streaml is True:
                url = 'http://127.0.0.1:8088/' + str(url)
                ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(
                    servicetype,
                    url.replace(":", "%3a"),
                    name.replace(":", "%3a")
                )
            print('final reference:', ref)

            sref = eServiceReference(ref)
            sref.setName(name)
            self.session.nav.stopService()
            self.session.nav.playService(sref)
        except Exception as e:
            print("Error in openTest:", str(e))
            print("url =", url, "name =", name)

    def doEofInternal(self, playing):
        print('doEofInternal', playing)
        Utils.MemClean()
        if self.execing and playing:
            self.openTest()

    def __evEOF(self):
        print('__evEOF')
        self.end = True
        Utils.MemClean()
        self.openTest()

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
        self.close()

    def leavePlayer(self):
        self.close()


class plgnstrt(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(path_skin, 'Plgnstrt.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self["poster"] = Pixmap()
        self["poster"].hide()
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
        if os.path.exists('/var/lib/dpkg/status'):
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
        if os.path.exists('/var/lib/dpkg/status'):
            if self.picload.startDecode(pixmaps, False) == 0:
                ptr = self.picload.getData()
        else:
            if self.picload.startDecode(pixmaps, 0, 0, False) == 0:
                ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return

    def image_downloaded(self):
        pngori = os.path.join(plugin_path, 'res/pics/fulltop.jpg')
        if os.path.exists(pngori):
            try:
                self.poster_resize(pngori)
            except Exception as ex:
                print(ex)

    def loadDefaultImage(self, failure=None):
        import random
        print("*** failure *** %s" % failure)
        global pngori
        fldpng = os.path.join(plugin_path, 'res/pics/')
        npj = random.choice(imgjpg)
        pngori = fldpng + npj
        self.poster_resize(pngori)

    def checkDwnld(self):
        self.icount = 0
        self['list'].setText(_('\n\n\nCheck Connection wait please...'))
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/status'):
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
        skin = os.path.join(path_skin, 'StreamTasks.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
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
        if current:
            if current[0] == "movie":
                if file1 is True:
                    path = Path_Movies
                url = path + current[1]
                name = current[1]
                file1 = False
                isFile = os.path.isfile(url)
                if isFile:
                    self.session.open(Playstream2, name, url, desc, self.movielist)
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
        dom = sel
        self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def callMyMsg1(self, result=None):
        if result:
            current = self["movielist"].getCurrent()
            sel = Path_Movies + current[1]
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


class DownloaderPostcondition(Condition):
    RECOVERABLE = True

    def check(self, task):
        if task.returncode == 0 or task.error is None:
            return True
        else:
            return False

    def getErrorMessage(self, task):
        return {
            task.ERROR_CORRUPT_FILE: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("DOWNLOADED FILE CORRUPTED:") + '\n%s' % task.error_message,
            task.ERROR_RTMP_ReadPacket: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("COULD NOT READ RTMP PACKET:") + '\n%s' % task.error_message,
            task.ERROR_SEGFAULT: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SEGMENTATION FAULT:") + '\n%s' % task.error_message,
            task.ERROR_SERVER: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SERVER RETURNED ERROR:") + '\n%s' % task.error_message,
            task.ERROR_UNKNOWN: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("UNKNOWN ERROR:") + '\n%s' % task.error_message
        }[task.error]


class downloadTask(Task):
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


def main(session, **kwargs):
    try:
        session.open(Revolmain)
    except:
        import traceback
        traceback.print_exc()


def menu(menuid, **kwargs):
    return [(desc_plug, main(), title_plug, 44)] if menuid == "mainmenu" else []


def mainmenu(session, **kwargs):
    main(session, **kwargs)


def Plugins(**kwargs):
    ico_path = 'logo.png'
    if not os.path.exists('/var/lib/dpkg/status'):
        ico_path = res_plugin_path + 'pics/logo.png'
    result = [PluginDescriptor(name=desc_plug,
                               description=title_plug,
                               where=PluginDescriptor.WHERE_PLUGINMENU,
                               icon=ico_path, fnc=main)]
    return result
