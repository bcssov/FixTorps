# by Mario
# License: MIT

import App
import Foundation

# Insert better mutator name def below pls
mode = Foundation.MutatorDef("Fix Torp Spread")

data = {}
timer = None


class LoadTrigger(Foundation.TriggerDef):
    def __init__(self, name, eventKey, dict={}):
        Foundation.TriggerDef.__init__(self, name, eventKey, dict)

    def __call__(self, pObject, pEvent, dict={}):
        global data, timer
        data = {}
        if not timer:
            timer = Watcher()


LoadTrigger('Fix Torp: Loaded', Foundation.TriggerDef.ET_FND_CREATE_PLAYER_SHIP, dict={'modes': [mode]})


class TorpedoReloaded(Foundation.TriggerDef):
    def __init__(self, name, eventKey, dict={}):
        Foundation.TriggerDef.__init__(self, name, eventKey, dict)

    def __call__(self, pObject, pEvent, dict={}):
        global data
        tube = App.TorpedoTube_Cast(pEvent.GetDestination())
        if tube:
            ship = tube.GetParentShip()
            if ship:
                shipId = ship.GetObjID()
                tubeId = tube.GetObjID()
                if data.has_key(shipId):
                    shipData = data[shipId]
                    if shipData.has_key(tubeId):
                        total = shipData[tubeId]['firedTorpedoes'] - 1
                        if total < 0:
                            total = 0
                        shipData[tubeId]['firedTorpedoes'] = total

        if pObject and pEvent:
            pObject.CallNextHandler(pEvent)


TorpedoReloaded('Fix Torp Spread: Torp Reloaded', App.ET_TORPEDO_RELOAD, dict={'modes': [mode]})


class TorpedoFired(Foundation.TriggerDef):
    def __init__(self, name, eventKey, dict={}):
        Foundation.TriggerDef.__init__(self, name, eventKey, dict)

    def __call__(self, pObject, pEvent, dict={}):
        global data
        tube = App.TorpedoTube_Cast(pEvent.GetDestination())
        if tube:
            ship = tube.GetParentShip()
            if ship:
                shipId = ship.GetObjID()
                reloadDelay = tube.GetReloadDelay()
                tubeId = tube.GetObjID()
                if data.has_key(shipId):
                    shipData = data[shipId]
                    if shipData.has_key(tubeId):
                        shipData[tubeId]['firedTorpedoes'] = shipData[tubeId]['firedTorpedoes'] + 1
                        shipData[tubeId]['reloadDelay'] = reloadDelay
                    else:
                        shipData[tubeId] = {'reloadDelay': reloadDelay, 'firedTorpedoes': 1}
                else:
                    data[shipId] = {tubeId: {'reloadDelay': reloadDelay, 'firedTorpedoes': 1}}

        if pObject and pEvent:
            pObject.CallNextHandler(pEvent)


TorpedoFired('Fix Torp Spread: Torp Fired', App.ET_TORPEDO_FIRED, dict={'modes': [mode]})


class Watcher:
    def __init__(self):
        self.timer = None
        self.__run__()

    def __run__(self):
        if self.timer:
            return
        self.timer = App.PythonMethodProcess()
        self.timer.SetInstance(self)
        self.timer.SetFunction("__update__")
        self.timer.SetDelay(1)
        self.timer.SetDelayUsesGameTime(1)
        self.timer.SetPriority(App.TimeSliceProcess.LOW)

    def __update__(self, fTime):
        global data
        for k, v in data.items():
            notFound = 1
            ship = App.ShipClass_GetObjectByID(None, k)
            if ship:
                torpSystem = ship.GetTorpedoSystem()
                shipData = data[ship.GetObjID()]
                if torpSystem:
                    notFound = 0
                    for i in range(torpSystem.GetNumChildSubsystems()):
                        tube = torpSystem.GetChildSubsystem(i)
                        tube = App.TorpedoTube_Cast(tube)
                        if tube:
                            if shipData.has_key(tube.GetObjID()):
                                torpData = shipData[tube.GetObjID()]
                                if torpData:
                                    if torpData['firedTorpedoes'] > 0:
                                        reloadDelay = torpData['reloadDelay'] - 1
                                        if reloadDelay <= 0:
                                            ready = tube.GetNumReady()
                                            maxReady = tube.GetMaxReady()
                                            remainingTorps = torpData['firedTorpedoes']
                                            newTorpCount = ready + remainingTorps
                                            if newTorpCount > remainingTorps:
                                                newTorpCount = maxReady
                                            tube.SetNumReady(newTorpCount)
                                            torpData['firedTorpedoes'] = 0

                                        torpData['reloadDelay'] = reloadDelay
            if notFound:
                del ship[k]
