"""Dựng báo cáo từ template của trường -> report/Plan2Model_Report.docx

Giữ nguyên trang bìa, style và định dạng chương của template; thay placeholder bằng nội dung.
Các chỗ cần nhóm điền (tên thành viên, kết quả U-Net) được tô vàng [TBD].
Chạy lại script sau khi có số U-Net: sửa dict UNET bên dưới rồi chạy lại.
"""
import copy, os, re
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "Project_Template_MSE_FPT University.docx")
OUT = os.path.join(HERE, "Plan2Model_Report.docx")
FIG = os.path.join(HERE, "figures")

TITLE = "Plan2Model: From Phone Photos of Paper Floor Plans to CAD Drawings and 3D Models with Classical Image Processing"
MEMBERS = ["Nguyễn Thu Trang – [TBD] Student ID", "Nguyễn Văn Thụ – 26ms23346",
           "Nguyễn Sơn Tùng – 26ms23347", "Nguyễn Hoàng Khôi Minh – 26ms23356"]
REPO_URL = "https://github.com/nstung463/plan2model"
VIDEO_URL = "https://github.com/nstung463/plan2model/releases/tag/v1.0"
YEAR = "2026"
# Điền sau khi train U-Net (None = chưa có, sẽ hiện [TBD])
UNET = {"wall_IoU": 0.774, "wall_P": 0.832, "wall_R": 0.915, "room_mIoU": 0.477, "room_F1": 0.565, "sec": 9008,
        "delta_wall_IoU": "+0.214 [+0.179, +0.251]", "delta_room_F1": "+0.111 [+0.056, +0.170]"}  # prototype/output/cc/test/unet_summary.json

doc = docx.Document(TEMPLATE)
P = doc.paragraphs
ABS_EMPTY = [P[i] for i in range(42, 56)]
TAIL_EMPTY = [P[i] for i in range(89, 94)]

# ---------- prototype định dạng lấy từ template ----------
BODY_PROTO = copy.deepcopy(P[68]._p)      # Times 12, 1.5 line
H1_PROTO = copy.deepcopy(P[66]._p)        # Heading 1
H2_PROTO = copy.deepcopy(P[67]._p)        # Heading 2
CH_PROTO = copy.deepcopy(P[64]._p)        # tiêu đề chương "Chapter N"
FRONT_TITLE_PROTO = copy.deepcopy(P[56]._p)  # "Table of Contents" (Arial, giữa trang, ngắt trang)


def _clear_runs(p_el):
    for r in p_el.findall(qn("w:r")) + p_el.findall(qn("w:hyperlink")):
        p_el.remove(r)
    for b in p_el.findall(qn("w:bookmarkStart")) + p_el.findall(qn("w:bookmarkEnd")):
        p_el.remove(b)


def _first_rpr(proto):
    r = proto.find(qn("w:r"))
    rpr = r.find(qn("w:rPr")) if r is not None else None
    return copy.deepcopy(rpr) if rpr is not None else OxmlElement("w:rPr")


def _add_run(p_el, text, rpr, bold=False, italic=False, highlight=False, sup=False, size=None):
    r = OxmlElement("w:r")
    rp = copy.deepcopy(rpr)
    for tag in ("w:b", "w:bCs", "w:i", "w:iCs", "w:highlight", "w:sz", "w:szCs"):
        if tag in ("w:sz", "w:szCs") and size is None:
            continue
        for e in rp.findall(qn(tag)):
            rp.remove(e)
    def setv(tag, val="1"):
        e = OxmlElement(tag); e.set(qn("w:val"), val); rp.insert(0, e)
    if size: setv("w:szCs", str(size * 2)); setv("w:sz", str(size * 2))
    if italic: setv("w:i")
    if bold: setv("w:b")
    if highlight: setv("w:highlight", "yellow")
    if sup:
        for e in rp.findall(qn("w:vertAlign")): rp.remove(e)
        e = OxmlElement("w:vertAlign"); e.set(qn("w:val"), "superscript"); rp.append(e)
    r.append(rp)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.append(t); p_el.append(r)
    return r


def _rich(p_el, text, rpr, **kw):
    """**bold**, *italic*, [TBD...] (tô vàng)."""
    base_italic = kw.pop("italic", False)
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|\[TBD[^\]]*\])", text):
        if not part:
            continue
        if part.startswith("**"):
            _add_run(p_el, part[2:-2], rpr, bold=True, italic=base_italic, **kw)
        elif part.startswith("[TBD"):
            _add_run(p_el, part, rpr, highlight=True, bold=True, italic=base_italic, **kw)
        elif part.startswith("*"):
            _add_run(p_el, part[1:-1], rpr, italic=True, **kw)
        else:
            _add_run(p_el, part, rpr, italic=base_italic, **kw)


