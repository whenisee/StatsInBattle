import BigWorld
import game
import Keys

import json
import urllib
import urllib2
import math
import os
import re
import threading
import time
import nations

from Avatar import PlayerAvatar
from Account import PlayerAccount
from gui import SystemMessages
from gui import InputHandler
from gui.app_loader import g_appLoader
from account_helpers.settings_core.SettingsCore import g_settingsCore
from gui.Scaleform.daapi.view.battle.legacy.stats_form import _StatsForm
from gui.battle_control.battle_arena_ctrl import BattleArenaController
from gui.Scaleform.battle_entry import BattleEntry
from gui.Scaleform.daapi.view.battle_loading import BattleLoading
from gui.Scaleform.daapi.view.battle.legacy.markers import _VehicleMarker, MarkersManager
from gui import GUI_SETTINGS
from gui.battle_control.arena_info.arena_vos import VehicleActions
from gui.battle_control import g_sessionProvider, arena_info
from CTFManager import g_ctfManager
from constants import AUTH_REALM
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from items.vehicles import VEHICLE_CLASS_TAGS
from ClientArena import ClientArena
from gui.Scaleform.framework import ViewTypes
from PlayerEvents import g_playerEvents
from helpers import getClientVersion
from gui.Scaleform.daapi.view.battle.shared.stats_exchage.stats_ctrl import BattleStatisticsDataController
from gui.battle_control.arena_info import vos_collections
from gui.Scaleform.daapi.view.battle.shared.stats_exchage.vehicle import VehicleInfoComponent
from gui.Scaleform.daapi.view.battle_loading import BattleLoading
from gui.Scaleform.daapi.view.battle.shared.markers2d.plugins import VehicleMarkerPlugin, VehicleMarker


CLIENT_VERSION = getClientVersion().split(' ')[0].replace('v.', '')
__version__ = '2.1 test #4'
__author__ = 'VasyaPRO_2014'

print '[LOAD_MOD] StatsInBattle v%s' % __version__


