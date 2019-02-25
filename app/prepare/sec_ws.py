import os, json, gzip, codecs

from ixbz2.ixbz2 import FormatterIndexBZ2
from app.model.job_pool import ExecutionTask
#===============================================
class SecondaryWsCreation(ExecutionTask):
    def __init__(self, dataset, ws_name, rec_no_seq):
        ExecutionTask.__init__(self, "Secondary WS creation")
        self.mDS = dataset
        self.mWSName = ws_name
        self.mRecNoSeq = rec_no_seq
        self.mReportLines = 100

    def execIt(self):
        ws_dir = self.mDS.getDataVault().getDir() + "/" + self.mWSName
        if os.path.exists(ws_dir):
            self.setStatus("Dataset already exists")
            return None
        os.mkdir(ws_dir)

        with FormatterIndexBZ2(ws_dir + "/vdata.ixbz2") as vdata_out:
            for out_rec_no, rec_no in enumerate(self.mRecNoSeq):
                if out_rec_no > 0 and (out_rec_no % self.mReportLines) == 0:
                    self.setStatus("Prepare records: %d/%d" %
                        (out_rec_no, len(self.mRecNoSeq)))
                rec_data = self.mDS.getRecordData(rec_no)
                vdata_out.putLine(json.dumps(rec_data, ensure_ascii = False))

        rec_no_set = set(self.mRecNoSeq)
        cnt_done = 0
        with gzip.open(ws_dir + "/fdata.json.gz", 'wb') as fdata_out:
            with self.mDS._openFData() as inp:
                for rec_no, line in enumerate(inp):
                    if rec_no in rec_no_set:
                        print >> fdata_out, line.rstrip()
                        cnt_done += 1
                        if (cnt_done % self.mReportLines) == 0:
                            self.setStatus("Prepare fdata: %d/%d" %
                                (cnt_done, len(self.mRecNoSeq)))

        cnt_done = 0
        with gzip.open(ws_dir + "/pdata.json.gz", 'wb') as fdata_out:
            with self.mDS._openPData() as inp:
                for rec_no, line in enumerate(inp):
                    if rec_no in rec_no_set:
                        print >> fdata_out, line.rstrip()
                        cnt_done += 1
                        if (cnt_done % self.mReportLines) == 0:
                            self.setStatus("Prepare fdata: %d/%d" %
                                (cnt_done, len(self.mRecNoSeq)))

        self.setStatus("Finishing...")

        ds_info = {
            "name": self.mWSName,
            "kind": "ws",
            "view_schema": self.mDS.getViewSchema(),
            "flt_schema": self.mDS.getFltSchema(),
            "total": len(self.mRecNoSeq),
            "mongo": self.mWSName}

        with codecs.open(ws_dir + "/dsinfo.json",
                "w", encoding = "utf-8") as outp:
            print >> outp, json.dumps(ds_info,
                sort_keys = True, indent = 4)

        with codecs.open(ws_dir + "/active",
                "w", encoding = "utf-8") as outp:
            print >> outp, ""

        self.mDS.getDataVault().loadNewWS(self.mWSName)

        self.setStatus("Done")
        return {"ws": self.mWSName}