class Cursor:
    """Chèn phần tử tuần tự sau một anchor."""
    def __init__(self, anchor_el):
        self.el = anchor_el

    def put(self, new_el):
        self.el.addnext(new_el); self.el = new_el
        return new_el

    def para(self, text, align=None, italic=False, size=None, space_before=None, keep_next=False):
        p = copy.deepcopy(BODY_PROTO); rpr = _first_rpr(BODY_PROTO); _clear_runs(p)
        ppr = p.find(qn("w:pPr"))
        if align:
            jc = ppr.find(qn("w:jc")); jc.set(qn("w:val"), align)
        if space_before is not None:
            ppr.find(qn("w:spacing")).set(qn("w:before"), str(space_before))
        if keep_next:
            kn = ppr.find(qn("w:keepNext")); kn.set(qn("w:val"), "1")
        _rich(p, text, rpr, italic=italic, size=size)
        return self.put(p)

    def bullets(self, items):
        for it in items:
            p = self.para("•  " + it, space_before=60)
            ind = p.find(qn("w:pPr")).find(qn("w:ind"))
            ind.set(qn("w:left"), "360"); ind.set(qn("w:hanging"), "260"); ind.attrib.pop(qn("w:firstLine"), None)

    def heading(self, text, level):
        proto = H1_PROTO if level == 1 else H2_PROTO
        p = copy.deepcopy(proto); rpr = _first_rpr(proto); _clear_runs(p)
        ppr = p.find(qn("w:pPr"))
        num = ppr.find(qn("w:numPr"))
        num.find(qn("w:numId")).set(qn("w:val"), "1")            # đánh số theo chương: 1.1., 1.1.1.
        num.find(qn("w:ilvl")).set(qn("w:val"), "1" if level == 1 else "2")
        ind = ppr.find(qn("w:ind")); ind.set(qn("w:left"), "720"); ind.set(qn("w:hanging"), "720")
        _add_run(p, text, rpr)
        return self.put(p)

    def chapter(self, text):
        p = copy.deepcopy(CH_PROTO); r = p.find(qn("w:r"))
        r.find(qn("w:t")).text = text
        return self.put(p)

    def front_title(self, text):
        p = copy.deepcopy(FRONT_TITLE_PROTO); rpr = _first_rpr(FRONT_TITLE_PROTO); _clear_runs(p)
        _add_run(p, text, rpr)
        return self.put(p)

    def field(self, instr, placeholder):
        p = copy.deepcopy(BODY_PROTO); rpr = _first_rpr(BODY_PROTO); _clear_runs(p)
        def fc(t):
            r = OxmlElement("w:r"); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), t); r.append(f); p.append(r)
        fc("begin")
        r = OxmlElement("w:r"); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "; r.append(it); p.append(r)
        fc("separate"); _add_run(p, placeholder, rpr, italic=True); fc("end")
        return self.put(p)

    def caption(self, kind, n, text):
        p = copy.deepcopy(BODY_PROTO); rpr = _first_rpr(BODY_PROTO); _clear_runs(p)
        ppr = p.find(qn("w:pPr")); ppr.find(qn("w:jc")).set(qn("w:val"), "center")
        ppr.find(qn("w:spacing")).set(qn("w:before"), "60")
        if kind == "Table":
            ppr.find(qn("w:keepNext")).set(qn("w:val"), "1")
        _add_run(p, f"{kind} ", rpr, bold=True, size=11)
        # SEQ field (để List of Figures/Tables cập nhật được trong Word)
        def fc(t):
            r = OxmlElement("w:r"); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), t); r.append(f); p.append(r)
        fc("begin")
        r = OxmlElement("w:r"); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" SEQ {kind} \\* ARABIC "; r.append(it); p.append(r)
        fc("separate"); _add_run(p, str(n), rpr, bold=True, size=11); fc("end")
        _add_run(p, ". ", rpr, bold=True, size=11)
        _rich(p, text, rpr, size=11)
        return self.put(p)

    def figure(self, path, width_cm, caption, key=None):
        global FIG_N
        FIG_N += 1
        if key: REFS[f'fig:{key}'] = FIG_N
        p = copy.deepcopy(BODY_PROTO); _clear_runs(p)
        ppr = p.find(qn("w:pPr")); ppr.find(qn("w:jc")).set(qn("w:val"), "center")
        ppr.find(qn("w:keepNext")).set(qn("w:val"), "1")
        sp = ppr.find(qn("w:spacing")); sp.set(qn("w:line"), "240"); sp.set(qn("w:before"), "200")
        self.put(p)
        tmp = doc.add_paragraph(); tmp.add_run().add_picture(path, width=Cm(width_cm))
        drawing_run = tmp._p.find(qn("w:r")); p.append(drawing_run); tmp._p.getparent().remove(tmp._p)
        self.caption("Figure", FIG_N, caption)
        return FIG_N

    def table(self, header, rows, widths_cm, caption, bold_rows=(), font=10, key=None):
        global TAB_N
        TAB_N += 1
        if key: REFS[f'tab:{key}'] = TAB_N
        self.caption("Table", TAB_N, caption)
        t = doc.add_table(rows=1 + len(rows), cols=len(header))
        tbl = t._tbl
        tblPr = tbl.tblPr
        jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "center"); tblPr.append(jc)
        borders = OxmlElement("w:tblBorders")
        for side, sz in [("top", 12), ("bottom", 12), ("insideH", 4)]:
            e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), "000000"); borders.append(e)
        for side in ["left", "right", "insideV"]:
            e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "nil"); borders.append(e)
        tblPr.append(borders)
        for i, row in enumerate([header] + rows):
            for j, val in enumerate(row):
                cell = t.cell(i, j); cell.width = Cm(widths_cm[j])
                par = cell.paragraphs[0]
                par.paragraph_format.space_before = Pt(2); par.paragraph_format.space_after = Pt(2)
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for part in re.split(r"(\[TBD[^\]]*\])", str(val)):
                    if not part: continue
                    run = par.add_run(part); run.font.name = "Times New Roman"; run.font.size = Pt(font)
                    run._r.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Times New Roman")
                    if i == 0 or i - 1 in bold_rows: run.bold = True
                    if part.startswith("[TBD"): run.font.highlight_color = WD_COLOR_INDEX.YELLOW; run.bold = True
                if i == 0:
                    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "E7ECF3"); tcPr.append(shd)
            if i == 0:
                trPr = t.rows[0]._tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); trPr.append(h)
        self.put(tbl)
        # khoảng trắng sau bảng
        self.para("", space_before=0)
        return TAB_N

    def equation(self, text):
        return self.para(text, align="center", italic=True)


FIG_N = 0
TAB_N = 0
REFS = {}


def set_par_text(p, text):
    """Đặt lại chữ cho đoạn template (giữ định dạng run đầu)."""
    runs = p.runs
    if not runs:
        p.add_run(text); return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def remove(p):
    p._p.getparent().remove(p._p)


def fmt(v, nd=3):
    return "[TBD]" if v is None else f"{v:.{nd}f}"


# ================= TRANG BÌA =================
for idx in (7, 23):
    set_par_text(P[idx], TITLE)
