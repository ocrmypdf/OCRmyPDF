
from ocrmypdf.pdfinfo import PdfInfo, PageInfo
from ocrmypdf.pipeline import JobContext, JobContextManager
from multiprocessing import Process
from multiprocessing.managers import BaseProxy


def client(context):
    assert isinstance(context, BaseProxy)
    pdfinfo = context.get_pdfinfo()
    page = pdfinfo[0]
    page.rotation = 90
    context.set_pdfinfo(pdfinfo)


def test_proxies(resources):
    manager = JobContextManager()
    manager.register('JobContext', JobContext)
    manager.start()

    context = manager.JobContext()

    pdfinfo = PdfInfo(resources / 'graph.pdf')
    assert pdfinfo[0].rotation == 0
    context.set_pdfinfo(pdfinfo)
    del pdfinfo

    p = Process(target=client, args=(context,))
    p.start()
    p.join()
    assert p.exitcode == 0, "Child process failed"

    assert context.get_pdfinfo()[0].rotation == 90