class Config:
    def __init__(self):
        self.load()
        return

    def __call__(self, path):
        path = path.split('/')
        c = self.config
        for x in path:
            c = c[x]
        return c

    def load(self):
        try:
            file = open('res_mods/configs/StatsInBattle/StatsInBattle.json', 'r')
            f = file.read()
            file.close()
            # Delete comments
            while f.count('/*'):
                f = f.replace(f[f.find('/*'):f.find('*/') + 2 if f.find('*/') + 2 != 1 else len(f)], '')
            while f.count('//'):
                f = f.replace(f[f.find('//'):f.find('\n', f.find('//')) if f.find('\n', f.find('//')) != -1 else len(f)], '')
            cfg = json.loads(f)
            # Check on valid
            cfg['reloadKey']
            cfg['region']
            cfg['applicationID']
            cfg['requestTimeout']
            cfg['allowAnalytics']
            cfg['playersPanel']['enable']
            cfg['playersPanel']['playerNameFull']['left']
            cfg['playersPanel']['playerNameFull']['right']
            cfg['playersPanel']['playerNameFull']['width']
            cfg['playersPanel']['playerNameCut']['left']
            cfg['playersPanel']['playerNameCut']['right']
            cfg['playersPanel']['playerNameCut']['width']
            cfg['playersPanel']['vehicleName']['left']
            cfg['playersPanel']['vehicleName']['right']
            cfg['playersPanel']['vehicleName']['width']
            cfg['playersPanel']['switcherVisible']
            cfg['playersPanel']['y']
            cfg['tab']['enable']
            cfg['tab']['playerName']['left']
            cfg['tab']['playerName']['right']
            cfg['tab']['playerName']['width']
            cfg['tab']['vehicleName']['left']
            cfg['tab']['vehicleName']['right']
            cfg['tab']['vehicleName']['width']
            cfg['battleLoading']['enable']
            cfg['battleLoading']['playerName']['left']
            cfg['battleLoading']['playerName']['right']
            cfg['battleLoading']['vehicleName']['left']
            cfg['battleLoading']['vehicleName']['right']
            cfg['marker']['enable']
            cfg['marker']['playerName']
            cfg['marker']['vehicleName']
            cfg['colors']['colorCodes']
            cfg['colors']['colorEFF']
            cfg['colors']['colorWGR']
            cfg['colors']['colorWN7']
            cfg['colors']['colorWN6']
            cfg['colors']['colorWinrate']
            cfg['colors']['colorBattles']
            if not len(cfg['colors']['colorCodes']) == len(cfg['colors']['colorEFF']) == len(cfg['colors']['colorWGR']) == len(cfg['colors']['colorWN7']) == len(cfg['colors']['colorWinrate']) == len(cfg['colors']['colorBattles']):
                raise KeyError
        except IOError:
            showMessage('[StatsInBattle] Cannot open config file (res_mods/configs/StatsInBattle/StatsInBattle.json)', 'red')
            self.loadDefault()
        except (ValueError, KeyError):
            showMessage('[StatsInBattle] Config is not valid.', 'red')
            self.loadDefault()
        else:
            self.config = cfg
            showMessage('[StatsInBattle] Config successfully loaded.', 'green')
        return

    def reload(self):
        self.load()

        arena = BigWorld.player().arena
        if arena is not None:
            ids = [str(pl['accountDBID']) for pl in arena.vehicles.values()]
            if ids != stats.dbIDs: # It is possible only on global map
                stats.loadStats()

        addStats()

    def loadDefault(self):
        showMessage('[StatsInBattle] Loading default config.', 'green')
        self.config = {
            'reloadKey': 'KEY_F9',
            'region': 'ru',
            'applicationID': 'demo',
            'requestTimeout': 5,
            'allowAnalytics': True,
            'playersPanel': {
                'enable':True,
                'playerNameFull': {
                    "left": '<font size="12" face="Consolas" color="#{colorBattles}">{kb:<3}</font> {nick}',
                    "right": '{nick:.10} <font size="12" face="Consolas" color="#{colorBattles}">{kb:>3}</font>',
                    'width' : 150
                },
                'playerNameCut': {
                    "left": '<font size="12" face="Consolas" color="#{colorBattles}">{kb:<3}</font> {nick:.16}',
                    "right": '{nick:.16} <font size="12" face="Consolas" color="#{colorBattles}">{kb:>3}</font>',
                    'width': 140
                },
                'vehicleName': {
                    'left': '{vehicle}',
                    'right': '{vehicle}',
                    'width': 100
                },
                'switcherVisible': True,
                'y': 65
            },
            'tab': {
                'enable': True,
                'playerName': {
                    'left': '<font size="12" face="Consolas">{spg_percent:<5.2f}</font> <img src="{flag_url}" width="16" height="12"> <font color="#{colorEFF}">{name}</font>',
                    'right': '<font color="#{colorEFF}">{name:.16}</font> <img src="{flag_url}" width="16" height="12"><font size="12" face="Consolas">{spg_percent:5.2f}</font>',
                    'width': 180
                },
                'vehicleName': {
                    'left': '<font face="Consolas"><font color="#{colorBattles}">{kb}</font> <font color="#{colorWinrate}">{winrate:0.0f}%</font> <font color="#{colorEFF}">{eff:4}</font></font>',
                    'right': '<font face="Consolas"><font color="#{colorEFF}">{eff:<4}</font> <font color="#{colorWinrate}">{winrate:0.0f}%</font> <font color="#{colorBattles}">{kb}</font></font>',
                    'width': 100
                }
            },
            'battleLoading': {
                'enable': True,
                'playerName': {
                    'left': '<img src="{flag_url}" width="16" height="12"> <font color="#{colorEFF}">{name}</font>',
                    'right': '<font color="#{colorEFF}">{name:.16}</font> <img src="{flag_url}" width="16" height="12">'
                },
                'vehicleName': {
                    'left': '<font face="Consolas"><font color="#{colorBattles}">{kb}</font> <font color="#{colorWinrate}">{winrate:0.0f}%</font> <font color="#{colorEFF}">{eff:4}</font></font>',
                    'right': '<font face="Consolas"><font color="#{colorEFF}">{eff:<4}</font> <font color="#{colorWinrate}">{winrate:0.0f}%</font> <font color="#{colorBattles}">{kb}</font></font>'
                },
            },
            'marker': {
                'enable': True,
                'playerName': '{eff} {nick}',
                'vehicleName': '{winrate:.0f}% {vehicle}'
            },
            'colors': {
                'colorCodes': ['FE0E00', 'FE7903', 'F8F400', '60FF00', '02C9B3', 'D042F3'],
                'colorEFF': [1, 615, 870, 1175, 1525, 1850],
                'colorWGR': [1, 2495, 4345, 6425, 8625, 10040],
                'colorWN7': [1, 495, 860, 1220, 1620, 1965],
                'colorWN6': [1, 460, 850, 1215, 1620, 1960],
                'colorWinrate': [1, 47, 49, 52.5, 58, 65],
                'colorBattles': [1, 2000, 6000, 16000, 30000, 43000]
            }
        }