for base in (9, 25):
    for i in range(6):
        p = P[base + i]
        if i < len(MEMBERS):
            set_par_text(p, MEMBERS[i])
            if "[TBD" in MEMBERS[i]:
                for r in p.runs: r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        else:
            set_par_text(p, "")
for idx in (17, 36):
    set_par_text(P[idx], f"© Copyright by the authors – {YEAR}")

# ================= ABSTRACT =================
set_par_text(P[38], TITLE)
ABSTRACT = ("Digitising paper floor plans is a routine but manual task in construction and real-estate work. "
            "We present Plan2Model, a pipeline that turns a smartphone photo of a printed floor plan into a "
            "vector CAD drawing (DXF) and an interactive 3D model using classical image processing only. The "
            "pipeline rectifies the page with contour-based quadrilateral detection and a homography, flattens "
            "illumination by morphological background estimation, binarises with a self-implemented Sauvola "
            "threshold, extracts walls with a hollow-wall filling step followed by morphological opening, and "
            "segments rooms with directional closing and connected components. On 60 official CubiCasa5K test "
            "images, with all parameters tuned on the validation split, the method reaches a wall IoU of 0.560 "
            "and a room F1 of 0.454, compared with 0.473 and 0.316 for a tuned Otsu baseline; both gains are "
            "significant under a paired bootstrap. Ablation shows that hollow-wall filling is the key component. "
            "For comparison, a U-Net with a ResNet-18 encoder trained on 300 images reaches a wall IoU of 0.774 "
            "and a room F1 of 0.565, at the cost of labelled data and hours of training. The pipeline is packaged "
            "as an interactive Streamlit application that exports DXF, JSON and 3D models.")
set_par_text(P[40], ABSTRACT)
remove(P[41])

for p in ABS_EMPTY + TAIL_EMPTY:
    remove(p)
set_par_text(P[58], "List of Tables")
set_par_text(P[60], "List of Figures")

# ================= MỤC LỤC / DANH MỤC =================
cur = Cursor(P[57]._p)
set_par_text(P[57], "")
cur.field('TOC \\h \\z \\t "Chapter Title,1,Heading 1,2,Heading 2,3"', "[Right-click → Update Field to build the Table of Contents]")
cur = Cursor(P[59]._p)
cur.field('TOC \\h \\z \\c "Table"', "[Right-click → Update Field to build the List of Tables]")
cur = Cursor(P[61]._p)
cur.field('TOC \\h \\z \\c "Figure"', "[Right-click → Update Field to build the List of Figures]")

# ================= THÂN BÀI =================
# Xoá placeholder trong các chương, giữ tiêu đề chương
chapter_idx = [64, 69, 74, 79, 84]
to_remove = [i for c in chapter_idx for i in range(c + 1, c + 5)]
chap = {i: P[i] for i in chapter_idx}
for i in sorted(to_remove, reverse=True):
    remove(P[i])

# ---------- Chapter 1: Introduction ----------
c = Cursor(chap[64]._p)
c.heading("Background and Motivation", 1)
c.para("A large share of existing buildings in Vietnam, and in many other countries, is documented only on paper: "
       "printed or hand-annotated floor plans kept by owners, management boards or local authorities. Renovation, "
       "interior design, facility management and real-estate listings all start by redrawing these plans in a CAD "
       "or BIM tool, which takes an experienced drafter from tens of minutes to hours per floor. Meanwhile, the "
       "people who hold the paper usually have only a smartphone.")
c.para("Turning a phone photo of a floor plan into a structured model is an image-processing problem with several "
       "classical sub-problems: the page is seen under perspective and uneven lighting, the drawing mixes thick "
       "structural lines (walls) with thin symbols, text and dimensions, and the semantic objects of interest "
       "(walls, doors, rooms) must be recovered as geometry rather than as pixels.")
c.heading("Problem Statement", 1)
c.para("**Input:** a photograph of a printed architectural floor plan taken with a handheld phone (arbitrary "
       "perspective, background and illumination), or a scanned floor-plan image.")
c.para("**Output:** (i) a binary wall mask and vectorised wall polygons, (ii) a set of room polygons with areas, "
       "(iii) a DXF file with separate WALL, ROOM and TEXT layers that opens in AutoCAD and imports into Revit, and "
       "(iv) an extruded 3D model viewable in a web browser.")
c.heading("Objectives and Contributions", 1)
c.bullets([
    "An end-to-end pipeline, from phone photo to CAD and 3D, built only from techniques covered in the course "
    "(edges, contours, geometric transforms, morphology, adaptive thresholding, connected components, Hough transform).",
    "A self-implemented Sauvola thresholding with integral images, verified against scikit-image (99.99 % pixel agreement).",
    "A simple *hollow-wall filling* step that handles the three wall drawing styles found in real plans (solid, "
    "outlined, hatched or coloured) and is the main source of improvement in our experiments.",
    "A rigorous evaluation on the public CubiCasa5K benchmark with an official validation/test split, tuned baselines, "
    "an ablation study, a paired bootstrap significance test and an error analysis.",
    "A comparison against a learned model (U-Net [13] with a ResNet-18 encoder) trained on 300 images of the official training split; it is clearly more accurate on walls (wall IoU 0.774 vs 0.560) and shows where the classical pipeline stands.",
])
c.heading("Report Organisation", 1)
c.para("Chapter 2 reviews related work. Chapter 3 describes the dataset and each processing stage. Chapter 4 reports "
       "experiments on synthetic phone photos and on CubiCasa5K. Chapter 5 concludes and outlines future work.")

# ---------- Chapter 2: Literature Review ----------
c = Cursor(chap[69]._p)
c.heading("Classical Floor-Plan Analysis", 1)
c.para("Early systems separated text from graphics and then detected walls as thick line pairs, using run-length "
       "analysis, morphology and the Hough transform [1], [2]. Ahmed et al. [3] introduced a wall-detection "
       "pipeline that separates thick, medium and thin lines by morphological operations and then extracts rooms as "
       "regions enclosed by walls and door gaps. Such methods are fast, explainable and need no training data, but are "
       "sensitive to the drawing style: a parameter set tuned for solid black walls fails on outlined or hatched walls.")
