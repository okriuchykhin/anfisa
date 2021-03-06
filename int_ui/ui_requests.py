import logging
from io import StringIO

from utils.log_err import logException
from .gen_html import formWsPage, noRecords, dirPage, notFound
from .html_xl import formXLPage
from .html_xltree import formXLTreePage
from .record import reportWsRecord, reportXlRecord
from .doc_nav import formDocNavigationPage
#===============================================
class IntUI:
    sHtmlBase = None
    sHtmlTitle = None
    sWsURL = None

    @classmethod
    def setup(cls, config, in_container):
        cls.sHtmlTitle = config["html-title"]
        cls.sWsURL = config.get("html-ws-url", "ws")
        cls.sHtmlBase = (config["html-base"]
            if in_container else None)
        if cls.sHtmlBase and not cls.sHtmlBase.endswith('/'):
            cls.sHtmlBase += '/'

    @classmethod
    def notFoundResponse(cls, serv_h):
        output = StringIO()
        notFound(output, cls.sHtmlTitle,
            cls.sHtmlBase if cls.sHtmlBase else '/')
        return serv_h.makeResponse(content = output.getvalue(),
            error = 404)

    @classmethod
    def finishRequest(cls, serv_h, rq_path, rq_args, data_vault):
        try:
            return cls._finishRequest(serv_h, rq_path, rq_args, data_vault)
        except:
            logException("Exception on evaluation request")
        return cls.notFoundResponse(serv_h)

    @classmethod
    def _finishRequest(cls, serv_h, rq_path, rq_args, data_vault):
        if rq_path == "/" or rq_path == "/ws":
            workspace = data_vault.getWS(rq_args.get("ws"))
            if workspace is None:
                return cls.notFoundResponse(serv_h)
            output = StringIO()
            formWsPage(output, cls.sHtmlTitle, cls.sHtmlBase,
                workspace, cls.sWsURL)
            return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/rec":
            workspace = data_vault.getWS(rq_args.get("ws"))
            modes = rq_args.get("m", "").upper()
            rec_no = int(rq_args.get("rec"))
            if workspace:
                output = StringIO()
                reportWsRecord(output, workspace, 'R' in modes, rec_no,
                    rq_args.get("details"), rq_args.get("port"))
                return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/xl_rec":
            dataset = data_vault.getXL(rq_args.get("ds"))
            rec_no = int(rq_args.get("rec"))
            if dataset:
                output = StringIO()
                reportXlRecord(output, dataset, rec_no)
                return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/dir":
            output = StringIO()
            dirPage(output, cls.sHtmlTitle, cls.sHtmlBase, cls.sWsURL)
            return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/norecords":
            output = StringIO()
            noRecords(output)
            return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/xl_flt":
            xl_ds = data_vault.getXL(rq_args.get("ds"))
            if xl_ds is None:
                return cls.notFoundResponse(serv_h)
            output = StringIO()
            formXLPage(output, cls.sHtmlTitle, cls.sHtmlBase,
                xl_ds, cls.sWsURL)
            return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/xl_tree":
            xl_ds = data_vault.getXL(rq_args.get("ds"))
            if xl_ds is None:
                return cls.notFoundResponse(serv_h)
            output = StringIO()
            formXLTreePage(output, cls.sHtmlTitle,
                cls.sHtmlBase, xl_ds, cls.sWsURL)
            return serv_h.makeResponse(content = output.getvalue())

        if rq_path == "/doc_nav":
            dataset = data_vault.getDS(rq_args.get("ds"))
            if dataset:
                output = StringIO()
                formDocNavigationPage(output,
                    cls.sHtmlTitle, cls.sHtmlBase, dataset)
                return serv_h.makeResponse(content = output.getvalue())

        logging.error("BAD server request: " + rq_path);
        return cls.notFoundResponse(serv_h)

