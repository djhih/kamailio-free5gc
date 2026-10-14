#!/usr/bin/env python3
"""Rebuild the editable architecture on page 12; preserve every other ZIP part.

All positions and font sizes below are in 1280 x 720 canvas pixels. This file
is the source of truth for the revised diagram, not its rendered PNG.
Requires Python 3 and lxml (already available in the project environment).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import posixpath
from zipfile import ZipFile

from lxml import etree as E

HERE = Path(__file__).resolve().parent
DEFAULT_DECK = HERE.parent.parent / "VoNR_over_IMS_kamailio_intro.pptx"
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
C = dict(bg="F6F7F9", ink="14213D", muted="5B6575", blue="2877B5",
         deep="0F4C81", pale="E8F1F9", edge="D5DAE1", orange="E8742A",
         peach="FCEBDD", white="FFFFFF", access="EEF1F5", dn="FFF9F4",
         custom="786B65", cx="7D8795")
FONT = "Noto Sans CJK TC"
EMU = 9525
elements = []


def box(key, x, y, w, h, fill, stroke=None, dashed=False, radius=True):
    elements.append(dict(kind="box", key=key, x=x, y=y, w=w, h=h,
                         fill=fill, stroke=stroke, dashed=dashed, radius=radius))


def text(key, x, y, w, h, value, size=18, color="ink", bold=False, align="left"):
    elements.append(dict(kind="text", key=key, x=x, y=y, w=w, h=h,
                         text=value, size=size, color=color, bold=bold, align=align))


def line(key, points, color="ink", width=2.4, dashed=False, arrow=True):
    elements.append(dict(kind="line", key=key, points=points, color=color,
                         width=width, dashed=dashed, arrow=arrow))


def node(key, x, y, w, title, subtitle, fill="white", color="blue", h=66):
    box(key, x, y, w, h, fill, "edge" if fill == "white" else None)
    text(key+"-title", x+5, y+10, w-10, 28, title, 23, color, True, "center")
    text(key+"-subtitle", x+4, y+40, w-8, 20, subtitle, 14,
         "white" if fill == "deep" else "muted", align="center")


def diagram():
    text("title", 46, 26, 1190, 51, "free5GC 接 IMS：資料路徑與政策控制", 36, bold=True)
    text("subtitle", 48, 88, 1190, 30,
         "IMS 媒體需求 → PCF 決策 → SMF session / QoS policy → UPF 規則下發", 21, "muted")

    # Logical domains, intentionally independent from Docker subnets.
    box("access-domain", 46, 142, 236, 432, "access")
    box("core-domain", 302, 142, 322, 432, "pale")
    box("ims-domain", 650, 142, 584, 432, "peach")
    text("access-title", 64, 156, 205, 31, "UE / RAN", 23, "deep", True)
    text("core-title", 322, 156, 270, 31, "5GC · free5GC", 23, "deep", True)
    text("ims-title", 672, 156, 270, 31, "IMS", 23, "orange", True)

    # N6 terminates on this network boundary. The IP reachability segment
    # inside the DN is a separate connector, not a UPF--P-CSCF interface.
    box("ims-data-network", 675, 354, 551, 217, "dn", "orange")
    text("dn-title", 820, 369, 207, 27, "IMS Data Network", 19, "orange", True)
    text("dn-subtitle", 822, 397, 205, 24, "N6 的 DN 端", 15, "muted")

    # Main policy chain: IMS session -> custom AF -> PCF -> SMF -> UPF.
    line("n5-af-to-pcf", [(705, 254), (465, 254)])
    line("n7-pcf-to-smf", [(396, 292), (396, 356)])
    line("n4-smf-to-upf", [(396, 422), (396, 486)])
    line("custom-pcscf-to-adapter", [(771, 486), (771, 293)],
         "custom", 2.4, dashed=True)

    # IP transport carrying UE IMS signaling; RTP is not sent through CSCFs.
    line("uu-ue-to-gnb", [(140, 519), (189, 519)], "blue", 4.2)
    line("n3-gnb-to-upf", [(267, 519), (327, 519)], "blue", 4.2)
    line("n6-upf-to-dn", [(465, 519), (675, 519)], "blue", 4.2)
    line("dn-ip-reachability", [(682, 519), (705, 519)], "blue", 4.2)

    # Gm is a logical endpoint relationship carried by the blue path above.
    line("gm-ue-to-pcscf", [(101, 552), (101, 614), (771, 614), (771, 552)],
         "orange", 2.4)
    line("mw-pcscf-to-icscf", [(837, 519), (891, 519)], "orange", 2.4)
    line("mw-icscf-to-scscf", [(1023, 519), (1076, 519)], "orange", 2.4)

    # Cx is Diameter, not part of the orange SIP chain. One shared HSS.
    line("cx-icscf-to-hss", [(957, 486), (957, 444), (1090, 444), (1090, 430)],
         "cx", 1.8)
    line("cx-scscf-to-hss", [(1142, 486), (1142, 430)], "cx", 1.8)

    node("ue", 62, 486, 78, "UE", "SIPp", color="deep")
    node("gnb", 189, 486, 78, "gNB", "模擬 RAN", color="deep")
    node("pcf", 327, 226, 138, "PCF", "Policy decision")
    node("smf", 327, 356, 138, "SMF", "Session / QoS")
    node("upf", 327, 486, 138, "UPF", "Forwarding / QER", "deep", "white")
    node("pcscf", 705, 486, 132, "P-CSCF", "(Kamailio)", color="orange")
    node("icscf", 891, 486, 132, "I-CSCF", "(Kamailio)", color="orange")
    node("scscf", 1076, 486, 132, "S-CSCF", "(Kamailio)", color="orange")
    node("hss", 1046, 368, 162, "HSS", "(PyHSS)", color="orange", h=62)

    box("custom-af-adapter", 705, 204, 318, 89, "white", "custom", dashed=True)
    text("af-title", 717, 214, 296, 28, "IMS-to-5GC AF Adapter", 21, "ink", True, "center")
    text("af-role", 717, 244, 296, 22, "Custom · 承接 IMS AF 功能", 16, "muted", align="center")
    text("af-custom-label", 717, 267, 296, 21, "Implementation-specific / Non-3GPP", 14.5,
         "custom", align="center")

    # Reference point on one line; service/protocol on subordinate lines.
    text("n5-name", 475, 186, 213, 25, "N5", 19, bold=True, align="center")
    text("n5-service", 473, 213, 226, 26, "Npcf_PolicyAuthorization", 16, align="center")
    text("n5-transport", 473, 266, 226, 25, "HTTP/2 SBI (h2c)", 15, "muted", align="center")
    text("n7-name", 414, 298, 191, 23, "N7", 18, bold=True)
    text("n7-semantic", 414, 322, 195, 23, "Npcf_SMPolicyControl", 15, "muted")
    text("n7-transport", 484, 348, 125, 23, "HTTP/2 SBI", 14, "muted")
    text("n4-name", 414, 431, 155, 24, "N4", 18, bold=True)
    text("n4-protocol", 414, 456, 65, 24, "PFCP", 16, "muted")
    text("uu-label", 129, 436, 70, 43, "NR / Uu", 15, "blue", True, "center")
    text("n3-name", 273, 439, 48, 24, "N3", 17, "blue", True, "center")
    text("n3-protocol", 269, 465, 57, 22, "GTP-U", 13, "blue", align="center")
    text("n6-name", 493, 463, 160, 24, "N6", 19, "blue", True, "center")
    text("n6-semantic", 487, 490, 172, 24, "User plane / IP", 16, "blue", align="center")
    text("n6-boundary", 490, 535, 173, 25, "UPF ↔ Data Network", 13.5, "muted", align="center")

    text("custom-api", 786, 309, 253, 26, "Custom HTTP API", 18, "custom", True)
    text("custom-api-scope", 786, 337, 244, 21, "implementation-specific", 14, "custom")
    text("custom-media-requirements", 686, 430, 75, 45, "IMS 媒體\n需求", 14, "custom", align="center")
    text("mw-p-i", 839, 465, 50, 45, "Mw\nSIP", 14, "orange", True, "center")
    text("mw-i-s", 1025, 465, 49, 45, "Mw\nSIP", 14, "orange", True, "center")
    text("cx-i-label", 967, 448, 79, 35, "Cx\nDiameter", 13, "cx", align="center")
    text("cx-s-label", 1149, 449, 72, 35, "Cx\nDiameter", 13, "cx", align="center")
    text("gm-label", 172, 582, 575, 27,
         "Gm · SIP REGISTER / INVITE（邏輯流；封包走藍色路徑）", 16, "orange", True)
    text("access-note", 65, 213, 198, 90,
         "IMS access path\nUE 的 SIP/IP 封包\n經 gNB、UPF 進入 DN", 17, "muted")
    text("ran-note", 65, 325, 198, 70,
         "本 PoC：free-ran-ue\n模擬 UE / gNB\nUu 為邏輯示意", 15, "muted")
    text("arrow-note", 818, 586, 410, 39,
         "箭頭：請求／政策下發方向；回應省略。\nP → I → S 為本專案的 SIP 路由。", 14, "muted")

    # Compact legend with independent encoding for each plane.
    legend = [(48, "blue", 4.2, False, "UE IP 路徑"),
              (275, "orange", 2.4, False, "IMS SIP"),
              (466, "ink", 2.4, False, "5GC policy / control"),
              (760, "cx", 1.8, False, "Cx / Diameter"),
              (1006, "custom", 2.4, True, "Custom integration")]
    for i, (x, color, width, dashed, label) in enumerate(legend):
        line(f"legend-line-{i}", [(x, 650), (x+32, 650)], color, width, dashed, arrow=False)
        text(f"legend-text-{i}", x+42, 637, 199, 28, label, 15, "muted")
    text("scope-note", 48, 681, 1186, 23,
         "PoC 範圍：RTP 在 UPF hairpin，不經 CSCF；QoS 僅驗證 PDR / QER 下發，未驗證端到端頻寬保證。", 14, "muted")


def q(name):
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def sub(parent, tag, **attrs):
    return E.SubElement(parent, q(tag), {k: str(v) for k, v in attrs.items()})


def fill(parent, color):
    sub(sub(parent, "a:solidFill"), "a:srgbClr", val=C.get(color, color))


def transform(parent, x, y, w, h, **attrs):
    xf = sub(parent, "a:xfrm", **attrs)
    sub(xf, "a:off", x=round(x*EMU), y=round(y*EMU))
    sub(xf, "a:ext", cx=round(w*EMU), cy=round(h*EMU))


def stroke(parent, color, width, dashed=False, arrow=False):
    ln = sub(parent, "a:ln", w=round(width*EMU), cap="rnd")
    fill(ln, color)
    sub(ln, "a:prstDash", val="dash" if dashed else "solid")
    sub(ln, "a:round")
    if arrow:
        sub(ln, "a:tailEnd", type="triangle", w="sm", len="sm")


def build_xml(original):
    root = E.fromstring(original)
    tree = root.find("p:cSld/p:spTree", NS)
    root.find("p:cSld", NS).set("name", "free5GC 接 IMS：資料路徑與政策控制")
    for child in list(tree)[2:]:
        tree.remove(child)
    shape_id = 2
    for el in elements:
        segments = list(zip(el["points"], el["points"][1:])) if el["kind"] == "line" else [None]
        for idx, segment in enumerate(segments):
            shape_id += 1
            sp = sub(tree, "p:cxnSp" if segment else "p:sp")
            nv = sub(sp, "p:nvCxnSpPr" if segment else "p:nvSpPr")
            sub(nv, "p:cNvPr", id=shape_id, name=el["key"]+(f"-{idx}" if segment else ""))
            sub(nv, "p:cNvCxnSpPr" if segment else "p:cNvSpPr",
                **({"txBox": "1"} if el["kind"] == "text" else {}))
            sub(nv, "p:nvPr")
            prop = sub(sp, "p:spPr")
            if segment:
                (x1, y1), (x2, y2) = segment
                attrs = {}
                if x2 < x1: attrs["flipH"] = "1"
                if y2 < y1: attrs["flipV"] = "1"
                transform(prop, min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1), **attrs)
                sub(sub(prop, "a:prstGeom", prst="line"), "a:avLst")
                stroke(prop, el["color"], el["width"], el["dashed"],
                       el["arrow"] and idx == len(segments)-1)
                continue
            transform(prop, el["x"], el["y"], el["w"], el["h"])
            geom = sub(prop, "a:prstGeom", prst="roundRect" if el.get("radius") else "rect")
            av = sub(geom, "a:avLst")
            if el.get("radius"):
                sub(av, "a:gd", name="adj", fmla="val 11000")
            if el["kind"] == "box":
                fill(prop, el["fill"])
                if el["stroke"]: stroke(prop, el["stroke"], 1.4, el["dashed"])
                else: sub(sub(prop, "a:ln"), "a:noFill")
                continue
            sub(prop, "a:noFill")
            sub(sub(prop, "a:ln"), "a:noFill")
            body = sub(sp, "p:txBody")
            bp = sub(body, "a:bodyPr", wrap="none", lIns="0", rIns="0", tIns="0", bIns="0", anchor="t")
            sub(bp, "a:noAutofit")
            sub(body, "a:lstStyle")
            for value in el["text"].split("\n"):
                para = sub(body, "a:p")
                pp = sub(para, "a:pPr", algn={"left":"l", "center":"ctr", "right":"r"}[el["align"]])
                sub(sub(pp, "a:lnSpc"), "a:spcPct", val="112000")
                sub(sub(pp, "a:spcAft"), "a:spcPts", val="0")
                run = sub(para, "a:r")
                rp = sub(run, "a:rPr", lang="zh-TW", sz=round(el["size"]*75), b="1" if el["bold"] else "0")
                fill(rp, el["color"])
                sub(rp, "a:latin", typeface=FONT)
                sub(rp, "a:ea", typeface=FONT)
                sub(rp, "a:cs", typeface=FONT)
                sub(run, "a:t").text = value
                sub(para, "a:endParaRPr", lang="zh-TW", sz=round(el["size"]*75))
    return E.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", type=Path, default=DEFAULT_DECK)
    args = parser.parse_args()
    deck = args.deck.resolve()
    with ZipFile(deck) as z:
        infos = z.infolist()
        before = {i.filename: z.read(i.filename) for i in infos}
    presentation = E.fromstring(before["ppt/presentation.xml"])
    relationships = E.fromstring(before["ppt/_rels/presentation.xml.rels"])
    rels = {r.get("Id"): r.get("Target") for r in relationships}
    page = presentation.find("p:sldIdLst", NS)[11]
    target = rels[page.get(q("r:id"))]
    part = posixpath.normpath(posixpath.join("ppt", target)) if not target.startswith("/") else target[1:]
    old_text = " ".join(E.fromstring(before[part]).xpath("//a:t/text()", namespaces=NS))
    if not all(word in old_text for word in ["PCF", "SMF", "UPF", "P-CSCF"]):
        raise ValueError("Page 12 is not the architecture slide; refusing to replace another page")
    archive = HERE / "original-slide12.xml"
    if not archive.exists():
        archive.write_bytes(before[part])
    diagram()
    xml = build_xml(before[part])
    out = deck.with_suffix(".building.pptx")
    with ZipFile(out, "w") as z:
        for info in infos:
            z.writestr(info, xml if info.filename == part else before[info.filename])
    with ZipFile(out) as z:
        assert z.testzip() is None
        changed = [name for name, data in before.items() if z.read(name) != data]
        assert set(z.namelist()) == set(before)
        assert set(changed) <= {part}, changed
        # Ensure XML remains parseable and shape IDs unique.
        slide = E.fromstring(z.read(part))
        ids = slide.xpath("//p:cNvPr/@id", namespaces=NS)
        assert len(ids) == len(set(ids))
    out.replace(deck)
    (HERE / "slide12.xml").write_bytes(xml)
    (HERE / "layout.json").write_text(json.dumps(elements, ensure_ascii=False, indent=2)+"\n")
    report = dict(deck=deck.name, page=12, part=part,
                  total_slides=len(presentation.find("p:sldIdLst", NS)),
                  changed_parts=changed, other_parts_preserved=len(before)-1,
                  native_editable_shapes=len(ids)-1,
                  original_slide_sha256=sha(archive.read_bytes()),
                  rebuilt_slide_sha256=sha(xml), deck_sha256=sha(deck.read_bytes()))
    (HERE / "verification.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