c.heading("Learning-Based Floor-Plan Recognition", 1)
c.para("Liu et al. [4] proposed Raster-to-Vector, which predicts junction heatmaps with a CNN and assembles walls by "
       "integer programming. Zeng et al. [5] (DeepFloorplan) used a multi-task network with room-boundary-guided "
       "attention and reported a wall accuracy of about 88 %, versus 53 % for Raster-to-Vector, on their benchmark. Kalervo et al. [6] "
       "released CubiCasa5K, 5,000 floor plans annotated with more than 80 object categories, together with a "
       "multi-task baseline. These models are clearly more accurate on in-distribution data, but require GPUs for "
       "training, large annotated datasets, and they are trained on clean digital or scanned images rather than "
       "phone photos.")
c.heading("Document Image Rectification and Binarisation", 1)
c.para("Phone-based document scanners locate the page as the largest quadrilateral contour and remove perspective "
       "with a homography [7]. For binarisation under uneven illumination, local methods such as Niblack and Sauvola [8] "
       "outperform a global Otsu threshold [9]; integral images make the local statistics computable in constant time "
       "per pixel [10].")
c.heading("From Plans to 3D", 1)
c.para("Several open-source projects (for example FloorplanToBlender3d [11]) extrude detected walls into 3D, and "
       "recent work builds semantic BIM models from 2D plans [12]. Our contribution is not a new recognition model, "
       "but a complete, reproducible and measurable pipeline that starts from a *phone photo*, uses only course-level "
       "techniques, and is evaluated honestly against tuned baselines and a learned model.")

# ---------- Chapter 3: Methodology ----------
c = Cursor(chap[74]._p)
c.heading("Datasets", 1)
c.para("**Synthetic phone photos.** To measure the full pipeline including page rectification, we render a floor "
       "plan with known geometry (5 rooms, exterior walls 25 cm, interior walls 15 cm, 6 doors, 4 windows, text, "
       "dimension lines and a title block) at 60 px/m, then simulate a phone photo: the page is placed on a wood "
       "texture, warped by a perspective transform, darkened by a lighting gradient and a hand shadow, and degraded by "
       "noise, blur and JPEG compression. The exact wall mask and room areas are known.")
c.para("**CubiCasa5K [6].** Real Finnish floor plans with SVG annotations. We use the official split files and take "
       "the first images of each of the three image categories, without manual selection. Only the archive entries "
       "needed are fetched by HTTP range requests (about 40 MB for the validation and test images and about 150 MB more for the training images, instead of the full 5.2 GB). Ground-truth wall masks and "
       "room masks are rasterised from the SVG polygons on the *F1_scaled* image, as in the official loader; room "
       "classes Outdoor and Undefined are ignored.")
c.table(["Split", "Architectural", "High quality", "Colorful", "Total", "Used for"],
        [["val (official)", "15", "15", "15", "45", "parameter tuning"],
         ["test (official)", "20", "20", "20", "60", "final evaluation only"],
         ["train (official)", "100", "100", "100", "300", "U-Net training only"]],
        [3.2, 2.4, 2.4, 2.0, 1.6, 4.0], "CubiCasa5K subsets used in this work.", key="data")
c.figure(os.path.join(FIG, "fig_cubicasa_examples.png"), 13.5, key="cubicasa", caption=
         "CubiCasa5K test examples of the three categories with ground truth (red: walls, colours: rooms). "
         "Wall styles range from solid black to outlined, hatched and coloured.")
c.heading("Pipeline Overview", 1)
c.para("Figure {fig:block} gives the block diagram of the method and Figure {fig:steps} shows every stage on a "
       "synthetic phone photo. Page detection and rectification are only needed for photos; scanned images enter at "
       "illumination flattening. Table {tab:tech} lists the image-processing techniques used.")
c.figure(os.path.join(FIG, "fig_block_diagram.png"), 16, key="block", caption="Block diagram of Plan2Model.")
c.table(["Technique", "Used for", "Course topic", "Implementation"],
        [["Canny edge detection", "page detection", "Edge detection", "OpenCV"],
         ["Contours + Douglas–Peucker", "page quadrilateral, polygons", "Shape representation", "OpenCV"],
         ["Homography (geometric transform)", "perspective rectification", "Geometric transformations", "OpenCV"],
         ["Grey-level and binary morphology", "illumination, walls, door closing", "Morphological processing", "OpenCV"],
         ["Sauvola adaptive threshold", "binarisation", "Segmentation by thresholding", "self-implemented"],
         ["Otsu threshold", "baseline", "Segmentation by thresholding", "OpenCV"],
         ["Distance transform, connected components", "hollow-wall filling, rooms", "Morphology and segmentation", "OpenCV"],
         ["Hough transform", "wall line segments", "Line detection", "OpenCV"]],
        [4.4, 4.2, 3.7, 2.8], "Image-processing techniques used and the corresponding course topics.", key="tech")
c.figure(os.path.join(FIG, "fig_pipeline_steps.png"), 16, key="steps", caption=
         "Pipeline on a synthetic phone photo: (a) input, (b) page detection, (c) perspective rectification, "
         "(d) illumination flattening, (e) Sauvola binarisation, (f) wall mask, (g) door closing, (h) rooms.")
c.heading("Page Detection and Rectification", 1)
c.para("The image is downscaled to 800 px, smoothed with a 5×5 Gaussian, and edges are found with Canny "
       "(thresholds 40/120) and dilated by a 3×3 kernel. Among the five largest external contours, the first whose "
       "Douglas–Peucker approximation (ε = 2 % of the perimeter) has four vertices and covers more than 20 % of the "
       "image is taken as the page. Corners are ordered by the sum and difference of coordinates and mapped to a "
       "1000×800 canvas with a homography H estimated from the four correspondences:")
