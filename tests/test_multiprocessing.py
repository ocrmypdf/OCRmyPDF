#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

from multiprocessing import Process
from multiprocessing.managers import BaseProxy

from ocrmypdf._jobcontext import JobContext, JobContextManager
from ocrmypdf.pdfinfo import PageInfo, PdfInfo


def test_jobcontext_proxy(resources):
    # Prove that managers are set up correctly to share state among processes
    manager = JobContextManager()
    manager.register('JobContext', JobContext)

    # Start the manager in a child process (or maybe thread)
    manager.start()

    # Tell the manager process to retrieve pdf info
    context = manager.JobContext()
    context.generate_pdfinfo(resources / 'graph.pdf')

    # Get a copy of that information for this process
    pdfinfo = context.get_pdfinfo()
    assert len(pdfinfo) == 1
    assert pdfinfo[0].rotation == 0

    # Update information and send back to manager
    pdfinfo[0].rotation = 90
    context.set_pdfinfo(pdfinfo)

    # Retrieve again, ensure it stayed changed
    pdfinfo2 = context.get_pdfinfo()
    assert pdfinfo2[0].rotation == 90

    # Start a new process which gets its own proxy object
    def client(context):
        assert isinstance(context, BaseProxy)
        pdfinfo = context.get_pdfinfo()
        page = pdfinfo[0]
        assert page.rotation == 90
        page.rotation += 90
        context.set_pdfinfo(pdfinfo)

    p = Process(target=client, args=(context,))
    p.start()
    p.join()
    assert p.exitcode == 0, "Child process failed"

    assert context.get_pdfinfo()[0].rotation == 180
