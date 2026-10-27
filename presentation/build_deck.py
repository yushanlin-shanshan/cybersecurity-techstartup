#!/usr/bin/env python3
"""Assignment 5 deck. English.

Live open: the staged exercise from the group.
Product: Opal, a small ornament that notices Meta glasses.
The earlier keychain is the thing this replaces. It worked, and it was ugly,
so people would not wear it.

Rebuild:
    python3 presentation/build_deck.py
"""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

W, H = 13.333333, 7.5

CREAM = RGBColor(0xF4, 0xEF, 0xE6)
INK = RGBColor(0x16, 0x14, 0x12)
MUTED = RGBColor(0x6F, 0x68, 0x5E)
TERR = RGBColor(0xC4, 0x49, 0x2C)
BLACK = RGBColor(0x0E, 0x0D, 0x0C)
IVORY = RGBColor(0xF6, 0xF1, 0xE8)
AMBER = RGBColor(0xE3, 0x9B, 0x12)
GREEN = RGBColor(0x1C, 0x68, 0x44)
LINE = RGBColor(0xE0, 0xD7, 0xC8)
WHITE = RGBColor(0xFF, 0xFC, 0xF8)
GOLD = RGBColor(0xC6, 0xA1, 0x5A)
GOLD_INK = RGBColor(0x8A, 0x5E, 0x32)
STONE = RGBColor(0xF7, 0xF1, 0xE8)
BLUSH = RGBColor(0xE4, 0xC8, 0xB8)
FIRE = RGBColor(0xD8, 0x84, 0x62)

FONT = "Arial"
PRODUCT = "Opal"


def rgb(shape_fill, color):
    shape_fill.solid()
    shape_fill.fore_color.rgb = color


def add_slide(prs, bg):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    rgb(shape.fill, bg)
    shape.line.fill.background()
    sp_tree = slide.shapes._spTree
    el = shape._element
    sp_tree.remove(el)
    sp_tree.insert(2, el)
    return slide


def _set_run(run, font, size, color, bold, italic, tracking):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    r_pr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        node = r_pr.find(qn(tag))
        if node is not None:
            r_pr.remove(node)
    for tag in ("a:latin", "a:ea", "a:cs"):
        r_pr.append(r_pr.makeelement(qn(tag), {"typeface": font}))
    if tracking is not None:
        r_pr.set("spc", str(int(tracking)))


def text(
    slide,
    content,
    x,
    y,
    w,
    h,
    size=18,
    color=INK,
    bold=False,
    italic=False,
    align="left",
    anchor="top",
    leading=1.0,
    tracking=None,
    font=FONT,
):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    body_pr = tf._txBody.find(qn("a:bodyPr"))
    body_pr.set("anchor", {"top": "t", "middle": "ctr", "bottom": "b"}[anchor])
    align_enum = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
    lines = content.split("\n") if isinstance(content, str) else list(content)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align_enum
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        p.line_spacing = leading
        run = p.add_run()
        run.text = line
        _set_run(run, font, size, color, bold, italic, tracking)
    return shape


def rect(slide, x, y, w, h, fill, line=None, radius=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    rgb(shape.fill, fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.25)
    if radius:
        try:
            shape.adjustments[0] = radius
        except Exception:
            pass
    return shape


def oval(slide, x, y, w, h, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h))
    rgb(shape.fill, fill)
    shape.line.fill.background()
    return shape


def rule(slide, x, y, w, color, weight=1.25):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Pt(weight))
    rgb(shape.fill, color)
    shape.line.fill.background()
    return shape


def notes(slide, body):
    frame = slide.notes_slide.notes_text_frame
    frame.text = body.strip()


def footer(slide, n, kind, dark=False):
    muted = RGBColor(0x8A, 0x84, 0x78) if not dark else RGBColor(0x5C, 0x58, 0x52)
    if kind == "pitch":
        text(slide, "OPAL", 0.72, 7.08, 5.5, 0.26, size=11, color=muted, bold=True, tracking=180)
    elif kind == "appendix":
        text(slide, "APPENDIX    ·    DO NOT PROJECT", 0.72, 7.08, 8, 0.26, size=11, color=muted, bold=True, tracking=140)
    text(slide, f"{n:02d}", 11.7, 7.08, 0.9, 0.26, size=11, color=muted, bold=True, align="right")


def label(slide, value, x, y, color, w=10):
    text(slide, value, x, y, w, 0.28, size=13, color=color, bold=True, tracking=180)


def draw_pin(slide, x, y, s=1.0):
    oval(slide, x, y, 1.72 * s, 1.72 * s, GOLD)
    oval(slide, x + 0.13 * s, y + 0.13 * s, 1.46 * s, 1.46 * s, STONE)
    oval(slide, x + 0.40 * s, y + 0.40 * s, 0.92 * s, 0.92 * s, BLUSH)
    oval(slide, x + 0.70 * s, y + 0.58 * s, 0.22 * s, 0.22 * s, FIRE)
    oval(slide, x + 0.98 * s, y + 0.78 * s, 0.10 * s, 0.10 * s, WHITE)


def draw_clip(slide, x, y, s=1.0):
    rect(slide, x, y + 0.62 * s, 2.15 * s, 0.22 * s, GOLD, radius=0.5)
    oval(slide, x + 0.28 * s, y + 0.18 * s, 0.95 * s, 1.10 * s, GOLD)
    oval(slide, x + 0.38 * s, y + 0.30 * s, 0.75 * s, 0.86 * s, STONE)
    oval(slide, x + 0.55 * s, y + 0.48 * s, 0.40 * s, 0.48 * s, BLUSH)
    oval(slide, x + 0.68 * s, y + 0.60 * s, 0.12 * s, 0.12 * s, FIRE)


def draw_charm(slide, x, y, s=1.0):
    oval(slide, x + 0.48 * s, y, 0.62 * s, 0.62 * s, GOLD)
    oval(slide, x + 0.64 * s, y + 0.16 * s, 0.30 * s, 0.30 * s, CREAM)
    rect(slide, x + 0.72 * s, y + 0.52 * s, 0.14 * s, 0.22 * s, GOLD, radius=0.4)
    oval(slide, x + 0.28 * s, y + 0.68 * s, 1.05 * s, 1.22 * s, GOLD)
    oval(slide, x + 0.40 * s, y + 0.80 * s, 0.81 * s, 0.98 * s, STONE)
    oval(slide, x + 0.58 * s, y + 1.00 * s, 0.44 * s, 0.52 * s, BLUSH)
    oval(slide, x + 0.72 * s, y + 1.16 * s, 0.12 * s, 0.12 * s, FIRE)