class Statistics:
    def __init__(self):
        self._vehiclesInfo = None
        self.loadVehiclesInfo()
        self.playersInfo = {}
        self.dbIDs = []
        self._account_info = None
        self._account_tanks = None

    def loadStats(self):
        arena = BigWorld.player().arena
        if arena is not None:
            if arena.bonusType != 6: # If it isn't tutorial battle
                self.dbIDs = [str(pl['accountDBID']) for pl in arena.vehicles.values()]
                idsStr = ','.join(self.dbIDs)
                account_info = 'https://api.worldoftanks.{region}/wot/account/info/?application_id={appId}&fields=client_language%2Cglobal_rating%2Cstatistics.all.battles%2Cstatistics.all.wins%2Cstatistics.all.damage_dealt%2Cstatistics.all.frags%2Cstatistics.all.spotted%2Cstatistics.all.capture_points%2Cstatistics.all.dropped_capture_points&account_id={id}'.format(id=idsStr, region=config('region'), appId=config('applicationID'))
                account_tanks = 'https://api.worldoftanks.{region}/wot/account/tanks/?application_id={appId}&fields=statistics.battles%2Ctank_id&account_id={id}'.format(id=idsStr, region=config('region'), appId=config('applicationID'))
                #startTime = time.time()
                try:
                    self._account_info = json.loads(urllib2.urlopen(account_info, timeout=config('requestTimeout')).read()).get('data', None)
                    self._account_tanks = json.loads(urllib2.urlopen(account_tanks, timeout=config('requestTimeout')).read()).get('data', None)
                except IOError:
                    showMessage('[StatsInBattle] Error loading statistics.', 'red')
                    self._account_info = None
                    self._account_tanks = None
                else:
                    #print 'Statistics successfully loaded [%s sec]' % str(time.time()-startTime)
                    for value in arena.vehicles.values():
                        dbID = str(value['accountDBID'])
                        if self._account_info[dbID] and self._account_info[dbID]['statistics']['all']['battles'] != 0:
                            self.playersInfo[dbID] = {}
                            self.playersInfo[dbID]['team'] = value['team']
                            self.playersInfo[dbID]['name'] = value['name']
                            self.playersInfo[dbID]['clan'] = '[%s]' % value['clanAbbrev'] if value['clanAbbrev'] else ''
                            self.playersInfo[dbID]['nick'] = self.playersInfo[dbID]['name'] + self.playersInfo[dbID]['clan']
                            self.playersInfo[dbID]['clannb'] = value['clanAbbrev']
                            self.playersInfo[dbID]['vehicle'] = value['vehicleType'].type.shortUserString
                            self.playersInfo[dbID]['tank_id'] = value['vehicleType'].type.compactDescr
                            self.playersInfo[dbID]['level'] = value['vehicleType'].level
                            self.playersInfo[dbID]['type'] = tuple(value['vehicleType'].type.tags & VEHICLE_CLASS_TAGS)[0]
                            self.playersInfo[dbID]['nation'] = nations.NAMES[value['vehicleType'].type.customizationNationID]
                            self.playersInfo[dbID]['wgr'] = self._account_info[dbID]['global_rating']
                            self.playersInfo[dbID]['battles'] = self._account_info[dbID]['statistics']['all']['battles']
                            self.playersInfo[dbID]['winrate'] = self._account_info[dbID]['statistics']['all']['wins'] * 100.0 / self._account_info[dbID]['statistics']['all']['battles']
                            self.playersInfo[dbID]['kb'] = str(int(round(self._account_info[dbID]['statistics']['all']['battles']/1000, 0))) + 'k' if self._account_info[dbID]['statistics']['all']['battles'] >= 1000 else self._account_info[dbID]['statistics']['all']['battles']
                            self.playersInfo[dbID]['colorWGR'] = self.getColor('colorWGR', self.playersInfo[dbID]['wgr'])
                            self.playersInfo[dbID]['colorBattles'] = self.getColor('colorBattles', self.playersInfo[dbID]['battles'])
                            self.playersInfo[dbID]['colorWinrate'] = self.getColor('colorWinrate', self._account_info[dbID]['statistics']['all']['wins'] * 100.0 / self._account_info[dbID]['statistics']['all']['battles'])
                            self.playersInfo[dbID]['lang'] = self._account_info[dbID]['client_language']
                            self.playersInfo[dbID]['flag_url'] = 'img://scripts/client/gui/mods/mod_stats_in_battle/flags/' + self.playersInfo[dbID]['lang'] + '.png'
                            self.playersInfo[dbID]['spg_battles'] = 0
                            if self._vehiclesInfo is not None:
                                avgDmg = self._account_info[dbID]['statistics']['all']['damage_dealt'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgFrags = self._account_info[dbID]['statistics']['all']['frags'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgSpot = self._account_info[dbID]['statistics']['all']['spotted'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgCap = self._account_info[dbID]['statistics']['all']['capture_points'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgDef = self._account_info[dbID]['statistics']['all']['dropped_capture_points'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                battles = self._account_info[dbID]['statistics']['all']['battles']
                                winrate = self._account_info[dbID]['statistics']['all']['wins'] * 100.0 / self._account_info[dbID]['statistics']['all']['battles']
                                player_tier_temp = 0
                                for tank in self._account_tanks[dbID]:
                                    if str(tank['tank_id']) in self._vehiclesInfo:
                                        player_tier_temp += self._vehiclesInfo[str(tank['tank_id'])]['level'] * tank['statistics']['battles']
                                        if self._vehiclesInfo[str(tank['tank_id'])]['type'] == 'SPG':
                                            self.playersInfo[dbID]['spg_battles'] += tank['statistics']['battles']
                                    else:
                                        description = 'ERROR: unknown tank_id %s in player %s' % (tank['tank_id'], dbID)
                                        if self.playersInfo[dbID]['tank_id'] == tank['tank_id']:
                                            player_tier_temp += self.playersInfo[dbID]['level'] * tank['statistics']['battles']
                                            description += ' (%s, level %d, type %s, nation %s)' % (self.playersInfo[dbID]['vehicle'], self.playersInfo[dbID]['level'], self.playersInfo[dbID]['type'], self.playersInfo[dbID]['nation'])
                                        ga.send_exception(description)
                                avgTier = float(player_tier_temp) / self._account_info[dbID]['statistics']['all']['battles']
                                self.playersInfo[dbID]['eff'] = self.getEFF(avgDmg, avgTier, avgFrags, avgSpot, avgCap, avgDef)
                                self.playersInfo[dbID]['wn7'] = self.getWN7(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate, battles)
                                self.playersInfo[dbID]['wn6'] = self.getWN6(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate)
                                self.playersInfo[dbID]['spg_percent'] = float(self.playersInfo[dbID]['spg_battles']) / battles * 100.0
                            else:
                                self.playersInfo[dbID]['eff'] = 0
                                self.playersInfo[dbID]['wn7'] = 0
                                self.playersInfo[dbID]['wn6'] = 0
                            self.playersInfo[dbID]['colorEFF'] = self.getColor('colorEFF', self.playersInfo[dbID]['eff'])
                            self.playersInfo[dbID]['colorWN7'] = self.getColor('colorWN7', self.playersInfo[dbID]['wn7'])
                            self.playersInfo[dbID]['colorWN6'] = self.getColor('colorWN6', self.playersInfo[dbID]['wn6'])

    def resetStats(self):
        self.dbIDs = []
        self.playersInfo = {}
        self._account_info = None
        self._account_tanks = None

    @staticmethod
    def getEFF(avgDmg, avgTier, avgFrags, avgSpot, avgCap, avgDef):
        return int(round(avgDmg * (10 / (avgTier + 2)) * (0.23 + 2 * avgTier / 100) + avgFrags * 250 + avgSpot * 150 + math.log(avgCap + 1, 1.732) * 150 + avgDef * 150))

    @staticmethod
    def getWN7(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate, total):
        return int(round((1240 - 1040 / (min(avgTier, 6) ** 0.164)) * avgFrags + avgDmg * 530 / (184 * math.exp(0.24 * avgTier) + 130) + avgSpot * 125 * min(avgTier, 3) / 3 + min(avgDef, 2.2) * 100 + ((185 / (0.17 + math.exp(((winrate) - 35) * -0.134))) - 500) * 0.45 + (-1 * (((5 - min(avgTier, 5)) * 125) / (1 + math.exp((avgTier - (total / 220 ** (3 / avgTier))) * 1.5))))))

    @staticmethod
    def getWN6(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate):
        return int(round((1240 - 1040 / (min(avgTier, 6)) ** 0.164) * avgFrags + avgDmg * 530 / (184 * math.exp(0.24 * avgTier) + 130) + avgSpot * 125 + min(avgDef, 2.2) * 100 + ((185 / (0.17 + math.exp((winrate - 35) * -0.134))) - 500) * 0.45 + (6 - min(avgTier, 6)) * -60))

    def loadVehiclesInfo(self):
        if self._vehiclesInfo is None:
            #startTime = time.time()
            url = 'https://raw.githubusercontent.com/VasyaPRO/StatsInBattle/master/vehicles_info.json'
            try:
                self._vehiclesInfo = json.load(urllib2.urlopen(url))
                #print 'vehicles info loaded [%s sec]' % str(time.time() - startTime)
            except IOError:
                showMessage('[StatsInBattle] Error loading vehicles.', 'red')
                try:
                    file = open('res_mods/%s/scripts/client/gui/mods/mod_stats_in_battle/vehicles_info.json' % CLIENT_VERSION, 'r')
                    self._vehiclesInfo = json.load(file)
                    file.close()
                except:
                    pass
            else:
                file = open('res_mods/%s/scripts/client/gui/mods/mod_stats_in_battle/vehicles_info.json' % CLIENT_VERSION, 'w')
                json.dump(self._vehiclesInfo, file)
                file.close()


    def getColor(self, rating, value):
        color = 'FFFFFF'
        for i in range(len(config('colors/colorCodes'))):
            if value >= config('colors')[rating][i]:
                color = config('colors/colorCodes')[i]
        return color
    
    def getAccountDBIDByPlayerName(self, playerName):
        for id,value in self.playersInfo.items():
            if value['name'].startswith(playerName):
                return id


class Analytics(object):
    def __init__(self):
        self._thread_analytics = None
        self.trackingID = 'UA-78494860-1'
        self.appName = 'StatsInBattle'
        self.appVersion = __version__
        self.started = False

    def getPlayerDBID(self):
        player = BigWorld.player()
        if hasattr(player, 'databaseID'):
            return player.databaseID
        elif hasattr(player, 'playerVehicleID'):
            return player.arena.vehicles[player.playerVehicleID]['accountDBID']
        else:
            #print 'fail :D'
            time.sleep(5)
            return self.getPlayerDBID()

    def screenview(self):
        if config('allowAnalytics'):
            self.started = True
            player = BigWorld.player()
            param = urllib.urlencode({
                'v': 1,
                't': 'screenview',
                'tid': '%s' % self.trackingID,
                'cid': '%s' % self.getPlayerDBID(),
                'an': '%s' % self.appName,
                'av': '%s' % self.appVersion,
                'cd': '%s [%s]' % (player.name, AUTH_REALM)
                })
            urllib2.urlopen(url='http://www.google-analytics.com/collect?', data=param)

    def send_screenview(self):
        if not self.started:
            self._thread_analytics = threading.Thread(target=self.screenview)
            self._thread_analytics.start()

    def exception(self, description):
        if config('allowAnalytics'):
            player = BigWorld.player()
            param = urllib.urlencode({
                'v': 1,
                't': 'exception',
                'tid': '%s' % self.trackingID,
                'cid': '%s' % self.getPlayerDBID(),
                'an': '%s' % self.appName,
                'av': '%s' % self.appVersion,
                'cd': '%s [%s]' % (player.name, AUTH_REALM),
                'exd': '%s' % description
                })
            urllib2.urlopen(url='http://www.google-analytics.com/collect?', data=param)

    def send_exception(self,description):
        self._thread_analytics = threading.Thread(target=self.exception, args=[description])
        self._thread_analytics.start()


def showMessage(text, color='green'):
    app = g_appLoader.getDefBattleApp()
    if app is not None:
        battle_page = app.containerManager.getContainer(ViewTypes.VIEW).getView()
        if color == 'green':
            battle_page.components['battleVehicleMessages'].as_showGreenMessageS(None, text)
        elif color == 'red':
            battle_page.components['battleVehicleMessages'].as_showRedMessageS(None, text)
        else:
            battle_page.components['battleVehicleMessages'].as_showPurpleMessageS(None, text)
            # as_showGoldMessageS, as_showSelfMessageS
    elif isinstance(BigWorld.player(), PlayerAccount):
        SystemMessages.pushMessage(text, type = SystemMessages.SM_TYPE.Warning)
    else:
        print text

def handleKeyEvent(event):
    is_down, key, mods, is_repeat = game.convertKeyEvent(event)
    if key is getattr(Keys, config('reloadKey'), 0) and is_down:
        config.reload()
    #if key is getattr(Keys, 'KEY_P') and is_down: # Debug
        #print stats.playersInfo

InputHandler.g_instance.onKeyDown += handleKeyEvent
InputHandler.g_instance.onKeyUp += handleKeyEvent


def new_Hangar__updateAll(self):
    old_Hangar__updateAll(self)
    ga.send_screenview()

old_Hangar__updateAll = Hangar._Hangar__updateAll
Hangar._Hangar__updateAll = new_Hangar__updateAll


def new__onVehicleListUpdate(self, argStr):
    old__onVehicleListUpdate(self, argStr)
    stats.loadStats()


old__onVehicleListUpdate = ClientArena._ClientArena__onVehicleListUpdate
ClientArena._ClientArena__onVehicleListUpdate = new__onVehicleListUpdate


def addStats():
    app = g_appLoader.getDefBattleApp()
    if app is None:
        return
    if config('playersPanel/enable'):
        playersPanel = app.containerManager.getContainer(ViewTypes.VIEW).getView().components['playersPanel']
        playersPanel.flashObject.panelSwitch.visible = config('playersPanel/switcherVisible')
        playersPanel.flashObject.listLeft.y = config('playersPanel/y')
        playersPanel.flashObject.listRight.y = config('playersPanel/y')
        for i in range(playersPanel.flashObject.listLeft._items.length):
            item = playersPanel.flashObject.listLeft.getItemsByIndex(i)
            accountDBID = item.accountDBID
            playerInfo = stats.playersInfo.get(str(int(accountDBID)), None)
            if config('playersPanel/playerNameFull/width'): item.listItem.playerNameFullTF.width = config('playersPanel/playerNameFull/width')
            if config('playersPanel/playerNameCut/width'): item.listItem.playerNameCutTF.width = config('playersPanel/playerNameCut/width')
            if config('playersPanel/vehicleName/width'): item.listItem.vehicleTF.width = config('playersPanel/vehicleName/width')
            if playerInfo is not None:
                item.listItem.playerNameFullTF.htmlText = config('playersPanel/playerNameFull/left').format(**playerInfo)
                item.listItem.playerNameCutTF.htmlText = config('playersPanel/playerNameCut/left').format(**playerInfo)
                item.listItem.vehicleTF.htmlText = config('playersPanel/vehicleName/left').format(**playerInfo)
        for i in range(playersPanel.flashObject.listRight._items.length):
            item = playersPanel.flashObject.listRight.getItemsByIndex(i)
            accountDBID = item.accountDBID
            playerInfo = stats.playersInfo.get(str(int(accountDBID)),None)
            if config('playersPanel/playerNameFull/width'): item.listItem.playerNameFullTF.width = config('playersPanel/playerNameFull/width')
            if config('playersPanel/playerNameCut/width'): item.listItem.playerNameCutTF.width = config('playersPanel/playerNameCut/width')
            if config('playersPanel/vehicleName/width'): item.listItem.vehicleTF.width = config('playersPanel/vehicleName/width')
            if playerInfo is not None:
                item.listItem.playerNameFullTF.htmlText = config('playersPanel/playerNameFull/right').format(**playerInfo)
                item.listItem.playerNameCutTF.htmlText = config('playersPanel/playerNameCut/right').format(**playerInfo)
                item.listItem.vehicleTF.htmlText = config('playersPanel/vehicleName/right').format(**playerInfo)
    if config('tab/enable'):
        fullStats = app.containerManager.getContainer(ViewTypes.VIEW).getView().components['fullStats']
        for i in range(1, 16):
            playerNameTF = getattr(fullStats.flashObject.statsTable, 'playerName_c1r%d' % i)
            vehicleNameTF = getattr(fullStats.flashObject.statsTable, 'vehicleName_c1r%d' % i)
            if config('tab/playerName/width'): playerNameTF.width = config('tab/playerName/width')
            if config('tab/vehicleName/width'): vehicleNameTF.width = config('tab/vehicleName/width')
            playerName = playerNameTF.text.split('[')[0].split('..')[0]
            accountDBID = stats.getAccountDBIDByPlayerName(playerName)
            playerInfo = stats.playersInfo.get(accountDBID,None)
            if playerInfo is not None:
                playerNameTF.htmlText = config('tab/playerName/left').format(**playerInfo)
                vehicleNameTF.htmlText = config('tab/vehicleName/left').format(**playerInfo)
        for i in range(1,16):
            playerNameTF = getattr(fullStats.flashObject.statsTable, 'playerName_c2r%d' % i)
            vehicleNameTF = getattr(fullStats.flashObject.statsTable, 'vehicleName_c2r%d' % i)
            if config('tab/playerName/width'): playerNameTF.width = config('tab/playerName/width')
            if config('tab/vehicleName/width'): vehicleNameTF.width = config('tab/vehicleName/width')
            playerName = playerNameTF.text.split('[')[0].split('..')[0]
            accountDBID = stats.getAccountDBIDByPlayerName(playerName)
            playerInfo = stats.playersInfo.get(accountDBID,None)
            if playerInfo is not None:
                playerNameTF.htmlText = config('tab/playerName/right').format(**playerInfo)
                vehicleNameTF.htmlText = config('tab/vehicleName/right').format(**playerInfo)


def new_BattleEntry_beforeDelete(self):
    old_BattleEntry_beforeDelete(self)
    stats.resetStats()

old_BattleEntry_beforeDelete = BattleEntry.beforeDelete
BattleEntry.beforeDelete=new_BattleEntry_beforeDelete

def new_addVehicleInfo(self, vInfoVO, overrides):
    BigWorld.callback(2.0, addStats)
    #print 'addVehicleInfo'
    return old_addVehicleInfo(self, vInfoVO, overrides)


old_addVehicleInfo = VehicleInfoComponent.addVehicleInfo
VehicleInfoComponent.addVehicleInfo = new_addVehicleInfo

def new_makeItem(self, vInfoVO, vStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout = False):
    item = old_makeItem(self, vInfoVO, vStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout)
    if config('battleLoading/enable'):
        accountDBID = item['accountDBID']
        playerInfo = stats.playersInfo.get(str(accountDBID), None)
        if playerInfo is not None:
            item['vehicleGuiName'] = config('battleLoading/vehicleName/left').format(**playerInfo) if vInfoVO.team == BigWorld.player().team else config('battleLoading/vehicleName/right').format(**playerInfo)
            item['playerName'] = config('battleLoading/playerName/left').format(**playerInfo) if vInfoVO.team == BigWorld.player().team else config('battleLoading/playerName/right').format(**playerInfo) 
    return item

old_makeItem = BattleLoading._makeItem
BattleLoading._makeItem = new_makeItem

def new__addOrUpdateVehicleMarker(self, vProxy, vInfo, guiProps, active = True):
    # Original code
    speaking = self.bwProto.voipController.isPlayerSpeaking(vInfo.player.accountDBID)
    flagBearer = g_ctfManager.getVehicleCarriedFlagID(vInfo.vehicleID) is not None
    if active:
        mProv = vProxy.model.node('HP_gui')
    else:
        mProv = None
    if vInfo.vehicleID in self._VehicleMarkerPlugin__vehiclesMarkers:
        marker = self._VehicleMarkerPlugin__vehiclesMarkers[vInfo.vehicleID]
        if marker.setActive(active):
            self._setMarkerMatrix(marker.getMarkerID(), mProv)
            self._setMarkerActive(marker.getMarkerID(), active)
            self._VehicleMarkerPlugin__updateVehicleStates(marker, speaking, vProxy.health, flagBearer)
            marker.attach(vProxy)
    else:
        hunting = VehicleActions.isHunting(vInfo.events)
        markerID = self._createMarkerWithMatrix(mProv, 'VehicleMarker')
        self._VehicleMarkerPlugin__vehiclesMarkers[vInfo.vehicleID] = VehicleMarker(markerID, vProxy, self._parentObj.getCanvasProxy(), active)
        battleCtx = g_sessionProvider.getCtx()
        result = battleCtx.getPlayerFullNameParts(vProxy.id)
        vType = vInfo.vehicleType
        squadIndex = 0
        if g_sessionProvider.arenaVisitor.gui.isFalloutMultiTeam() and vInfo.squadIndex:
            squadIndex = vInfo.squadIndex
        # My code
        vehicleName = result.vehicleName
        playerName = result.playerName
        playerInfo = stats.playersInfo.get(str(vInfo.player.accountDBID))
        if config('marker/enable') and playerInfo is not None:
            playerName = config('marker/playerName').format(**playerInfo)
            vehicleName = config('marker/vehicleName').format(**playerInfo)
        self._invokeMarker(markerID, 'setVehicleInfo', [vType.classTag,
         vType.iconPath,
         vehicleName,
         vType.level,
         result.playerFullName,
         playerName,
         result.clanAbbrev,
         result.regionCode,
         vType.maxHealth,
         guiProps.name(),
         hunting,
         squadIndex])
        if not vProxy.isAlive():
            self._VehicleMarkerPlugin__updateMarkerState(markerID, 'dead', True)
        if active:
            self._VehicleMarkerPlugin__updateVehicleStates(self._VehicleMarkerPlugin__vehiclesMarkers[vInfo.vehicleID], speaking, vProxy.health, flagBearer)
    return
VehicleMarkerPlugin._VehicleMarkerPlugin__addOrUpdateVehicleMarker = new__addOrUpdateVehicleMarker

'''
# DON'T DELETE IT
def new_BattleEntry_onAddToIgnored(self, _, uid, userName):
    old_BattleEntry_onAddToIgnored(self, _, uid, stats.playersInfo[str(int(uid))]['name'])

old_BattleEntry_onAddToIgnored = BattleEntry._BattleEntry__onAddToIgnored
BattleEntry._BattleEntry__onAddToIgnored = new_BattleEntry_onAddToIgnored


def new_BattleEntry_onAddToFriends(self, _, uid, userName):
    old_BattleEntry_onAddToFriends(self, _, uid, stats.playersInfo[str(int(uid))]['name'])

old_BattleEntry_onAddToFriends = BattleEntry._BattleEntry__onAddToFriends
BattleEntry._BattleEntry__onAddToFriends = new_BattleEntry_onAddToFriends 
'''

ga = Analytics()
config = Config()
stats = Statistics()