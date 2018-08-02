#import sys
import json, codecs
from .data_set import DataSet, DataRecord
from .form_tab import formTable
from .cfg_a_json import CONFIG_AJson
#===============================================
class DataSet_AJson(DataSet):
    sMainKey = CONFIG_AJson["_main_key"]
    def __init__(self, name, fname):
        DataSet.__init__(self, name)
        self.mRecords = []
        self.mRecDict = dict()
        with codecs.open(fname, "r", encoding = "utf-8") as inp:
            for line in inp:
                record = json.loads(line)
                record["_no"] = len(self.mRecords)
                self.mRecords.append(record)
        for rec in self.mRecords:
            self.mRecDict[rec[self.sMainKey]] = rec

    def reportList(self, output):
        print >> output, '<ul class="records">'
        for idx, rec in enumerate(self.mRecords):
            rec_key = rec[self.sMainKey]
            print >> output, ('<li id="li--%d" '
                'onclick="changeRec(\'%s\', %d)";">%s</li>' %
                (idx, self.getName(), idx, rec_key))
        print >> output, '</ul>'

    def getRecKey(self, rec_no):
        return self.mRecords[rec_no][self.sMainKey]

    def getRecord(self, rec_no):
        return DataRecord_AJson(self.mRecords[int(rec_no)])

#===============================================
class DataRecord_AJson(DataRecord):
    def __init__(self, json_obj):
        self.mObj = json_obj
        self.mUseFields = {fld: False for fld in self.mObj.keys()}
        for fld in CONFIG_AJson["_no_view_fields"]:
            self.mUseFields[fld] = True
        self.mUseFields["_no"] = True

    def getID(self):
        return self.mObj[self.sMainKey]

    def reportIt(self, output):
        cfg = CONFIG_AJson["_aspect_title"]
        print >> output, '<div class="r-tab">'
        for aspect in (["main", "cons", "colv"] +
                CONFIG_AJson["_view_tabs"] + ["inp"]):
            print >> output, ('<button class="r-tablnk" id="la--%s" '
                'onclick="chooseAspect(event, \'a--%s\')">%s</button>' %
                (aspect, aspect, cfg[aspect]))
        print >> output, '</div>'

        print >> output, '<div id="a--inp" class="r-tabcnt">'
        self.reportInput(output)
        print >> output, '</div>'

        print >> output, '<div id="a--cons" class="r-tabcnt">'
        self.reportConsequences(output)
        print >> output, '</div>'

        print >> output, '<div id="a--colv" class="r-tabcnt">'
        self.reportColocatedVariants(output)
        print >> output, '</div>'

        for aspect in CONFIG_AJson["_view_tabs"]:
            print >> output, '<div id="a--%s" class="r-tabcnt">' % aspect
            self.reportAspect(output, aspect)
            print >> output, '</div>'

        print >> output, '<div id="a--main" class="r-tabcnt">'
        self.reportMain(output)
        print >> output, '</div>'

    def reportMain(self, output):
        cfg = CONFIG_AJson["main"]
        formTable(output, "rec-main",
            [self.mObj], cfg["fields"], cfg["options"], self.mUseFields)
        print >> output, '</td></tr></table>'
        unused_fields = set()
        for fld, used in self.mUseFields.items():
            if not used:
                unused_fields.add(fld)
        if len(unused_fields) > 0:
            print >> output, ('<p class="error">Unused fields: %s</p>' %
                ' '.join(sorted(unused_fields)))

    def reportColocatedVariants(self, output):
        if "colocated_variants" not in self.mObj:
            return
        self.mUseFields["colocated_variants"] = True
        variants = self.mObj["colocated_variants"]
        use_flds = dict()
        for var in variants:
            for fld in var.keys():
                use_flds[fld] = False
        cfg = CONFIG_AJson["colocated_variants"]
        formTable(output, "c-variants", variants,
            cfg["fields"], cfg["options"], use_flds)
        unused_fields = set()
        for fld, used in use_flds.items():
            if not used:
                unused_fields.add(fld)
        if len(unused_fields) > 0:
            print >> output, ('<p class="error">'
                'Unused fields in colocated_variants: %s</p>' %
                ' '.join(sorted(unused_fields)))

    def reportConsequences(self, output):
        variants = []
        prefix_head = []
        cfg = CONFIG_AJson["consequences"]
        for cons_name in cfg["groups"]:
            grp_data = cfg["group-options"][cons_name]
            if grp_data["field"] not in self.mObj:
                continue
            vars = self.mObj[grp_data["field"]]
            if len(vars) == 0:
                continue
            self.mUseFields[grp_data["field"]] = True
            prefix_head.append((grp_data["title"], len(vars)))
            variants += vars

        if len(variants) == 0:
            return
        use_flds = dict()
        for var in variants:
            for fld in var.keys():
                use_flds[fld] = False

        formTable(output, "rec-consequences",
            variants, cfg["fields"], cfg["options"], use_flds, prefix_head)
        unused_fields = set()
        for fld, used in use_flds.items():
            if not used:
                unused_fields.add(fld)
        if len(unused_fields) > 0:
            print >> output, ('<p class="error">'
                'Unused fields in consequences: %s</p>' %
                ' '.join(sorted(unused_fields)))
        print >> output, '<p></p>'

    def reportInput(self, output):
        self.mUseFields["input"] = True
        if "input" not in self.mObj:
            print >> output, '<p class="error">No input data</p>'
            return
        print >> output, '<pre>'
        collect_str = ""
        for fld in self.mObj["input"].split('\t'):
            if len(fld) < 40:
                if len(collect_str) < 60:
                    collect_str += "\t" + fld
                else:
                    print >> output, collect_str[1:]
                    collect_str = "\t" + fld
                continue
            if collect_str:
                print >> output, collect_str[1:]
                collect_str = ""
            for vv in fld.split(';'):
                var, q, val = vv.partition('=')
                if var == "CSQ":
                    print >> output, "==v====SCQ======v========"
                    for idx, dt in enumerate(val.split(',')):
                        ddd = dt.split('|')
                        print >> output, "%d:\t%s" % (idx, '|'.join(ddd[:17]))
                        print >> output, "\t|%s" % ('|'.join(ddd[17:37]))
                        print >> output, "\t|%s" %  ('|'.join(ddd[37:]))
                    print >> output, "==^====SCQ======^========"
                else:
                    print >> output, vv
        if collect_str:
            print >> output, collect_str[1:]
            collect_str = ""

    def reportAspect(self, output, aspect):
        self.mUseFields[aspect] = True
        cfg = CONFIG_AJson[aspect]
        formTable(output, "rec-%s" % aspect,
            [self.mObj[aspect]], cfg["fields"], cfg["options"])
