"""Xuất report/Plan2Model_Report.pdf có mục lục, danh mục bảng/hình đã điền (LibreOffice cập nhật các trường TOC).

Chạy bằng Python đi kèm LibreOffice:
  "C:\Program Files\LibreOffice\program\python.exe" report/export_pdf.py
"""
import os, sys, time, subprocess, uno
from com.sun.star.beans import PropertyValue
def pv(n, v):
    p = PropertyValue(); p.Name = n; p.Value = v; return p
HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "Plan2Model_Report.docx")
out_pdf = os.path.join(HERE, "Plan2Model_Report.pdf")
soffice = r"C:\Program Files\LibreOffice\program\soffice.exe"
proc = subprocess.Popen([soffice, "--headless", "--norestore", "--accept=socket,host=127.0.0.1,port=2002;urp;"])
ctx = uno.getComponentContext()
res = ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", ctx)
for _ in range(60):
    try:
        rc = res.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext"); break
    except Exception: time.sleep(1)
desk = rc.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", rc)
doc = desk.loadComponentFromURL(uno.systemPathToFileUrl(src), "_blank", 0, (pv("Hidden", True),))
idx = doc.getDocumentIndexes()
print("indexes:", idx.getCount())
for _ in range(2):
    doc.refresh()
    for i in range(idx.getCount()):
        ix = idx.getByIndex(i); ix.update(); print(" ", i, len(ix.getAnchor().getString()), "ky tu")
doc.storeToURL(uno.systemPathToFileUrl(out_pdf), (pv("FilterName", "writer_pdf_Export"),))
doc.close(True)
try: desk.terminate()
except Exception: pass
proc.wait(30)