c.equation("[x′, y′, w′]ᵀ = H · [x, y, 1]ᵀ,   (u, v) = (x′/w′, y′/w′)")
c.heading("Illumination Flattening and Sauvola Binarisation (self-implemented)", 1)
c.para("The paper background B is estimated by a grey-level morphological closing with a 41×41 elliptical element "
       "(which removes the dark strokes) followed by a 31×31 Gaussian blur; the flattened image is I′ = 255·I/(B+1). "
       "We then apply Sauvola's local threshold [8]:")
c.equation("T(x, y) = m(x, y) · [ 1 + k · ( s(x, y) / R − 1 ) ],   k = 0.2, R = 128, window 25×25")
c.para("where m and s are the local mean and standard deviation. We implemented it ourselves with two integral "
       "images (of I and I²), so each pixel costs O(1) regardless of the window size. Our output agrees with "
       "*skimage.filters.threshold_sauvola* on 99.99 % of pixels.")
c.heading("Wall Extraction with Hollow-Wall Filling", 1)
c.para("Walls are the thickest strokes in a plan, so a morphological opening [14] with a k×k square removes text, door "
       "arcs, furniture and dimension lines while keeping walls; components smaller than 400 px are discarded. This "
       "works for solid walls but deletes outlined walls entirely, because each outline is thin (Figure {fig:hollow}c). We "
       "therefore build a wall-candidate mask before the opening:")
c.bullets([
    "**Stroke repair:** a 3×3 closing joins hatching strokes.",
    "**Colour cue:** pixels with HSV saturation > 110 and value > 90 are added (yellow, red or grey wall fills).",
    "**Hollow-wall filling:** every background component that is fully enclosed by ink, whose maximum inscribed "
    "radius r (from the distance transform) satisfies 1.5 ≤ r ≤ r_max, whose elongation area/r² ≥ 6, and whose "
    "longer side exceeds 6r, is filled. These are exactly the narrow, long gaps between the two outlines of a wall; "
    "rooms are too wide and letters are too short to pass.",
])
c.figure(os.path.join(FIG, "fig_hollow_fill.png"), 16, key="hollow", caption=
         "Effect of hollow-wall filling on an outlined-wall plan: without filling, the opening (c) removes almost "
         "all walls; with filling (d), the opening (e) keeps the wall network.")
c.para("We also tested an *adaptive* kernel size k = 0.25·T, where the wall thickness T is estimated as twice the "
       "median of the upper half of the distance transform of the candidate mask after a 5×5 opening (clipped to 8–40 px). As reported "
       "in Chapter 4, it did not beat a fixed k selected on the validation set, so the final method uses k = 7.")
c.heading("Door Closing and Room Segmentation", 1)
c.para("Doors and windows appear as gaps in the wall mask, which would merge rooms with each other and with the "
       "outside. We close the wall mask separately with a horizontal 1×L and a vertical L×1 line element and take the "
       "union, which bridges gaps only between collinear wall ends. L corresponds to the largest opening to close. "
       "When the drawing scale is known (synthetic data, 60 px/m) we use L = 2.2 m, which also bridges exterior "
       "windows. On CubiCasa5K the scale is unknown, so we assume 25 cm walls; with the nominal wall thickness "
       "T = k/0.25 = 28 px of the final method this gives about 112 px/m, and L = 1.6 m (about 180 px) was "
       "selected on validation. Rooms are the 4-connected components of the complement that do not touch the image "
       "border and are larger than 1.5 m²; each is simplified to a polygon with Douglas–Peucker.")
c.heading("Vectorisation, CAD Export and 3D", 1)
c.para("Wall polygons with holes are obtained with *findContours* in two-level hierarchy mode, and line segments with "
       "*HoughLinesP* on the wall mask. Coordinates are converted to metres and written with *ezdxf* into a DXF "
       "file with WALL, ROOM and TEXT layers (room name and area). The same geometry is exported to JSON and extruded "
       "to a height of 2.8 m in a Three.js viewer, with coloured floors and floating area labels (Figure {fig:3d}).")
c.heading("Evaluation Protocol", 1)
c.bullets([
    "**Wall IoU, precision and recall** between predicted and ground-truth wall masks.",
    "**Room F1:** predicted and ground-truth rooms are matched one-to-one greedily by IoU; a match counts if IoU ≥ 0.5. "
    "We also report room mIoU (mean over ground-truth rooms of the best IoU).",
    "**Tuning:** all methods, including the baselines, are tuned by grid search on the 45 validation images with the "
    "objective J = 0.5·wall IoU + 0.5·room F1. Test images are used once, with frozen parameters.",
    "**Significance:** paired bootstrap over test images (5,000 resamples), 95 % confidence interval of the mean difference.",
])
c.table(["Method", "Parameters selected on validation", "Validation J"],
        [["B0 Otsu", "opening k = 5, door L = 1.6 m", "0.387"],
         ["B1 Sauvola (v1, tuned on synthetic)", "opening k = 3, door L = 2.0 m", "0.355"],
         ["Proposed, adaptive k", "r_max = 14, k = 0.25·T (k ≥ 5), door L = 1.6 m", "0.485"],
         ["Proposed, fixed k (final)", "r_max = 14, k = 7, door L = 1.6 m", "0.493"]],
        [4.8, 7.4, 2.6], "Parameters selected by grid search on the validation split.", bold_rows=(3,), key="params")

# ---------- Chapter 4: Simulation Results ----------
c = Cursor(chap[79]._p)
c.heading("Experimental Setup", 1)
c.para("All experiments run on a 16-thread CPU without a GPU, Python 3.13, OpenCV 5.0, scikit-image 0.25 and "
       "PyTorch 2.13 (CPU). Code, data-fetching scripts and the exact parameters are in the project repository "
       "(Appendix B).")
c.heading("End-to-End Results on a Synthetic Phone Photo", 1)
c.para("On the simulated phone photo the pipeline detects the page, recovers all 5 rooms and builds the 3D model in "
       "0.2–0.4 s on CPU. With the photo configuration (illumination flattening, Sauvola, opening k = 7, "
       "L = 2.2 m) the wall IoU is 0.810, versus 0.377 with a global Otsu threshold, whose single threshold "
       "breaks under the hand shadow. Measured areas are about 9 % smaller than the nominal areas because the pipeline "
       "measures the *clear floor area* inside the walls, whereas nominal areas are computed to the wall centrelines.")