def draw_old_fob(slide, x, y, s=1.0):
    oval(slide, x + 0.42 * s, y, 0.70 * s, 0.70 * s, RGBColor(0x3A, 0x38, 0x36))
    oval(slide, x + 0.58 * s, y + 0.16 * s, 0.38 * s, 0.38 * s, CREAM)
    rect(slide, x + 0.68 * s, y + 0.62 * s, 0.18 * s, 0.16 * s, RGBColor(0x3A, 0x38, 0x36), radius=0.3)
    rect(slide, x, y + 0.74 * s, 1.55 * s, 1.85 * s, RGBColor(0x2A, 0x28, 0x26), radius=0.12)
    oval(slide, x + 0.42 * s, y + 1.15 * s, 0.70 * s, 0.70 * s, RGBColor(0xC4, 0x49, 0x2C))
    oval(slide, x + 0.62 * s, y + 1.35 * s, 0.30 * s, 0.30 * s, RGBColor(0xE8, 0x7A, 0x62))


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "Opal — Assignment 5"
    prs.core_properties.subject = "A small ornament that notices Meta glasses"
    prs.core_properties.category = "Presentation"
    prs.core_properties.author = "Session 2 team"
    n = 0

    def finish(slide, kind, dark=False):
        nonlocal n
        n += 1
        footer(slide, n, kind, dark)
        return slide

    # 1
    s = add_slide(prs, CREAM)
    label(s, "A SMALL CHANGE OF PLAN", 0.78, 1.35, TERR)
    text(s, "Beside", 0.75, 1.75, 10, 1.35, size=84, color=INK, bold=True, leading=0.9)
    rule(s, 0.8, 3.25, 2.1, TERR, 3.5)
    text(s, "We changed our product.", 0.78, 3.5, 10, 0.6, size=32, color=INK, bold=True)
    text(s, "A mental health connection app.", 0.78, 4.2, 10, 0.5, size=24, color=MUTED)
    text(s, "Five volunteers. Step outside with us for a moment.", 0.78, 6.35, 10, 0.4, size=18, color=INK)
    finish(s, "bit")
    notes(
        s,
        """
Say this straight. Do not smile like a prank.

"Quick change before we start. We dropped the old idea. This is Beside. A mental health connection app. We need five volunteers. Leave your stuff. Come outside for ten seconds."

Pick five people who can keep a straight face. Tell the professor the day before: slides 1 through 7 are a staged feeling, and nobody records. If they say no, start on the Opal title.

If the class never heard a prior product, drop "we changed our product" and say: "We want to start with a one-minute exercise. It's called Beside."
""",
    )

    # 2
    s = add_slide(prs, CREAM)
    label(s, "BESIDE", 0.78, 0.42, TERR)
    text(s, "Phones down.", 0.75, 1.05, 12, 0.9, size=60, color=INK, bold=True)
    text(
        s,
        "Groups of two or three. One minute.\nTalk to the people next to you.",
        0.78,
        2.15,
        11,
        1.15,
        size=28,
        color=INK,
        leading=1.05,
    )
    rule(s, 0.8, 3.55, 11.7, LINE, 1.25)
    text(s, "01", 0.78, 3.85, 1.0, 0.4, size=18, color=TERR, bold=True)
    text(s, "Something from this week you would not post.", 1.9, 3.82, 9.5, 0.45, size=22, color=INK, bold=True)
    text(s, "02", 0.78, 4.55, 1.0, 0.4, size=18, color=TERR, bold=True)
    text(s, "An embarrassing thing, or just how the week went.", 1.9, 4.52, 9.5, 0.45, size=22, color=INK, bold=True)
    text(s, "03", 0.78, 5.25, 1.0, 0.4, size=18, color=TERR, bold=True)
    text(s, "We'll tell you when to stop. Ordinary is fine.", 1.9, 5.22, 9.5, 0.45, size=22, color=INK, bold=True)
    text(s, "Don't perform it. Actually say it.", 0.78, 6.35, 10, 0.4, size=18, color=MUTED, italic=True)
    finish(s, "bit")
    notes(
        s,
        """
Volunteers are back in their seats. Phones face up, lock screen, untouched.

"Beside is the conversation. Phones on the table. Face up is fine. Don't touch them."

If someone will not put a phone down, let them. Do not collect phones.

Say the easy version out loud: "How your week went is enough. You do not owe anyone an embarrassing story."

Click to the prompt and start a 75-second timer. Stay at the front. Do not write down what anyone says.
""",
    )

    # 3
    s = add_slide(prs, CREAM)
    label(s, "SIXTY SECONDS", 0.78, 1.85, TERR)
    text(
        s,
        "Something from this week\nyou would not post.",
        0.75,
        2.3,
        12,
        2.4,
        size=48,
        color=INK,
        bold=True,
        leading=0.98,
    )
    text(s, "Then we move on.", 0.78, 5.5, 8, 0.4, size=20, color=MUTED)
    finish(s, "bit")
    notes(
        s,
        """
Leave this up. Seventy-five seconds. If someone is actually distressed, end it: "That's a minute. Phones up, we're good." Then go to the clear slide and skip both black slides.
""",
    )

    # 4
    s = add_slide(prs, BLACK)
    text(s, "BEFORE WE GO ON", 0.78, 1.9, 10, 0.3, size=13, color=AMBER, bold=True, tracking=180)
    text(s, "The volunteers\nwere recording you.", 0.75, 2.35, 12, 2.5, size=60, color=IVORY, bold=True, leading=0.95)
    finish(s, "bit", dark=True)
    notes(
        s,
        """
One full second of silence. Then, flat: "The five people who stepped outside put their phones down so they could record."

Look at the volunteers. Do not repeat anyone's story. If the room already feels bad, skip the next slide.
""",
    )

    # 5
    s = add_slide(prs, BLACK)
    text(s, "ONE MORE THING", 0.78, 1.9, 10, 0.3, size=13, color=AMBER, bold=True, tracking=180)
    text(s, "We might post\nthe clips.", 0.75, 2.35, 12, 2.5, size=64, color=IVORY, bold=True, leading=0.95)
    finish(s, "bit", dark=True)
    notes(
        s,
        """
One breath. Do not add a joke. Do not point at a person. If anyone looks genuinely upset, click straight to the next slide.

This slide is optional. Cut it if the first black slide already landed, or if the professor asked for a smaller scare.
""",
    )

    # 6
    s = add_slide(prs, CREAM)
    label(s, "CLEAR", 0.78, 1.15, GREEN)
    text(s, "Nobody recorded you.", 0.75, 1.6, 12, 0.75, size=44, color=INK, bold=True)
    text(s, "Nothing was posted.", 0.75, 2.4, 12, 0.7, size=44, color=INK, bold=True)
    text(s, "Nothing exists.", 0.75, 3.2, 12, 0.7, size=44, color=INK, bold=True)
    rect(s, 0.78, 4.7, 8.6, 1.15, WHITE, line=LINE, radius=0.1)
    text(s, "Phones up. Lock screen. Camera closed.", 1.05, 4.85, 8.1, 0.4, size=20, color=INK, bold=True)
    text(s, "Show the room. Take your time.", 1.05, 5.32, 8.1, 0.35, size=16, color=MUTED)
    finish(s, "bit")
    notes(
        s,
        """
Say this before anything clever.

"Nobody recorded you. I need you to see that before anything else. Phones up. Lock screens. There is no clip, no file, nothing to post."

If a volunteer actually recorded, stop. Delete it in front of the room. Tell the professor. Do not continue the pitch that day.

Do not ask anyone to repeat what they said.
""",
    )

    # 7
    s = add_slide(prs, CREAM)
    label(s, "WHAT THAT PROVED", 0.78, 1.55, TERR)
    text(s, "Your phone was\non the table.", 0.75, 2.05, 12, 1.9, size=48, color=INK, bold=True, leading=0.96)
    text(
        s,
        "You were acting normal.\nYou still would not have known.",
        0.78,
        4.25,
        11,
        1.2,
        size=28,
        color=INK,
        leading=1.05,
    )
    text(s, "That is the product requirement.", 0.78, 5.85, 10, 0.4, size=20, color=TERR, bold=True)
    finish(s, "bit")
    notes(
        s,
        """
"We told you to put the useful object down and act normal. You still would not have known. Whatever we build has to work while you are dressed as yourself, in that room. Beside was the exercise. Here is the product."
""",
    )

    # 8 real title
    s = add_slide(prs, CREAM)
    label(s, "THE ACTUAL PRODUCT", 0.78, 1.35, GOLD_INK)
    text(s, PRODUCT, 0.75, 1.75, 8, 1.05, size=72, color=INK, bold=True)
    text(s, "A small ornament that\nnotices Meta glasses.", 0.78, 3.05, 8.2, 1.25, size=28, color=INK, leading=1.02)
    rule(s, 0.8, 4.55, 2.1, GOLD, 3.5)
    text(s, "Discreet enough to wear. Finished enough that you will.", 0.78, 4.8, 8.2, 0.4, size=18, color=MUTED)
    text(s, "Beside was the demo.", 0.78, 5.4, 7, 0.35, size=16, color=MUTED)
    text(s, "[ Name ]     ·     [ Name ]     ·     [ Name ]", 0.78, 6.35, 8, 0.35, size=14, color=MUTED)
    draw_pin(s, 10.15, 2.15, 1.35)
    finish(s, "pitch")
    notes(
        s,
        """
"This is what we actually brought. Opal. It notices Meta glasses, and it looks like something you already put on."

Hold up the prop here if you have one: a pin, a hair clip, or a bag charm. Cardboard is fine if it looks considered. A bare dev board is the old mistake.

Fill in the three names before you present.
""",
    )

    # 9 the ugly keychain
    s = add_slide(prs, CREAM)
    label(s, "THE VERSION PEOPLE ALREADY TRIED", 0.75, 0.38, GOLD_INK)
    text(s, "The keychain could detect.\nNobody wanted it out.", 0.72, 0.82, 12, 1.4, size=36, color=INK, bold=True, leading=0.96)
    rect(s, 0.72, 2.6, 5.7, 3.9, WHITE, line=LINE, radius=0.08)
    rect(s, 6.7, 2.6, 5.9, 3.9, WHITE, line=LINE, radius=0.08)
    draw_old_fob(s, 2.95, 2.82, 0.78)
    text(s, "KEYCHAIN", 1.05, 5.15, 5.1, 0.28, size=13, color=TERR, bold=True, tracking=140, align="center")
    text(s, "A gadget. A light. A job it announced.", 1.0, 5.5, 5.2, 0.55, size=16, color=MUTED, align="center")
    draw_pin(s, 8.79, 2.85, 1.0)
    text(s, "OPAL", 7.0, 5.15, 5.4, 0.28, size=13, color=GOLD_INK, bold=True, tracking=140, align="center")
    text(s, "Same awareness. Worn as a small decoration.", 7.05, 5.5, 5.3, 0.55, size=16, color=MUTED, align="center")
    finish(s, "pitch")
    notes(
        s,
        """
This is the design thesis. Do not sneer for long.

"There is already a version of this idea. It is a keychain. It can do the job, and it looks like it can do the job. So it stays in a bag. An ugly detector at dinner is a statement. People decline the statement. Then the product is the same as not having one.

Opal is the correction. The sensing is sealed inside a pin, a clip, or a charm. From across the table it is jewelry. The only signal is a tap, and only the person wearing it feels the tap."
""",
    )

    # 10 this room
    s = add_slide(prs, CREAM)
    label(s, "THIS ROOM", 0.78, 0.42, GOLD_INK)
    text(s, "Keep the glasses.", 0.75, 0.9, 12, 0.8, size=48, color=INK, bold=True)
    text(
        s,
        "A camera you don't have to hold is a better camera.\nOpal is for the person who didn't press record.",
        0.78,
        1.9,
        11.5,
        1.1,
        size=24,
        color=INK,
        leading=1.08,
    )
    rect(s, 0.78, 3.4, 5.7, 3.05, WHITE, line=LINE, radius=0.08)
    rect(s, 6.7, 3.4, 5.85, 3.05, WHITE, line=LINE, radius=0.08)
    text(s, "WHAT YOU ALREADY THINK", 1.05, 3.62, 5.2, 0.3, size=13, color=GOLD_INK, bold=True, tracking=100)
    text(s, "Hands free.\nThe shot is from your eyes.\nThe glasses are worth liking.", 1.05, 4.15, 5.1, 1.8, size=22, color=INK, leading=1.12)
    text(s, "THE OTHER SEAT", 6.98, 3.62, 5.2, 0.3, size=13, color=TERR, bold=True, tracking=120)
    text(s, "They didn't press it.\nThey may not be looking\nat the frame.", 6.98, 4.15, 5.2, 1.8, size=22, color=INK, leading=1.12)
    finish(s, "pitch")
    notes(
        s,
        """
Do not sneer at Meta or at anyone who likes the glasses.

"You can like them. We do. Opal does not ask anyone to take them off. It is for the other person at the table."

If someone says "they already have an LED," answer: "Yes. Next slide. We use that light. We do not pretend it isn't there."
""",
    )

    # 11 what it notices
    s = add_slide(prs, CREAM)
    label(s, "WHAT OPAL NOTICES", 0.75, 0.36, GOLD_INK)
    text(s, "Meta glasses.\nAnd when they are capturing.", 0.72, 0.78, 12, 1.35, size=36, color=INK, bold=True, leading=0.96)
    rect(s, 0.72, 2.5, 5.85, 3.95, WHITE, line=LINE, radius=0.08)
    rect(s, 6.8, 2.5, 5.8, 3.95, INK, radius=0.08)
    text(s, "A PAIR IS HERE", 1.0, 2.75, 5.3, 0.3, size=13, color=GOLD_INK, bold=True, tracking=140)
    text(
        s,
        "Meta glasses speak Bluetooth\nwhile they are on.\n\nOpal recognizes that family,\na few meters away.\n\nOrdinary eyeglasses stay silent.\nThey have nothing to say.",
        1.0,
        3.2,
        5.2,
        2.9,
        size=18,
        color=INK,
        leading=1.05,
    )
    text(s, "THE LIGHT IS ON", 7.1, 2.75, 5.2, 0.3, size=13, color=GOLD, bold=True, tracking=140)
    text(
        s,
        "Meta publishes the pattern.\nA blink for a photo.\nA continuing blink for video.\n\nA seed-sized sensor behind\nthe ornament feels that blink\nand changes the tap.",
        7.1,
        3.2,
        5.2,
        2.9,
        size=18,
        color=IVORY,
        leading=1.05,
    )
    finish(s, "pitch")
    notes(
        s,
        """
Be precise. This room will punish a fake claim.

"Two different facts. First: a pair of Meta glasses is nearby. They already broadcast over Bluetooth while they are powered. Ordinary glasses do not. Opal listens for that family, at the distance of a conversation. We do not store a name, and we do not follow anyone out of the room.

Second: they are capturing. Meta's own capture LED blinks for a photo and stays on through a video. The sensor is behind the face of the pin, looking at the room. When it sees that blink, the tap changes. One soft tap means the glasses arrived. A longer pulse means the light is on. The pulse stops when the blink stops.

If every pair in this room buzzed for the whole class, the product would be unbearable. Idle glasses get one tap. Capturing is the signal that stays."

Do not quote protocol bytes, radio identifiers, or a method for covering the LED. If asked how the radio is recognized: "The glasses already announce themselves. We match that family. The report will cite Meta's privacy page for the light, and describe the radio match at the level of a product, not a teardown."
""",
    )

    # 12 discreet
    s = add_slide(prs, CREAM)
    label(s, "QUIET ON THE OUTSIDE", 0.75, 0.38, GOLD_INK)
    text(s, "The room sees jewelry.\nYou feel a tap.", 0.72, 0.82, 8.2, 1.45, size=36, color=INK, bold=True, leading=0.96)
    rows = [
        ("No lamp on the front", "A detector with its own light is the ugly keychain again. Opal's face is enamel and metal."),
        ("The sensor is sealed in", "The way a watch hides its gears. From a meter away there is nothing to read."),
        ("The tap is private", "It lands on skin, through the back of the pin or the clip. You can know, and the table can stay a table."),
    ]
    for i, (title, body) in enumerate(rows):
        y = 2.55 + i * 1.35
        text(s, f"0{i+1}", 0.78, y, 0.7, 0.35, size=16, color=GOLD_INK, bold=True)
        text(s, title, 1.7, y - 0.02, 10, 0.36, size=22, color=INK, bold=True)
        text(s, body, 1.7, y + 0.42, 10.5, 0.65, size=16, color=MUTED)
    draw_pin(s, 11.15, 0.42, 0.72)
    finish(s, "pitch")
    notes(
        s,
        """
"隐蔽" in the brief means the object disappears into what you already wear. Say it in those words, not as a spy gadget.

"We do not want a thing you have to hide in your hand. We want a thing nobody reads as a device. The concealment is the finish. Pin, clip, charm. The information stays on your body, because announcing it to the whole table would be the keychain with better manners."
""",
    )

    # 13 the set
    s = add_slide(prs, CREAM)
    label(s, "THE SMALL DECORATIONS", 0.75, 0.34, GOLD_INK)
    text(s, "One sensor. Three things\nyou would actually wear.", 0.72, 0.72, 12, 1.25, size=34, color=INK, bold=True, leading=0.96)
    draw_pin(s, 1.55, 2.35, 1.15)
    draw_clip(s, 5.35, 2.45, 1.2)
    draw_charm(s, 9.35, 2.25, 1.15)
    cols = [
        (0.7, "PIN", "On a jacket or a collar.\nThe face toward the room.\nThe tap on the chest."),
        (4.85, "CLIP", "In the hair, or on a strap.\nAlready part of getting dressed.\nNothing new to remember."),
        (9.0, "CHARM", "On the bag you set down.\nIt stays out while the phone\ngoes face up and useless."),
    ]
    for x, title, body in cols:
        text(s, title, x, 4.7, 3.6, 0.35, size=14, color=GOLD_INK, bold=True, tracking=140, align="center")
        text(s, body, x, 5.1, 3.6, 1.15, size=15, color=INK, align="center", leading=1.05)
    finish(s, "pitch")
    notes(
        s,
        """
Point at each one.

"The pin is the clearest. The clip is the one you forget you are wearing, which is the highest compliment we can pay it. The charm is the callback: the phone was on the table and could not help. A charm on the bag is already out, and it does not look like equipment."

If you only bring one prop, bring the pin. It reads in the back row.
""",
    )

    # 14 why decoration
    s = add_slide(prs, CREAM)
    label(s, "WHY A DECORATION WINS", 0.75, 0.4, GOLD_INK)
    text(s, "The useful object is the one\nyou were going to wear anyway.", 0.72, 0.85, 12, 1.3, size=32, color=INK, bold=True, leading=0.98)
    items = [
        ("01", "The phone", "Right computer. Wrong moment. It was on the table, and looking at it meant leaving the conversation."),
        ("02", "The keychain", "Right job. Wrong finish. It advertised itself, so it lived in a drawer."),
        ("03", "The LED on the frame", "Right idea. It sits on the wearer. You get it only if you are looking at the temple."),
        ("04", "The ornament", "Already on you. Already allowed in the room. The signal arrives where you can feel it."),
    ]
    for i, (num, title, body) in enumerate(items):
        col = i % 2
        row = i // 2
        x = 0.72 + col * 6.3
        y = 2.5 + row * 2.05
        text(s, num, x, y, 0.8, 0.35, size=16, color=GOLD_INK, bold=True)
        text(s, title, x + 0.9, y - 0.02, 5.0, 0.4, size=22, color=INK, bold=True)
        text(s, body, x + 0.9, y + 0.5, 5.0, 1.15, size=16, color=MUTED, leading=1.05)
    finish(s, "pitch")
    notes(
        s,
        """
"An app fails the demo. A keychain fails the outfit. Opal has to survive both tests: you are not looking at a screen, and you are willing to be seen wearing it."
""",
    )

    # 15 the two taps
    s = add_slide(prs, CREAM)
    label(s, "WHAT YOU FEEL", 0.75, 0.4, GOLD_INK)
    text(s, "Idle is a tap.\nCapturing stays.", 0.72, 0.85, 12, 1.3, size=40, color=INK, bold=True, leading=0.96)
    rect(s, 0.72, 2.55, 5.85, 3.85, WHITE, line=LINE, radius=0.08)
    rect(s, 6.8, 2.55, 5.8, 3.85, WHITE, line=LINE, radius=0.08)
    text(s, "ONE SOFT TAP", 1.0, 2.8, 5.3, 0.3, size=13, color=GOLD_INK, bold=True, tracking=140)
    text(s, "Glasses arrived.", 1.0, 3.3, 5.2, 0.5, size=26, color=INK, bold=True)
    text(
        s,
        "A pair of Meta glasses came into\nthe conversation. Then silence.\nA room full of them cannot\nbuzz for an hour.",
        1.0,
        4.05,
        5.2,
        1.8,
        size=18,
        color=MUTED,
        leading=1.08,
    )
    text(s, "A LONGER PULSE", 7.08, 2.8, 5.2, 0.3, size=13, color=TERR, bold=True, tracking=140)
    text(s, "The light is on.", 7.08, 3.3, 5.2, 0.5, size=26, color=INK, bold=True)
    text(
        s,
        "Photo or video, for as long as\nMeta's capture light blinks.\nIt stops when the blink stops.\nThis is the one that matters.",
        7.08,
        4.05,
        5.2,
        1.8,
        size=18,
        color=MUTED,
        leading=1.08,
    )
    finish(s, "pitch")
    notes(
        s,
        """
Demonstrate with two knocks on the table if you have no hardware. One knock. Then a slow pair. Say which is which.

"If we only detected the glasses, this class would hate it by minute three. Half of you would be wearing them. Presence is a courtesy tap. Recording is the product."
""",
    )

    # 16 refusals
    s = add_slide(prs, CREAM)
    label(s, "WHAT IT REFUSES", 0.75, 0.42, GOLD_INK)
    text(s, "A notice, not a verdict.", 0.72, 0.88, 12, 0.65, size=36, color=INK, bold=True)
    refusals = [
        ("No recording", "Opal does not store audio, video, or a transcript."),
        ("No names", "The tap means nearby, and right now. It does not mean who."),
        ("No tracking", "Nothing is kept once the glasses leave the conversation."),
        ("No bypass", "It does not cover, disable, or work around the capture LED."),
        ("No proof", "Silence is not safety. It means no Meta glasses in view, and no blink."),
    ]
    for i, (title, body) in enumerate(refusals):
        y = 1.8 + i * 0.95
        text(s, title, 0.78, y, 3.5, 0.4, size=22, color=INK, bold=True)
        text(s, body, 4.5, y + 0.04, 8.0, 0.55, size=18, color=MUTED)
    finish(s, "pitch")
    notes(
        s,
        """
Read them. They are the product.

"If Opal ever tells you a classmate's name, we built the wrong thing. A decoration that accuses people is worse than the ugly keychain."
""",
    )

    # 17 for the wearers
    s = add_slide(prs, CREAM)
    label(s, "FOR THE PEOPLE WEARING THEM", 0.75, 0.38, GOLD_INK)
    text(s, "We use the signals\nthe glasses already send.", 0.72, 0.8, 12, 1.35, size=36, color=INK, bold=True, leading=0.96)
    steps = [
        ("1", "You keep them.", "Opal is not a reason to take the glasses off. The camera can stay good."),
        ("2", "The blink still counts.", "Meta's capture light is real. We move it from their frame to your skin."),
        ("3", "You can feel it later.", "A wearer who wants the same courtesy wears Opal too. The ornament does not care which seat you are in."),
    ]
    for i, (num, title, body) in enumerate(steps):
        x = 0.75 + i * 4.1
        oval(s, x, 2.55, 0.48, 0.48, INK)
        text(s, num, x, 2.61, 0.48, 0.36, size=16, color=IVORY, bold=True, align="center")
        text(s, title, x, 3.25, 3.8, 0.85, size=22, color=INK, bold=True)
        text(s, body, x, 4.2, 3.75, 1.5, size=16, color=MUTED, leading=1.08)
    text(
        s,
        "The offer is a private tap. The glasses stay on the face that chose them.",
        0.78,
        6.0,
        11.6,
        0.45,
        size=18,
        color=INK,
        bold=True,
    )
    finish(s, "pitch")
    notes(
        s,
        """
Land this slowly. It is how you win the room.

"If you wear them, you already accepted a light. We are not adding a lecture. We are letting the person across from you feel the blink without staring at your temple. And if you want that same tap when someone else is wearing a pair, Opal is a pin. It looks like a pin on you, too."
""",
    )

    # 18 three moments
    s = add_slide(prs, CREAM)
    label(s, "THREE MOMENTS", 0.75, 0.36, GOLD_INK)
    text(s, "Most minutes, it does nothing.", 0.72, 0.78, 12, 0.55, size=32, color=INK, bold=True)
    moments = [
        ("Monday", "Seminar", "Someone's Meta glasses are on for a photo of the board. The pulse lasts as long as the blink. You see them hold the moment up. Back to your notes."),
        ("Thursday", "This class", "Several pairs are in the room, idle. One tap as each sits down. Then quiet. You forget the pin is a device. That is the success."),
        ("Saturday", "Dinner", "The capture light stays on. You do not hold up a phone and you do not accuse. You feel it, and you choose what to say next."),
    ]
    for i, (day, place, body) in enumerate(moments):
        y = 1.6 + i * 1.7
        rect(s, 0.72, y, 11.9, 1.55, WHITE, line=LINE, radius=0.08)
        text(s, day, 1.0, y + 0.28, 2.4, 0.3, size=14, color=GOLD_INK, bold=True, tracking=80)
        text(s, place, 1.0, y + 0.65, 2.5, 0.45, size=20, color=INK, bold=True)
        text(s, body, 3.7, y + 0.32, 8.5, 1.0, size=18, color=INK, leading=1.05)
    finish(s, "pitch")
    notes(
        s,
        """
Thursday is the slide that answers "won't this buzz all day in a room that loves these glasses?" Say that sentence out loud.
""",
    )

    # 19 tests
    s = add_slide(prs, CREAM)
    label(s, "BEFORE THE REPORT", 0.75, 0.38, GOLD_INK)
    text(s, "Four tests. One of them\nis whether it is beautiful.", 0.72, 0.8, 12, 1.35, size=34, color=INK, bold=True, leading=0.96)
    tests = [
        ("01", "Wear", "Will someone put the pin on for a day, the way they put on any other pin? If they won't, the keychain problem is unsolved."),
        ("02", "Meta, not everything", "Does a pair of Meta glasses tap it across this table, while AirPods and ordinary eyeglasses do not?"),
        ("03", "The blink", "Can the sensor tell a capture blink from a ceiling light? If it cannot, we ship presence only, and we say so."),
        ("04", "Today", "Did this exercise make you want the tap, or just make you angry? We ask that after class, on paper."),
    ]
    for i, (num, title, body) in enumerate(tests):
        col = i % 2
        row = i // 2
        x = 0.72 + col * 6.3
        y = 2.45 + row * 2.15
        text(s, num, x, y, 0.8, 0.35, size=16, color=GOLD_INK, bold=True)
        text(s, title, x + 0.9, y - 0.02, 5.0, 0.4, size=20, color=INK, bold=True)
        text(s, body, x + 0.9, y + 0.48, 5.1, 1.35, size=15, color=MUTED, leading=1.05)
    finish(s, "pitch")
    notes(
        s,
        """
Spend time on 01 and 04.

"The last product failed because it was ugly. If Opal is also ugly, we have learned nothing. And today is a feeling, not evidence. After class, one unsigned question: do you want this tap, or did we only startle you? If the answer is the second, the report says so."
""",
    )

    # 20 risks
    s = add_slide(prs, CREAM)
    label(s, "SAID OUT LOUD", 0.75, 0.38, GOLD_INK)
    text(s, "The ways this goes wrong.", 0.72, 0.8, 12, 0.55, size=32, color=INK, bold=True)
    risks = [
        ("A room of idle glasses.", "If presence and recording feel the same, people take Opal off by Wednesday. The two taps have to be different."),
        ("Beauty as an excuse.", "A pretty object that secretly records the room is worse than an ugly keychain. The sensor listens and watches for a blink. It does not capture."),
        ("The blink can be missed.", "A pin facing forward misses glasses behind you. Bluetooth still says a pair is near. We will say which signal fired."),
        ("The exercise was a false premise.", "The next sentence had to be that nothing exists. The professor hears the plan first."),
    ]
    for i, (title, body) in enumerate(risks):
        y = 1.65 + i * 1.25
        rule(s, 0.78, y + 0.08, 0.42, GOLD, 3.5)
        text(s, title, 1.45, y - 0.08, 10.8, 0.36, size=18, color=INK, bold=True)
        text(s, body, 1.45, y + 0.34, 10.9, 0.7, size=15, color=MUTED)
    finish(s, "pitch")
    notes(
        s,
        """
Volunteer this before they ask. If the room is still annoyed about the exercise, stay here.
""",
    )

    # 21 close
    s = add_slide(prs, CREAM)
    draw_pin(s, 0.78, 1.7, 0.85)
    text(s, PRODUCT.upper(), 2.5, 1.95, 6, 0.45, size=16, color=GOLD_INK, bold=True, tracking=220, anchor="middle")
    text(s, "Notice Meta glasses.\nWear it anyway.", 0.75, 3.45, 12, 1.6, size=44, color=INK, bold=True, leading=0.96)
    text(s, "Before the sentence, not after.", 0.78, 5.3, 10, 0.4, size=22, color=INK)
    text(s, "Questions.", 0.78, 6.15, 4, 0.35, size=18, color=MUTED)
    finish(s, "pitch")
    notes(
        s,
        """
Stop. Do not recap the whole deck.

"You already felt the second. Opal is that second, on something you will actually wear. Questions."

Then be quiet.
""",
    )

    # 22 appendix
    s = add_slide(prs, INK)
    text(s, "APPENDIX", 0.78, 2.3, 12, 0.4, size=14, color=GOLD, bold=True, tracking=200)
    text(s, "Do not project\nthe rest.", 0.75, 2.75, 12, 1.8, size=52, color=IVORY, bold=True, leading=0.96)
    text(s, "Run of show, hallway script, repairs, report, sources.", 0.8, 5.0, 11, 0.4, size=18, color=RGBColor(0xC8, 0xC0, 0xB4))
    finish(s, "appendix", dark=True)
    notes(s, "Stop sharing the screen here.")

    # 23 run of show
    s = add_slide(prs, CREAM)
    label(s, "RUN OF SHOW", 0.72, 0.28, GOLD_INK)
    text(s, "About nine minutes. The scare is not the grade.", 0.72, 0.62, 12, 0.38, size=20, color=INK, bold=True)
    rows = [
        ("0:00", "Beside", "Five volunteers. Straight face."),
        ("0:30", "Hallway", "Read the script. They sit back down. Nobody records."),
        ("1:15", "Phones down", "Groups. Ordinary is allowed."),
        ("1:45", "Prompt", "75 seconds. Watch for distress, not for stories."),
        ("3:00", "Black slides", "One second of silence. Skip the second if the room is shaky."),
        ("3:15", "Clear", "Phones up before any joke."),
        ("3:40", "Requirement", "Phone on the table. Acting normal. Still didn't know."),
        ("4:00", "Opal", "Keychain, then Meta glasses, then the three ornaments."),
        ("9:00", "Questions", "Lead with: idle is one tap, capturing stays, we do not name anyone."),
    ]
    for i, (t, name, detail) in enumerate(rows):
        y = 1.15 + i * 0.6
        text(s, t, 0.72, y, 1.15, 0.4, size=15, color=GOLD_INK, bold=True)
        text(s, name, 1.95, y, 2.3, 0.4, size=16, color=INK, bold=True)
        text(s, detail, 4.4, y, 8.2, 0.45, size=16, color=MUTED)
    finish(s, "appendix")
    notes(s, "Short on time: Beside through Clear, then the keychain slide, what Opal notices, and the three ornaments.")

    # 24 hallway
    s = add_slide(prs, CREAM)
    label(s, "HALLWAY  ·  READ IT", 0.72, 0.32, TERR)
    text(s, "Nobody outside is recording anything.", 0.72, 0.72, 12, 0.45, size=26, color=INK, bold=True)
    script = [
        "Walk back in separately. Sit down.",
        "Phone face up, on the lock screen. Don't touch it.",
        "Do not open the camera. Do not open voice memos. Do not take notes.",
        "Look ordinary. If you smirk, the exercise dies.",
        "When we say phones up, show the lock screen. Camera closed.",
        "If anyone looks actually upset, don't wait. Phones up first.",
    ]
    for i, line in enumerate(script):
        y = 1.45 + i * 0.82
        oval(s, 0.78, y, 0.42, 0.42, INK)
        text(s, str(i + 1), 0.78, y + 0.05, 0.42, 0.34, size=14, color=IVORY, bold=True, align="center")
        text(s, line, 1.45, y + 0.02, 10.8, 0.48, size=20, color=INK)
    finish(s, "appendix")
    notes(s, "Screenshot this onto the phone of whoever walks them out, so it is not on the projector. Add: if one of you hits record as a joke, we stop and delete it in front of everyone.")

    # 25 lines
    s = add_slide(prs, CREAM)
    label(s, "LINES", 0.75, 0.32, GOLD_INK)
    text(s, "Say these. Don't decorate them.", 0.72, 0.68, 12, 0.45, size=26, color=INK, bold=True)
    left = [
        ("Open", "We changed our product. We need five volunteers outside."),
        ("Exercise", "How your week went is enough. You don't owe an embarrassing story."),
        ("Reveal", "The volunteers were recording you."),
        ("Clear", "Nobody recorded you. Nothing exists. Phones up."),
    ]
    right = [
        ("Hinge", "Your phone was on the table. You still would not have known."),
        ("Keychain", "It could detect. Nobody wanted it out."),
        ("Product", "Opal notices Meta glasses. It looks like a pin."),
        ("Limit", "Idle is one tap. Capturing stays. We do not name anyone."),
    ]
    for i, (k, v) in enumerate(left):
        y = 1.35 + i * 1.3
        text(s, k.upper(), 0.75, y, 5.5, 0.28, size=12, color=GOLD_INK, bold=True, tracking=120)
        text(s, v, 0.75, y + 0.32, 5.6, 0.75, size=16, color=INK)
    for i, (k, v) in enumerate(right):
        y = 1.35 + i * 1.3
        text(s, k.upper(), 7.0, y, 5.6, 0.28, size=12, color=TERR, bold=True, tracking=120)
        text(s, v, 7.0, y + 0.32, 5.6, 0.75, size=16, color=INK)
    finish(s, "appendix")
    notes(s, "If you forget everything else: the clear line, and the limit line.")

    # 26 breaks
    s = add_slide(prs, CREAM)
    label(s, "IF IT BREAKS", 0.75, 0.32, TERR)
    text(s, "Leave the bit. Keep the product.", 0.72, 0.68, 12, 0.42, size=26, color=INK, bold=True)
    cases = [
        ("Someone won't share", "Then talk about lunch. Beside doesn't get to demand a confession."),
        ("Someone is upset", "Clear slide, immediately. Skip the rest of the scare. Talk after class, not from the front."),
        ("A volunteer recorded", "Stop. Delete it in front of the room. Tell the professor. Do not pitch today."),
        ("The professor hates it", "Start at Opal. The ornament does not need the scare to make sense."),
        ("They say glasses already blink", "Agree. We use that blink. The gap is that you have to be looking at the frame."),
        ("They ask for a price", "We don't have a parts list. A price before that is fiction. The test is whether you would wear it."),
    ]
    for i, (title, body) in enumerate(cases):
        col = i % 2
        row = i // 2
        x = 0.72 + col * 6.3
        y = 1.35 + row * 1.75
        text(s, title, x, y, 6.0, 0.4, size=16, color=INK, bold=True)
        text(s, body, x, y + 0.42, 6.0, 1.0, size=15, color=MUTED, leading=1.05)
    finish(s, "appendix")
    notes(s, "A volunteer who actually recorded is a hard stop.")

    # 27 report
    s = add_slide(prs, CREAM)
    label(s, "WRITTEN REPORT  ·  15 POINTS", 0.75, 0.28, GOLD_INK)
    text(s, "Due Sunday, May 17, 2026.", 0.72, 0.62, 12, 0.4, size=26, color=INK, bold=True)
    sections = [
        ("1", "The scene", "A room that likes Meta glasses, and a table where phones were down."),
        ("2", "The exercise", "What you staged, what you refused to record, how the room reacted."),
        ("3", "The requirement", "Know, while acting normal, without looking at a screen or a temple."),
        ("4", "Why the keychain lost", "It could do the job. It looked like the job. People would not wear it."),
        ("5", "Opal", "Pin, clip, charm. Same sensor. Private tap. No lamp on the front."),
        ("6", "Meta, present", "Bluetooth the glasses already speak. A few meters. No name stored."),
        ("7", "Meta, capturing", "The published capture blink. A longer pulse. Idle is only one tap."),
        ("8", "Refusals", "No recording, no names, no tracking, no bypass, silence is not proof."),
        ("9", "Evidence", "Would you wear it? And, after class: want the tap, or just startled?"),
        ("10", "Team", "Who made the prop, who spoke, what you would build next."),
    ]
    for i, (num, title, body) in enumerate(sections):
        col = i // 5
        row = i % 5
        x = 0.72 + col * 6.3
        y = 1.2 + row * 1.08
        text(s, num, x, y, 0.4, 0.28, size=14, color=GOLD_INK, bold=True)
        text(s, title, x + 0.45, y, 5.5, 0.28, size=15, color=INK, bold=True)
        text(s, body, x + 0.45, y + 0.32, 5.6, 0.6, size=13, color=MUTED)
    finish(s, "appendix")
    notes(
        s,
        """
Presentation session: May 11, 2026, 10 points.
Written report: Sunday, May 17, 2026, 15 points.
The upload box also says Friday by 5:10pm, 10 points, file upload. Confirm which Friday, and which file, on the course page.
""",
    )

    # 28 blanks
    s = add_slide(prs, CREAM)
    label(s, "BEFORE YOU PRESENT", 0.75, 0.32, TERR)
    blanks = [
        ("Names", "Three names on the Opal title."),
        ("The professor", "The day before. Black slides are a feeling. Nobody records. A veto means you start at Opal."),
        ("A prop", "One finished-looking pin, even paper and gold tape. Hold it up at the title and at the set."),
        ("Honesty", "If the sensor is not built, do not flicker an LED and call it Bluetooth. Say what it will do."),
        ("The two taps", "Rehearse them as knocks. Idle, once. Capturing, a pulse. Do not blur them."),
        ("The survey", "After class, unsigned: do you want this, or were you only startled?"),
        ("Citations", "Read the two Meta pages the morning of. Quote the LED from the page."),
        ("Friday upload", "Confirm whether 5:10pm Friday is this file. Export a PDF as a backup."),
    ]
    for i, (title, body) in enumerate(blanks):
        col = i % 2
        row = i // 2
        x = 0.72 + col * 6.3
        y = 0.85 + row * 1.45
        text(s, title, x, y, 6.0, 0.32, size=16, color=INK, bold=True)
        text(s, body, x, y + 0.36, 6.0, 0.85, size=14, color=MUTED, leading=1.02)
    finish(s, "appendix")
    notes(s, "A opens and runs the hallway. B owns both black slides and the clear slide. C takes Opal through the close.")

    # 29 speakers
    s = add_slide(prs, CREAM)
    label(s, "WHO SPEAKS", 0.75, 0.38, GOLD_INK)
    text(s, "One person owns the scare.\nThey also own the apology.", 0.72, 0.8, 12, 1.15, size=28, color=INK, bold=True, leading=1.0)
    roles = [
        ("A", "The setup", "Beside, the volunteers, the hallway, phones down. Ends when the timer starts."),
        ("B", "The two seconds", "Both black slides and the clear slide. Calm. No jokes. If B freezes, A reads the clear line."),
        ("C", "The product", "From the requirement through questions. The keychain, then Opal. Does not retell stories."),
    ]
    for i, (who, title, body) in enumerate(roles):
        x = 0.75 + i * 4.1
        rect(s, x, 2.4, 3.9, 3.5, WHITE, line=LINE, radius=0.08)
        text(s, who, x + 0.25, 2.6, 3.4, 0.5, size=28, color=GOLD_INK, bold=True)
        text(s, title, x + 0.25, 3.25, 3.4, 0.5, size=20, color=INK, bold=True)
        text(s, body, x + 0.25, 3.9, 3.4, 1.6, size=15, color=MUTED, leading=1.05)
    finish(s, "appendix")
    notes(s, "B rehearses the clear line until it sounds like relief.")

    # 30 q and a
    s = add_slide(prs, CREAM)
    label(s, "IF THEY ASK", 0.75, 0.28, GOLD_INK)
    qas = [
        ("Glasses already have an LED.", "Yes. We use it. The blink is on their frame. Opal puts that fact on your skin, so you don't have to stare at the temple."),
        ("Can you detect a hidden mic?", "No. Opal notices Meta glasses, and the capture blink those glasses publish. A silent phone mic is a different problem, and we don't pretend."),
        ("Won't it buzz all class?", "Idle is one tap when a pair sits down. The pulse stays only while the capture light is on."),
        ("So it's just a prettier keychain.", "The keychain failed by being readable as a detector. If you will not wear Opal to dinner, we have the same failure in a nicer metal."),
    ]
    for i, (q, a) in enumerate(qas):
        y = 0.75 + i * 1.5
        text(s, q, 0.75, y, 12, 0.35, size=18, color=INK, bold=True)
        text(s, a, 0.75, y + 0.42, 11.8, 0.85, size=16, color=MUTED)
    finish(s, "appendix")
    notes(
        s,
        """
More, if you need them:

What about glasses behind me? The blink sensor faces forward with the pin. Bluetooth can still say a pair is near. We say which one fired.

Are you tracking people? No. We do not keep an identifier after they leave conversation distance. The tap is the whole output.

What if someone covers the LED? Meta says the camera is supposed to stop. We do not help anyone cover it, and we do not claim to see through tape.

Ordinary eyeglasses? No radio, no capture LED, no tap.

Cost? No parts list yet. A price before that is fiction.
""",
    )

    # 31 sources
    s = add_slide(prs, CREAM)
    label(s, "SOURCES FOR THE LED", 0.75, 0.38, GOLD_INK)
    text(s, "Read them the morning you present.", 0.72, 0.8, 12, 0.4, size=24, color=INK, bold=True)
    text(
        s,
        "Meta publishes a capture LED on its AI glasses. It blinks for a photo\nand stays on through a video. Meta says the light has no off switch,\nand that covering or destroying it disables the camera.",
        0.75,
        1.45,
        12,
        1.25,
        size=18,
        color=INK,
        leading=1.08,
    )
    rect(s, 0.75, 3.0, 11.85, 1.3, WHITE, line=LINE, radius=0.08)
    text(s, "META PRIVACY PAGE", 1.0, 3.18, 11, 0.28, size=12, color=GOLD_INK, bold=True, tracking=120)
    text(s, "https://www.meta.com/ai-glasses/privacy/", 1.0, 3.55, 11, 0.4, size=18, color=INK)
    rect(s, 0.75, 4.5, 11.85, 1.35, WHITE, line=LINE, radius=0.08)
    text(s, "META NEWSROOM, JULY 2026", 1.0, 4.68, 11, 0.28, size=12, color=GOLD_INK, bold=True, tracking=120)
    text(s, "https://about.fb.com/news/2026/07/metas-ai-glasses-your-questions-answered/", 1.0, 5.08, 11.2, 0.45, size=16, color=INK)
    text(
        s,
        "If a detail has changed by presentation day, their page wins and this slide loses.",
        0.78,
        6.15,
        11.5,
        0.35,
        size=15,
        color=MUTED,
    )
    finish(s, "appendix")
    notes(
        s,
        """
Our claim is narrower than Meta's. The LED is real. It helps the person who is looking at the frame. Opal notices the glasses by the Bluetooth they already speak, and notices capture by that published blink. We are not describing how to tamper with the light.
""",
    )

    out = "presentation/Opal-Assignment5.pptx"
    prs.save(out)
    print(f"saved {out} slides={len(prs.slides)}")


if __name__ == "__main__":
    build()
