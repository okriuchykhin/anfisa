import os, json, logging
from glob import glob
from threading import Lock

from .workspace import Workspace
from .rest_api import RestAPI
from app.xl.xl_dataset import XLDataset
from utils.log_err import logException
#===============================================
class DataVault:
    def __init__(self, application, vault_dir):
        self.mApp = application
        self.mVaultDir = os.path.abspath(vault_dir)
        self.mLock  = Lock()
        self.mDataSets = dict()

        workspaces = []
        names = [[], []]
        for active_path in glob(self.mVaultDir + "/*/active"):
            ds_path = os.path.dirname(active_path)
            info_path =  ds_path + "/dsinfo.json"
            if not os.path.exists(info_path):
                continue
            with open(info_path, "r", encoding = "utf-8") as inp:
                ds_info = json.loads(inp.read())
            if ds_info["kind"] == "xl":
                assert ds_info["name"] not in self.mDataSets
                try:
                    ds_h = XLDataset(self, ds_info, ds_path)
                except:
                    logException("Bad XL-dataset load: " + ds_info["name"])
                    continue
                self.mDataSets[ds_info["name"]] = ds_h
                names[0].append(ds_info["name"])
            else:
                assert ds_info["kind"] == "ws"
                workspaces.append((ds_info, ds_path))
        for ds_info, ds_path in workspaces:
            assert ds_info["name"] not in self.mDataSets
            try:
                ws_h = Workspace(self, ds_info, ds_path)
            except:
                logException("Bad WS-dataset load: " + ds_info["name"])
                continue
            self.mDataSets[ds_info["name"]] = ws_h
            names[1].append(ds_info["name"])
        logging.info("Vault %s started with %d/%d datasets" %
            (self.mVaultDir, len(names[0]), len(names[1])))
        if len(names[0]) > 0:
            logging.info("XL-datasets: " + " ".join(names[0]))
        if len(names[1]) > 0:
            logging.info("WS-datasets: " + " ".join(names[1]))

    def __enter__(self):
        self.mLock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.mLock.release()

    def descrContext(self, rq_args, rq_descr):
        if "ds" in rq_args:
            rq_descr.append("ds=" + rq_args["ds"])
        if "ws" in rq_args:
            rq_descr.append("ds=" + rq_args["ws"])

    def getApp(self):
        return self.mApp

    def getDir(self):
        return self.mVaultDir

    def getWS(self, ws_name):
        ds = self.mDataSets.get(ws_name)
        return ds if ds and ds.getDSKind() == "ws" else None

    def getXL(self, ds_name):
        ds = self.mDataSets.get(ds_name)
        return ds if ds and ds.getDSKind() == "xl" else None

    def getDS(self, ds_name):
        return self.mDataSets.get(ds_name)

    def checkNewDataSet(self, ds_name):
        with self:
            return ds_name not in self.mDataSets

    def loadDS(self, ds_name, ds_kind = None):
        ds_path = self.mVaultDir + '/' + ds_name
        info_path =  ds_path + "/dsinfo.json"
        with open(info_path, "r", encoding = "utf-8") as inp:
            ds_info = json.loads(inp.read())
        assert ds_info["name"] == ds_name
        assert not ds_kind or ds_info["kind"] == "ws"
        with self:
            if ds_info["name"] not in self.mDataSets:
                if ds_info["kind"] == "xl":
                    ds = XLDataset(self, ds_info, ds_path)
                else:
                    assert ds_info["kind"] == "ws"
                    ds = Workspace(self, ds_info, ds_path)
                self.mDataSets[ds_info["name"]] = ds
        return ds_name

    def unloadDS(self, ds_name, ds_kind = None):
        with self:
            ds = self.mDataSets[ds_name]
            assert not ds_kind or (
                ds_kind == "ws" and isinstance(ds, Workspace)) or (
                ds_kind == "xl" and isinstance(ds, XLDataset))
            del self.mDataSets[ds_name]

    def _prepareDS(self, rq_args):
        kind = "ws" if "ws" in rq_args else "ds"
        ds = self.mDataSets[rq_args[kind]]
        assert kind == "ds" or ds.getDSKind().lower() == "ws"
        return ds

    def getBaseDS(self, ws_h):
        return self.mDataSets.get(ws_h.getBaseDSName())

    def getSecondaryWS(self, ds_h):
        ret = []
        for ws_h in self.mDataSets.values():
            if ws_h.getBaseDSName() == ds_h.getName():
                ret.append(ws_h)
        return sorted(ret, key = lambda ws_h: ws_h.getName())

    #===============================================
    @RestAPI.vault_request
    def rq__dirinfo(self, rq_args):
        rep = {
            "version": self.mApp.getVersionCode(),
            "workspaces": [],
            "xl-datasets": [],
            "reserved": []}
        for ds_name in sorted(self.mDataSets.keys()):
            ds_h = self.mDataSets[ds_name]
            if ds_h.getDSKind() == "ws":
                rep["workspaces"].append(
                    ds_h.dumpDSInfo(navigation_mode = True))
            else:
                rep["xl-datasets"].append(
                    ds_h.dumpDSInfo(navigation_mode = True))
        for reserved_path in glob(self.mVaultDir + "/*"):
            rep["reserved"].append(os.path.basename(reserved_path))
        return rep

    #===============================================
    @RestAPI.vault_request
    def rq__recdata(self, rq_args):
        ds = self._prepareDS(rq_args)
        return ds.getRecordData(int(rq_args.get("rec")))

    #===============================================
    @RestAPI.vault_request
    def rq__reccnt(self, rq_args):
        ds = self._prepareDS(rq_args)
        modes = rq_args.get("m", "").upper()
        return ds.getViewRepr(int(rq_args.get("rec")),
            'R' in modes or ds.getDSKind().lower == "xl",
            details = rq_args.get("details"))

    #===============================================
    @RestAPI.vault_request
    def rq__dsinfo(self, rq_args):
        assert "ws" not in rq_args
        ds = self._prepareDS(rq_args)
        note = rq_args.get("note")
        if note is not None:
            with ds:
                ds.getMongoAgent().setNote(note)
        return ds.dumpDSInfo(navigation_mode = False)

    #===============================================
    @RestAPI.vault_request
    def rq__single_cnt(self, rq_args):
        record = json.loads(rq_args["record"])
        modes = rq_args.get("m", "").upper()
        return self.mApp.viewSingleRecord(record, 'R' in modes)

    #===============================================
    @RestAPI.vault_request
    def rq__job_status(self, rq_args):
        return self.mApp.askJobStatus(rq_args["task"])

    #===============================================
    @RestAPI.vault_request
    def rq__solutions(self, rq_args):
        ds = self.mDataSets[rq_args["ds"]]
        return ds.getIndex().getCondEnv().reportSolutions()

    #===============================================
    # Administrator authorization required
    @RestAPI.vault_request
    def rq__adm_ds_on(self, rq_args):
        self.loadDS(rq_args["ds"])
        return []

    #===============================================
    @RestAPI.vault_request
    def rq__adm_ds_off(self, rq_args):
        self.unloadDS(rq_args["ds"])
        return []