c.table(["Room", "Nominal area (m²)", "Measured (m²)", "IoU"],
        [["Living room", "30.00", "27.42", "0.954"], ["Kitchen", "15.00", "13.16", "0.949"],
         ["Bedroom 1", "31.50", "28.74", "0.963"], ["WC", "15.75", "14.18", "0.958"],
         ["Bedroom 2", "15.75", "13.87", "0.954"], ["Mean", "", "", "0.956"]],
        [4.0, 3.6, 3.2, 2.2], "Room-level results on the synthetic phone photo.", bold_rows=(5,), key="synth")
c.figure(os.path.join(FIG, "fig_3d_model.png"), 13, key="3d", caption=
         "3D model generated automatically from the synthetic phone photo (Three.js viewer).")
c.heading("Main Results on CubiCasa5K", 1)
c.para("Table {tab:main} and Figure {fig:bar} report test results with frozen parameters. The proposed method improves wall IoU by "
       "+0.088 and room F1 by +0.138 over the tuned Otsu baseline. Precision is slightly lower than Otsu but recall is "
       "much higher (0.743 vs 0.556), which is what room segmentation needs: a missing wall merges two rooms, while a "
       "small false-positive blob rarely does.")
c.table(["Method", "Wall IoU", "Wall P", "Wall R", "Room mIoU", "Room F1"],
        [["B0 Otsu (tuned)", "0.473", "0.727", "0.556", "0.258", "0.316"],
         ["B1 Sauvola v1 (tuned)", "0.421", "0.649", "0.525", "0.345", "0.304"],
         ["Proposed, adaptive k", "0.552", "0.672", "0.756", "0.387", "0.447"],
         ["Proposed, fixed k = 7 (final)", "0.560", "0.692", "0.743", "0.344", "0.454"],
         ["U-Net ResNet-18 (learned)", fmt(UNET["wall_IoU"]), fmt(UNET["wall_P"]), fmt(UNET["wall_R"]), fmt(UNET["room_mIoU"]), fmt(UNET["room_F1"])]],
        [5.2, 1.9, 1.7, 1.7, 2.0, 1.8], "Results on the CubiCasa5K test split (60 images; 52 have room annotations).",
        bold_rows=(3,), key="main")
c.figure(os.path.join(FIG, "fig_results_bar.png"), 14.5, key="bar", caption= "Wall IoU and room F1 on the test split.")
c.heading("Ablation Study", 1)
c.para("Each component of the proposed method is removed in turn (Table {tab:abl}). Hollow-wall filling is by far the most "
       "important: without it, room F1 halves (0.447 → 0.229) and wall IoU on architectural drawings drops from 0.47 "
       "to 0.21 (Figure {fig:cat}). The colour cue adds a small gain. Illumination flattening has no effect on CubiCasa5K, as "
       "expected for scanned images; its benefit is on phone photos (Section 4.2). The adaptive kernel size does not "
       "help either: the validation set already preferred a fixed k, and on test it is slightly worse in wall IoU.")
c.table(["Variant", "Wall IoU", "Room F1", "Δ Room F1"],
        [["Proposed (adaptive k)", "0.552", "0.447", "–"],
         ["  without hollow-wall filling", "0.435", "0.229", "−0.218"],
         ["  without colour cue", "0.544", "0.426", "−0.021"],
         ["  without illumination flattening", "0.557", "0.447", "0.000"],
         ["  with fixed k = 7 instead of adaptive", "0.560", "0.454", "+0.007"]],
        [6.6, 2.2, 2.2, 2.2], "Ablation on the test split.", key="abl")
c.figure(os.path.join(FIG, "fig_results_by_category.png"), 13.5, key="cat", caption=
         "Wall IoU per image category. Hollow-wall filling mainly helps architectural drawings.")
c.heading("Statistical Significance", 1)
c.table(["Comparison (final method − other)", "Δ Wall IoU [95 % CI]", "Δ Room F1 [95 % CI]"],
        [["vs B0 Otsu", "+0.088 [+0.038, +0.142]", "+0.138 [+0.064, +0.216]"],
         ["vs B1 Sauvola v1", "+0.139 [+0.101, +0.177]", "+0.150 [+0.072, +0.228]"],
         ["vs without hollow-wall filling", "+0.125 [+0.085, +0.169]", "+0.225 [+0.150, +0.299]"],
         ["U-Net vs final method", UNET.get("delta_wall_IoU") or "[TBD]", UNET.get("delta_room_F1") or "[TBD]"]],
        [5.6, 4.4, 4.4], "Paired bootstrap (5,000 resamples) on test images.", key="boot")
c.para("None of the confidence intervals for the classical comparisons contains zero, so the improvements are "
       "statistically significant at the 95 % level.")
c.heading("Comparison with a Learned Model (U-Net)", 1)
c.para("To position the classical pipeline against deep learning, we train a U-Net [13] with an ImageNet-pretrained "
       "ResNet-18 encoder for binary wall segmentation on the 300 training images (images resized to 768 px on the long "
       "side, random 256×256 crops, flips, rotations and brightness/contrast jitter, BCE + Dice loss, AdamW with a "
       "one-cycle schedule, CPU only). The checkpoint and the probability threshold are selected on the validation "
       "split. The predicted wall mask is passed to the same door-closing and room-segmentation stage, so the "
       "comparison isolates wall extraction.")
c.para("The model is trained for 3,000 iterations (batch 8) in about 2.5 hours on CPU. The best validation wall IoU "
       "at a threshold of 0.5 is 0.710; the threshold then selected on validation, 0.6, gives 0.712. On the test split "
       "(Tables {tab:main} and {tab:boot}) the U-Net reaches wall IoU 0.774 and room F1 0.565, i.e. +0.214 wall IoU and "
       "+0.111 room F1 over the final classical method, both significant at 95 %. Most of the wall gain is in recall "
       "(0.915 vs 0.743), and precision is also higher (0.832 vs 0.692). The price is 300 labelled training images, "
       "hours of training and a 57 MB model, whereas the classical pipeline needs no training data, runs in about 0.5 s "
       "per image, and every stage can be inspected and tuned by hand. Both share the same room-segmentation stage, so "
       "the limitations of that stage (open-plan areas, unclosed doors) apply to both.")
c.heading("Demo Application", 1)
c.para("The pipeline is packaged as a Streamlit application (Appendix B). The user picks a sample or uploads a photo, "
       "chooses the paper format and how the drawing scale is obtained (known house width, assumed wall thickness, or "
       "pixels per metre), and adjusts the opening size and the door-closing length. Each component can be switched off "
       "to show the ablation live; on CubiCasa5K samples the app also reports wall IoU and room F1 against the ground "
       "truth. Results are shown as processing steps, a room table with areas, and an interactive 3D model, and can be "
       "downloaded as DXF, JSON or a stand-alone 3D web page.")
c.heading("Error Analysis", 1)
c.figure(os.path.join(FIG, "fig_qualitative.png"), 16, key="qual", caption=
         "Best, median and worst test images (green: correct wall, red: false positive, blue: missed wall).")
c.bullets([
    "**Hand-drawn or faint outlined walls** (worst case, IoU 0.13): the two outlines are broken, so the gap between "
    "them is not enclosed and is not filled.",
    "**Solid non-wall objects:** staircases, kitchen counters and filled furniture survive the opening and become "
    "false walls (median case).",
    "**Hatched balcony walls** are partly missed because the hatching leaves gaps larger than the 3×3 repair.",
    "**Open-plan spaces:** kitchen–living areas separated only by a dashed line or by a change of floor finish have no "
    "wall, so they always merge into one room. This is the main limit of room F1 for any wall-based method.",
])
c.heading("Discussion", 1)
c.para("The classical pipeline is fully explainable, needs no training data or GPU, runs in about 0.5 s per scan "
       "on a CPU, and each of its stages can be checked visually, which is valuable in a professional workflow where a "
       "drafter must trust the result. Its accuracy, however, depends on drawing conventions; the large drop on "
       "architectural drawings without hollow-wall filling shows how a single design decision can dominate the "
       "result. A careful protocol also mattered: our first comparison, in which only the proposed "
       "method had been tuned (on the test images themselves), suggested an eight-fold gain in room F1 over Otsu, "
       "mainly because the baseline used an unsuitable door-closing length. With both methods tuned on the "
       "same validation data, the gain is smaller but real and significant.")

# ---------- Chapter 5: Conclusions ----------
c = Cursor(chap[84]._p)
c.heading("Summary", 1)
c.para("We built Plan2Model, an end-to-end pipeline that converts a phone photo of a paper floor plan into a DXF "
       "drawing and a 3D model using classical image processing. On a synthetic phone photo it recovers all rooms "
       "with a mean IoU of 0.956. On 60 official CubiCasa5K test images, with parameters tuned only on validation, it "
       "reaches a wall IoU of 0.560 and a room F1 of 0.454, significantly above a tuned Otsu baseline (0.473 and "
       "0.316). A hollow-wall filling step accounts for most of the gain.")
c.heading("Limitations", 1)
c.bullets([
    "Evaluation of the phone-photo stages (page detection, illumination) is on synthetic photos only; a set of "
    "real phone photos with annotations is still needed.",
    "Doors, windows and room types are not recognised as objects; open-plan rooms cannot be separated.",
    "The metric scale is inferred from an assumed wall thickness unless the user provides a known dimension.",
    "Results are on subsets (45 validation, 60 test images) of CubiCasa5K because of time and storage constraints.",
])
c.heading("Future Work", 1)
c.bullets([
    "Collect about 20 real phone photos of printed plans and annotate them to measure the full pipeline.",
    "Hybrid approach: use the learned wall mask where the classical candidate mask is uncertain.",
    "Read the scale bar or a dimension string with OCR to obtain metric coordinates automatically.",
    "Export directly to IFC/Revit with door and window families.",
])

# ================= TÀI LIỆU THAM KHẢO =================
refs = [
    "[1] S. Ahmed, M. Weber, M. Liwicki, and A. Dengel, “Text/graphics segmentation in architectural floor plans,” in Proc. ICDAR, 2011, pp. 734–738.",
    "[2] S. Macé, H. Locteau, E. Valveny, and S. Tabbone, “A system to detect rooms in architectural floor plan images,” in Proc. DAS, 2010, pp. 167–174.",
    "[3] S. Ahmed, M. Liwicki, M. Weber, and A. Dengel, “Improved automatic analysis of architectural floor plans,” in Proc. ICDAR, 2011, pp. 864–869.",
    "[4] C. Liu, J. Wu, P. Kohli, and Y. Furukawa, “Raster-to-vector: Revisiting floorplan transformation,” in Proc. IEEE ICCV, 2017, pp. 2195–2203.",
    "[5] Z. Zeng, X. Li, Y. K. Yu, and C.-W. Fu, “Deep floor plan recognition using a multi-task network with room-boundary-guided attention,” in Proc. IEEE ICCV, 2019, pp. 9096–9104.",
    "[6] A. Kalervo, J. Ylioinas, M. Häikiö, A. Karhu, and J. Kannala, “CubiCasa5K: A dataset and an improved multi-task model for floorplan image analysis,” in Proc. SCIA, 2019, pp. 28–40.",
    "[7] R. Szeliski, Computer Vision: Algorithms and Applications, 2nd ed. Cham, Switzerland: Springer, 2022.",
    "[8] J. Sauvola and M. Pietikäinen, “Adaptive document image binarization,” Pattern Recognition, vol. 33, no. 2, pp. 225–236, 2000.",
    "[9] N. Otsu, “A threshold selection method from gray-level histograms,” IEEE Trans. Syst., Man, Cybern., vol. 9, no. 1, pp. 62–66, 1979.",
    "[10] F. Shafait, D. Keysers, and T. M. Breuel, “Efficient implementation of local adaptive thresholding techniques using integral images,” in Proc. SPIE Document Recognition and Retrieval XV, 2008.",
    "[11] D. Westberg, “FloorplanToBlender3d,” GitHub repository. [Online]. Available: https://github.com/grebtsew/FloorplanToBlender3d",
    "[12] A. Cambeiro Barreiro, M. Trzeciakiewicz, A. Hilsmann, and P. Eisert, “Automatic reconstruction of semantic 3D models from 2D floor plans,” arXiv:2306.01642, 2023.",
    "[13] O. Ronneberger, P. Fischer, and T. Brox, “U-Net: Convolutional networks for biomedical image segmentation,” in Proc. MICCAI, 2015, pp. 234–241.",
    "[14] R. C. Gonzalez and R. E. Woods, Digital Image Processing, 4th ed. New York, NY, USA: Pearson, 2018.",
]
P2 = doc.paragraphs
ref_title = next(p for p in P2 if p.text.startswith("References or Bibliography"))
set_par_text(ref_title, "References")
ref_note = ref_title._p.getnext()
c = Cursor(ref_title._p)
for r in refs:
    p = c.para(r, space_before=80)
    ind = p.find(qn("w:pPr")).find(qn("w:ind")); ind.set(qn("w:left"), "540"); ind.set(qn("w:hanging"), "540"); ind.attrib.pop(qn("w:firstLine"), None)
ref_note.getparent().remove(ref_note)

# ================= PHỤ LỤC =================
app_title = next(p for p in doc.paragraphs if p.text.startswith("Appendices"))
set_par_text(app_title, "Appendices")
c = Cursor(app_title._p)
c.para("**Appendix A. Task Allocation**", space_before=240)
c.table(["Member", "Main responsibilities", "Contribution (%)"],
        [["Nguyễn Sơn Tùng (lead)", "Project coordination and system design; integration of the pipeline (core.py); Streamlit demo application; demo video; report writing and final editing", "25"],
         ["Nguyễn Thu Trang", "Page detection and perspective rectification; illumination flattening; self-implemented Sauvola threshold and its verification; synthetic plan and phone-photo generator", "25"],
         ["Nguyễn Văn Thụ", "Wall candidate extraction (colour cue, hollow-wall filling); door closing and room segmentation; vectorisation, DXF/JSON export and 3D model", "25"],
         ["Nguyễn Hoàng Khôi Minh", "CubiCasa5K download and ground-truth parsing; grid-search tuning and test protocol; ablation and bootstrap analysis; U-Net training and comparison", "25"]],
        [3.8, 8.6, 2.4], "Task allocation and contribution.")
c.para("**Appendix B. How to Run**", space_before=240)
for line in [f"Repository: {REPO_URL}",
             "pip install -r requirements.txt",
             "streamlit run app.py — interactive demo: sample or uploaded images, parameter sliders, live ablation toggles, processing steps, 3D viewer, DXF/JSON/HTML download",
             "python prototype/run_demo.py — synthetic phone photo → DXF, JSON and 3D page (prototype/output/demo.html)",
             "python prototype/fetch_cubicasa.py val 45 ; python prototype/fetch_cubicasa.py test 60 — data subsets",
             "python prototype/tune.py — grid search on validation → prototype/params.json",
             "python prototype/eval_cubicasa.py test — frozen-parameter evaluation, ablation, figures of predictions",
             "python prototype/unet_wall.py train 3000 ; python prototype/eval_unet.py — U-Net training and evaluation (CPU)",
             f"Demo video: {VIDEO_URL} (Plan2Model_video.mp4)",
             "Dataset: https://github.com/nstung463/plan2model/releases/download/v1.0/plan2model_dataset.zip (CubiCasa5K subset + synthetic images; unzip into prototype/data/)"]:
    c.para(line, space_before=60, size=11)
c.para("**Appendix C. Declaration of AI Tool Usage**", space_before=240)
c.para("In accordance with the course regulations, the group declares the following use of AI tools.")
c.table(["Tool", "Purpose", "Scope"],
        [["Claude (Anthropic), via Claude Code", "Code prototyping and debugging; suggesting experiment design; drafting report text; editing, motion graphics and captions of the demo video (HyperFrames)",
          "All generated code and text were reviewed, run and edited by the group; all numbers come from our own experiments"],
         ["Whisper large-v3-turbo (OpenAI), via faster-whisper", "Speech-to-text of the narration, used for captions and cut points",
          "Demo video only; the narration is spoken by a group member and the transcript was corrected before use"]],
        [3.8, 5.4, 5.6], "AI tool usage declaration.")

# Thay token {fig:x}/{tab:x} bằng số thật
for t in doc.element.body.iter(qn("w:t")):
    if t.text and "{" in t.text:
        t.text = re.sub(r"\{((?:fig|tab):\w+)\}", lambda m: str(REFS[m.group(1)]), t.text)
# Style "Chapter Title" cho tiêu đề chương, References, Appendices (để mục lục nhận)
from docx.enum.style import WD_STYLE_TYPE
cst = doc.styles.add_style("Chapter Title", WD_STYLE_TYPE.PARAGRAPH)
cst.base_style = doc.styles["normal"]
for p in doc.paragraphs:
    ppr = p._p.find(qn("w:pPr"))
    num = ppr.find(qn("w:numPr")) if ppr is not None else None
    if num is not None and num.find(qn("w:numId")).get(qn("w:val")) == "1" and num.find(qn("w:ilvl")).get(qn("w:val")) == "0":
        p.style = cst
    elif p.text in ("References", "Appendices"):
        p.style = cst
# Word cập nhật các trường (TOC, danh mục) khi mở file
settings = doc.settings.element
uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true"); settings.append(uf)

doc.save(OUT)
print("saved", OUT, "| figures:", FIG_N, "tables:", TAB_N)
