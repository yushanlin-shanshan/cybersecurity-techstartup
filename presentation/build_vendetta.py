#!/usr/bin/env python3
"""Expanded English pitch for the existing Sumi / Vendetta deck.

Keeps the live exercise, the product name, the four features, the
notification toggles, the $20 price, and the conclusion line.
Replaces the Venus/Mercury placeholder and fills the empty slides.

    python3 presentation/build_vendetta.py
"""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

W, H = 10.0, 5.625

TEAL = RGBColor(0x15, 0x81, 0x58)
ROSE = RGBColor(0xCC, 0x52, 0x7A)
ROSE_DEEP = RGBColor(0x9A, 0x34, 0x58)
INK = RGBColor(0x1C, 0x16, 0x1A)
MUTED = RGBColor(0x5C, 0x4C, 0x54)
PAPER = RGBColor(0xFB, 0xF6, 0xF4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xF0, 0xD5, 0xDE)
GOLD = RGBColor(0xE7, 0xC2, 0xA0)

FONT = "Poppins"


def rgb(fill, color):
    fill.solid()
    fill.fore_color.rgb = color


def _set_run(run, size, color, bold, italic, tracking):
    run.font.name = FONT
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
        r_pr.append(r_pr.makeelement(qn(tag), {"typeface": FONT}))
    if tracking is not None:
        r_pr.set("spc", str(int(tracking)))


def text(slide, content, x, y, w, h, size=15, color=INK, bold=False, italic=False,
         align="left", anchor="top", leading=1.0, tracking=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    for edge in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, edge, Emu(0))
    tf._txBody.find(qn("a:bodyPr")).set(
        "anchor", {"top": "t", "middle": "ctr", "bottom": "b"}[anchor]
    )
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
        _set_run(run, size, color, bold, italic, tracking)
    return shape


def rect(slide, x, y, w, h, fill, line=None, radius=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    rgb(shape.fill, fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.0)
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


def send_back(slide, shape):
    sp_tree = slide.shapes._spTree
    el = shape._element
    sp_tree.remove(el)
    sp_tree.insert(2, el)


def add_slide(prs, kind):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    shape.line.fill.background()
    if kind == "grad":
        shape.fill.gradient()
        shape.fill.gradient_angle = 115
        shape.fill.gradient_stops[0].color.rgb = TEAL
        shape.fill.gradient_stops[1].color.rgb = ROSE
    else:
        rgb(shape.fill, PAPER)
    send_back(slide, shape)
    return slide


def notes(slide, body):
    slide.notes_slide.notes_text_frame.text = body.strip()


def footer(slide, n, kind):
    color = WHITE if kind == "grad" else MUTED
    text(slide, "Product vision  |  Pitch deck", 0.42, 5.28, 5.5, 0.24, size=10, color=color, bold=True, tracking=40)
    text(slide, f"{n:02d}", 8.55, 5.28, 1.05, 0.24, size=10, color=color, bold=True, align="right")


def label(slide, value, x, y, color, w=8):
    text(slide, value, x, y, w, 0.24, size=11, color=color, bold=True, tracking=140)


def charm(slide, x, y, s=1.0):
    oval(slide, x + 0.28 * s, y, 0.38 * s, 0.38 * s, GOLD)
    oval(slide, x + 0.38 * s, y + 0.1 * s, 0.18 * s, 0.18 * s, PAPER if s < 1.2 else WHITE)
    oval(slide, x, y + 0.32 * s, 0.94 * s, 1.05 * s, GOLD)
    oval(slide, x + 0.1 * s, y + 0.42 * s, 0.74 * s, 0.85 * s, WHITE)
    oval(slide, x + 0.26 * s, y + 0.58 * s, 0.42 * s, 0.48 * s, RGBColor(0xF3, 0xC2, 0xD0))
    oval(slide, x + 0.40 * s, y + 0.72 * s, 0.12 * s, 0.12 * s, ROSE)


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "Vendetta — expanded pitch"
    prs.core_properties.subject = "Sumi exercise, then Vendetta, a charm that notices Meta glasses"
    prs.core_properties.author = "Livia Aschheim"
    n = 0

    def finish(slide, kind):
        nonlocal n
        n += 1
        footer(slide, n, kind)
        return slide

    # 1 Sumi
    s = add_slide(prs, "grad")
    text(s, "SUMI", 0.55, 1.15, 8.8, 0.28, size=13, color=WHITE, bold=True, tracking=220, align="center")
    text(s, "Sumi", 0.5, 1.5, 9, 1.15, size=60, color=WHITE, bold=True, align="center")
    text(s, "A mental health connection app", 0.6, 2.75, 8.8, 0.4, size=18, color=WHITE, align="center")
    text(s, "Product vision   ·   Pitch deck   ·   2026", 0.6, 4.55, 8.8, 0.3, size=12, color=WHITE, align="center")
    finish(s, "grad")
    notes(s, """
Say it straight, like a logistics update. Do not smile like a prank.

"Quick change. This is Sumi, a mental health connection app. We need five volunteers. Step outside with us for a moment."

Tell the professor the day before: the next few slides are a staged feeling, and nobody records or livestreams. If they say no, start at Vendetta.

Livia opens. Fill the other two names before you present.
""")

    # 2 volunteers
    s = add_slide(prs, "grad")
    text(s, "BEFORE WE START", 0.55, 1.35, 8.8, 0.28, size=13, color=WHITE, bold=True, tracking=180, align="center")
    text(s, "We need\n5 volunteers.", 0.6, 1.75, 8.8, 2.0, size=44, color=WHITE, bold=True, align="center", leading=0.95)
    text(s, "Leave your stuff. Come outside for ten seconds.", 0.6, 4.15, 8.8, 0.35, size=16, color=WHITE, align="center")
    finish(s, "grad")
    notes(s, "Pick five people who can keep a straight face. Not the professor. One of you walks them out and reads the hallway script. It is in the appendix. Do not project that script.")

    # 3 prompt
    s = add_slide(prs, "paper")
    label(s, "THE IMPORTANCE OF CONNECTION", 0.48, 0.38, ROSE_DEEP)
    text(s, "Groups of two or three.\nOne minute.", 0.45, 0.72, 9, 1.15, size=32, color=INK, bold=True, leading=0.95)
    rect(s, 0.48, 2.15, 9.05, 2.55, WHITE, line=LINE, radius=0.08)
    text(s, "THE PROMPT", 0.75, 2.35, 8.5, 0.25, size=12, color=ROSE_DEEP, bold=True, tracking=120)
    text(s, "Share something you've\nstruggled with this week.", 0.75, 2.7, 8.4, 1.15, size=26, color=INK, bold=True, leading=0.98)
    text(s, "Ordinary is fine. You do not owe anyone a confession.", 0.75, 4.05, 8.4, 0.35, size=14, color=MUTED)
    finish(s, "paper")
    notes(s, """
Volunteers are seated again. Phones face up, on the lock screen, untouched.

"Sumi is the conversation. Phones on the table. Don't touch them. How your week went is enough."

If someone will not put a phone down, let them. Do not collect phones. Then click to the hold slide and start 75 seconds.
""")

    # 4 hold
    s = add_slide(prs, "paper")
    label(s, "SIXTY SECONDS", 0.48, 1.35, ROSE_DEEP)
    text(s, "Something you struggled\nwith this week.", 0.45, 1.7, 9, 1.6, size=34, color=INK, bold=True, leading=0.96)
    text(s, "Then we move on.", 0.48, 3.7, 8, 0.35, size=16, color=MUTED)
    finish(s, "paper")
    notes(s, "Leave this up. Stay quiet. If someone is actually distressed, end it early and skip the plot-twist slide. Go straight to the clear slide.")

    # 5 plot twist
    s = add_slide(prs, "grad")
    text(s, "PLOT TWIST", 0.5, 1.15, 9, 0.28, size=13, color=WHITE, bold=True, tracking=200, align="center")
    text(s, "We had the volunteers\nlivestream your\ndiscussions.", 0.55, 1.55, 8.9, 2.5, size=34, color=WHITE, bold=True, align="center", leading=0.98)
    finish(s, "grad")
    notes(s, """
One second of silence. Then say their line flat: "The five people who stepped outside were livestreaming you."

Look at the volunteers, not at the person who just shared. Do not repeat anyone's story. Do not joke. If the room is already shaky, skip ahead to the clear slide immediately.
""")

    # 6 clear
    s = add_slide(prs, "paper")
    label(s, "CLEAR", 0.48, 0.42, TEAL)
    text(s, "Nobody livestreamed you.", 0.45, 0.78, 9, 0.55, size=28, color=INK, bold=True)
    text(s, "Nothing was posted.", 0.45, 1.4, 9, 0.5, size=28, color=INK, bold=True)
    text(s, "Nothing exists.", 0.45, 2.02, 9, 0.5, size=28, color=INK, bold=True)
    rect(s, 0.48, 2.85, 9.05, 1.85, WHITE, line=LINE, radius=0.08)
    text(s, "Phones up. Lock screen. Camera closed.", 0.75, 3.1, 8.5, 0.4, size=18, color=INK, bold=True)
    text(s, "There is no stream, no clip, and no link.\nShow the room. Take your time.", 0.75, 3.6, 8.5, 0.75, size=15, color=MUTED, leading=1.05)
    finish(s, "paper")
    notes(s, """
This slide is not optional. Say it before anything clever.

"Nobody livestreamed you. I need you to see that before anything else. Phones up. There is no stream, no file, nothing to post."

If a volunteer actually recorded or went live, stop. Delete it in front of the room. Tell the professor. Do not pitch today.

Do not ask anyone to repeat what they said.
""")

    # 7 consent
    s = add_slide(prs, "paper")
    label(s, "WHAT THAT WAS FOR", 0.48, 0.32, ROSE_DEEP)
    text(s, "No one wants to be recorded\nwithout consent.", 0.45, 0.62, 9.1, 1.2, size=28, color=INK, bold=True, leading=0.96)
    rect(s, 0.45, 2.1, 2.95, 2.7, WHITE, line=LINE, radius=0.08)
    rect(s, 3.52, 2.1, 2.95, 2.7, WHITE, line=LINE, radius=0.08)
    rect(s, 6.6, 2.1, 2.95, 2.7, WHITE, line=LINE, radius=0.08)
    cards = [
        (0.62, "THE PHONE", "Face up on the table.\nIt looked like manners.\nIt could still have been a mic."),
        (3.7, "THE GLASSES", "Meta glasses sit at eye level.\nA small capture light is the warning.\nYou have to be looking at the frame."),
        (6.78, "THE GAP", "You were talking.\nYou were not inspecting anyone.\nYou still would not have known."),
    ]
    for x, title, body in cards:
        text(s, title, x, 2.28, 2.6, 0.4, size=12, color=ROSE_DEEP, bold=True, tracking=80)
        text(s, body, x, 2.8, 2.6, 1.7, size=13, color=INK, leading=1.05)
    finish(s, "paper")
    notes(s, """
"Meta's AI glasses do have a capture LED. It blinks for a photo and stays on through a video. Cover that light and the camera is supposed to stop. We are not claiming the glasses are secret.

The gap is smaller than a scandal and bigger than a shrug. The light helps the person who is looking at the frame. A voice memo has no light at all. For one minute, you were that person."
""")

    # 8 requirement
    s = add_slide(prs, "grad")
    text(s, "THE REQUIREMENT", 0.5, 0.85, 9, 0.26, size=12, color=WHITE, bold=True, tracking=160)
    text(s, "Your phone was\non the table.", 0.48, 1.25, 9, 1.4, size=34, color=WHITE, bold=True, leading=0.95)
    text(s, "You were acting normal.\nYou still would not have known.", 0.5, 2.9, 8.8, 0.9, size=18, color=WHITE, leading=1.05)
    text(s, "Sumi was the exercise. Vendetta is the product.", 0.5, 4.15, 8.8, 0.4, size=16, color=WHITE, bold=True)
    finish(s, "grad")
    notes(s, "Slow down. This is the hinge into the real pitch. Four requirements follow from the minute you just ran: phone down, acting normal, signal during the conversation, and no accusation afterward.")

    # 9 Vendetta title
    s = add_slide(prs, "grad")
    text(s, "THE ACTUAL PRODUCT", 0.5, 0.7, 7, 0.24, size=12, color=WHITE, bold=True, tracking=160)
    text(s, "Vendetta", 0.45, 1.0, 7.2, 0.9, size=48, color=WHITE, bold=True)
    text(s, "A cute wearable that notices\nMeta glasses.", 0.5, 2.05, 6.6, 0.9, size=20, color=WHITE, leading=1.02)
    text(s, "Small enough for a key ring, a zipper, or a bag.", 0.5, 3.15, 6.8, 0.4, size=14, color=WHITE)
    text(s, "Livia Aschheim    ·    [ Name ]    ·    [ Name ]", 0.5, 4.35, 7.2, 0.3, size=13, color=WHITE)
    charm(s, 7.7, 1.55, 1.55)
    finish(s, "grad")
    notes(s, "Hold up a charm, even paper and ribbon, if you have one. A bare circuit board is the old mistake: it looks like a detector, so people will not carry it. Vendetta has to look like something you already clip on.")

    # 10 features
    s = add_slide(prs, "paper")
    label(s, "FEATURES", 0.45, 0.28, ROSE_DEEP)
    text(s, "Four words. Each one is a behavior.", 0.42, 0.52, 9, 0.4, size=22, color=INK, bold=True)
    feats = [
        ("01", "Discreet", "No screen to check. A tap, a tiny light, or a soft sound. Each one can be turned off."),
        ("02", "Continuous", "While it is on, it keeps noticing Meta glasses nearby. It does not record the room."),
        ("03", "Privacy forward", "A warning, not a name. No audio saved. No list of who walked by."),
        ("04", "Cute", "A pendant-sized charm. On keys, a zipper, or a bag. Cute is why it leaves the house."),
    ]
    for i, (num, title, body) in enumerate(feats):
        x = 0.4 + (i % 4) * 2.38
        rect(s, x, 1.2, 2.25, 3.55, WHITE, line=LINE, radius=0.1)
        text(s, num, x + 0.14, 1.38, 1.9, 0.28, size=12, color=ROSE_DEEP, bold=True)
        text(s, title, x + 0.14, 1.75, 1.95, 0.7, size=16, color=INK, bold=True)
        text(s, body, x + 0.14, 2.55, 1.95, 1.9, size=12, color=MUTED, leading=1.05)
    finish(s, "paper")
    notes(s, "Read the four, then stop. The next slides are the proof of each word. If you are short on time, keep Discreet and Cute, and let questions cover the rest.")

    # 11 cute
    s = add_slide(prs, "paper")
    label(s, "CUTE IS THE PRODUCT", 0.45, 0.32, ROSE_DEEP)
    text(s, "A detector people will not\nwear is the same as no detector.", 0.42, 0.62, 9.1, 1.05, size=24, color=INK, bold=True, leading=0.98)
    rect(s, 0.42, 1.95, 4.4, 2.85, WHITE, line=LINE, radius=0.08)
    rect(s, 5.05, 1.95, 4.5, 2.85, WHITE, line=LINE, radius=0.08)
    text(s, "THE GADGET VERSION", 0.62, 2.15, 4.0, 0.28, size=12, color=ROSE_DEEP, bold=True, tracking=80)
    text(s, "Black plastic.\nA lamp on the front.\nIt announces the job,\nso it stays in a drawer.", 0.62, 2.55, 3.9, 1.9, size=15, color=INK, leading=1.05)
    text(s, "VENDETTA", 5.25, 2.15, 4.0, 0.28, size=12, color=TEAL, bold=True, tracking=80)
    text(s, "Enamel and a small ring.\nThe sensor is sealed inside.\nFrom a meter away,\nit is a charm.", 5.25, 2.55, 4.0, 1.9, size=15, color=INK, leading=1.05)
    finish(s, "paper")
    notes(s, "This is the design thesis. The first objects in this category looked like keychain gadgets. They could do the job and people still left them at home. Vendetta keeps the wearable idea and changes the finish. Cute is not decoration on top of the product. Cute is how the product gets worn.")

    # 12 how it works
    s = add_slide(prs, "paper")
    label(s, "HOW IT ACTUALLY WORKS", 0.45, 0.26, ROSE_DEEP)
    text(s, "Two signals. Both already public.", 0.42, 0.5, 9, 0.4, size=22, color=INK, bold=True)
    rect(s, 0.4, 1.1, 4.5, 3.15, WHITE, line=LINE, radius=0.08)
    rect(s, 5.1, 1.1, 4.5, 3.15, INK, radius=0.08)
    text(s, "A PAIR IS HERE", 0.6, 1.28, 4.1, 0.26, size=12, color=ROSE_DEEP, bold=True, tracking=80)
    text(s, "Meta glasses speak\nBluetooth while they are on.\n\nVendetta recognizes that\nfamily, a few meters away.\n\nOrdinary eyeglasses stay quiet.", 0.6, 1.65, 4.1, 2.35, size=14, color=INK, leading=1.02)
    text(s, "THE LIGHT IS ON", 5.3, 1.28, 4.1, 0.26, size=12, color=GOLD, bold=True, tracking=80)
    text(s, "Meta publishes the pattern.\nA blink for a photo.\nOn through a video.\n\nA sensor in the charm\nwatches for that blink\nand changes the alert.", 5.3, 1.65, 4.1, 2.35, size=14, color=WHITE, leading=1.02)
    finish(s, "paper")
    notes(s, """
Replace the old Venus and Mercury boxes. Those were template filler. Say so if anyone remembers them: "That slide was a placeholder. This is the mechanism."

Be precise. Do not quote radio identifiers, and do not describe covering the LED.

"First signal: the glasses are nearby and powered. Second signal: Meta's own capture light is blinking, which means a photo or a video. We use the signals they already send. We do not claim to catch a silent microphone in a pocket."
""")

    # 13 two alerts
    s = add_slide(prs, "paper")
    label(s, "CONTINUOUS, WITHOUT BUZZING ALL DAY", 0.45, 0.28, ROSE_DEEP)
    text(s, "Idle is one tap.\nCapturing stays.", 0.42, 0.55, 9, 1.05, size=28, color=INK, bold=True, leading=0.95)
    rect(s, 0.42, 1.85, 4.45, 2.9, WHITE, line=LINE, radius=0.08)
    rect(s, 5.1, 1.85, 4.48, 2.9, WHITE, line=LINE, radius=0.08)
    text(s, "ONE SOFT TAP", 0.62, 2.05, 4.0, 0.26, size=12, color=TEAL, bold=True, tracking=80)
    text(s, "Glasses arrived.", 0.62, 2.4, 4.0, 0.4, size=18, color=INK, bold=True)
    text(s, "A pair came into range.\nThen silence. A room full\nof idle glasses cannot\npulse for an hour.", 0.62, 2.95, 4.0, 1.5, size=14, color=MUTED, leading=1.05)
    text(s, "A LONGER PULSE", 5.3, 2.05, 4.0, 0.26, size=12, color=ROSE_DEEP, bold=True, tracking=80)
    text(s, "The light is on.", 5.3, 2.4, 4.0, 0.4, size=18, color=INK, bold=True)
    text(s, "For as long as the capture\nlight blinks. It stops when\nthe blink stops. This is\nthe alert that matters.", 5.3, 2.95, 4.0, 1.5, size=14, color=MUTED, leading=1.05)
    finish(s, "paper")
    notes(s, "Knock the table once, then knock a slow pair, so the room hears the difference. Continuous monitoring means Vendetta stays awake. It does not mean a constant alarm. If those two feel the same, people take it off by Wednesday.")

    # 14 notifying
    s = add_slide(prs, "paper")
    label(s, "NOTIFYING SYSTEM", 0.45, 0.26, ROSE_DEEP)
    text(s, "You choose how it tells you.", 0.42, 0.5, 9, 0.4, size=24, color=INK, bold=True)
    rows = [
        ("Light", "A tiny lamp on the back of the charm, toward you. Off by default in a bright room."),
        ("Sound", "A short tone. Easy to turn off in class, at dinner, in a library."),
        ("Buzz", "The default. A tap through the charm into your hand or your bag strap."),
        ("A text you wrote", "Optional. After a capture alert, your phone can send a line you saved earlier."),
    ]
    for i, (title, body) in enumerate(rows):
        y = 1.1 + i * 0.95
        text(s, f"0{i+1}", 0.48, y, 0.55, 0.3, size=14, color=ROSE_DEEP, bold=True)
        text(s, title, 1.15, y - 0.02, 2.6, 0.32, size=16, color=INK, bold=True)
        text(s, body, 3.8, y - 0.02, 5.7, 0.7, size=13, color=MUTED)
    finish(s, "paper")
    notes(s, """
Examples of the preset text, said out loud so they hear how small it is: "Look up." Or, to a friend, "Call me in two minutes."

The message is written by the wearer, ahead of time. Vendetta does not draft a sentence about who it saw. It does not attach audio. It does not text the person wearing the glasses.

Default for a normal day: buzz only. Light, sound, and text each have their own off switch. All four can be off, which is just a charm again.
""")

    # 15 privacy
    s = add_slide(prs, "paper")
    label(s, "PRIVACY FORWARD", 0.45, 0.28, ROSE_DEEP)
    text(s, "A notice, not a verdict.", 0.42, 0.54, 9, 0.45, size=26, color=INK, bold=True)
    items = [
        ("No recording", "Vendetta does not store audio, video, or a transcript."),
        ("No names", "The tap means nearby, and right now. It does not mean who."),
        ("No tracking", "Nothing is kept once the glasses leave conversation distance."),
        ("No bypass", "It does not cover, disable, or work around the capture LED."),
        ("No proof", "Silence is not safety. It means no Meta glasses in view, and no blink."),
    ]
    for i, (title, body) in enumerate(items):
        y = 1.15 + i * 0.75
        text(s, title, 0.48, y, 2.5, 0.32, size=14, color=INK, bold=True)
        text(s, body, 3.15, y, 6.4, 0.55, size=13, color=MUTED)
    finish(s, "paper")
    notes(s, "Read them. If Vendetta ever shows a classmate's name, we built the wrong product. A cute object that accuses people is worse than an ugly gadget.")

    # 16 three moments
    s = add_slide(prs, "paper")
    label(s, "THREE MOMENTS", 0.45, 0.26, ROSE_DEEP)
    text(s, "Most minutes, it does nothing.", 0.42, 0.5, 9, 0.4, size=22, color=INK, bold=True)
    moments = [
        ("Monday", "Seminar", "Someone's glasses capture the board. The pulse lasts as long as the blink. You look up, see the photo, go back to notes."),
        ("Thursday", "This class", "Several pairs are idle. One tap as people sit down. Then quiet. You forget it is a device. That is the success."),
        ("Saturday", "Dinner", "The capture light stays on. You do not hold up a phone and you do not accuse. You feel it, and you choose the next sentence."),
    ]
    for i, (day, place, body) in enumerate(moments):
        y = 1.1 + i * 1.28
        rect(s, 0.42, y, 9.15, 1.18, WHITE, line=LINE, radius=0.08)
        text(s, day, 0.6, y + 0.14, 2.0, 0.24, size=11, color=ROSE_DEEP, bold=True, tracking=60)
        text(s, place, 0.6, y + 0.42, 2.1, 0.4, size=16, color=INK, bold=True)
        text(s, body, 2.85, y + 0.22, 6.45, 0.8, size=13, color=INK, leading=1.02)
    finish(s, "paper")
    notes(s, "Thursday answers the obvious objection: a room that likes these glasses would hate a charm that vibrates the entire class. Presence is a courtesy tap. Recording is the product.")

    # 17 audience and price
    s = add_slide(prs, "paper")
    label(s, "WHO IT IS FOR", 0.45, 0.28, ROSE_DEEP)
    text(s, "About $20.\nPriced like a charm.", 0.42, 0.55, 9, 1.05, size=28, color=INK, bold=True, leading=0.95)
    cols = [
        ("PRIMARY", "People who already buy a small accessory, and will not carry a tactical device."),
        ("ALSO", "Privacy-conscious friends, students, and anyone who likes the glasses and still wants the other seat protected."),
        ("NOT THIS", "Sumi was the exercise. Vendetta is not a mental health treatment, and it is not a medical device."),
    ]
    for i, (title, body) in enumerate(cols):
        x = 0.42 + i * 3.15
        rect(s, x, 1.9, 3.0, 2.85, WHITE, line=LINE, radius=0.08)
        text(s, title, x + 0.16, 2.08, 2.7, 0.28, size=12, color=ROSE_DEEP, bold=True, tracking=80)
        text(s, body, x + 0.16, 2.5, 2.68, 1.95, size=13, color=INK, leading=1.05)
    finish(s, "paper")
    notes(s, "The $20 is a ceiling we are willing to say out loud, because the object has to compete with a bag charm, not with a phone. If the parts cost more than that, the report should say the price moves. Do not invent a market size.")

    # 18 what 20 buys
    s = add_slide(prs, "paper")
    label(s, "WHAT THE PRICE COVERS", 0.45, 0.3, ROSE_DEEP)
    text(s, "A charm, two signals, and the switches.", 0.42, 0.58, 9.1, 0.45, size=22, color=INK, bold=True)
    left = [
        "The pendant and the ring",
        "A battery for a day of class, until we measure longer",
        "Bluetooth recognition of Meta glasses",
        "The capture-blink sensor",
        "Light, sound, buzz, and the preset text",
    ]
    right = [
        "A promise to catch every hidden mic",
        "A name, a face, or a saved clip",
        "A way around Meta's capture LED",
        "A medical or therapy claim",
        "A price lower than the parts, just to sound generous",
    ]
    text(s, "IN THE BOX", 0.48, 1.2, 4.3, 0.28, size=12, color=TEAL, bold=True, tracking=80)
    text(s, "NOT IN THE BOX", 5.15, 1.2, 4.4, 0.28, size=12, color=ROSE_DEEP, bold=True, tracking=80)
    for i, line in enumerate(left):
        text(s, line, 0.48, 1.6 + i * 0.58, 4.4, 0.45, size=13, color=INK)
    for i, line in enumerate(right):
        text(s, line, 5.15, 1.6 + i * 0.58, 4.4, 0.45, size=13, color=INK)
    finish(s, "paper")
    notes(s, "If they ask for a bill of materials, say we do not have one yet. Twenty dollars is the product position, not a quote from a factory. The first prototype is a dev board inside a paper charm. We will not flicker an LED and call it Bluetooth.")

    # 19 tests
    s = add_slide(prs, "paper")
    label(s, "BEFORE THE REPORT", 0.45, 0.26, ROSE_DEEP)
    text(s, "Four tests. One of them is\nwhether it is cute enough.", 0.42, 0.52, 9, 0.95, size=24, color=INK, bold=True, leading=0.96)
    tests = [
        ("01", "Wear", "Will someone clip it on because they like it, the way they clip on any other charm?"),
        ("02", "Meta, not everything", "Does a pair of Meta glasses tap it across this table, while ordinary glasses do not?"),
        ("03", "The blink", "Can the sensor tell a capture blink from a ceiling light? If not, we ship presence only, and we say so."),
        ("04", "Today", "Did this exercise make you want Vendetta, or only startle you? We ask that after class, on paper."),
    ]
    for i, (num, title, body) in enumerate(tests):
        col = i % 2
        row = i // 2
        x = 0.42 + col * 4.8
        y = 1.7 + row * 1.6
        text(s, num, x, y, 0.55, 0.28, size=13, color=ROSE_DEEP, bold=True)
        text(s, title, x + 0.6, y - 0.02, 3.9, 0.3, size=15, color=INK, bold=True)
        text(s, body, x + 0.6, y + 0.32, 3.95, 1.05, size=12, color=MUTED, leading=1.02)
    finish(s, "paper")
    notes(s, "Test 04 is what makes the exercise legitimate. Today is a feeling, not evidence. One unsigned question after class. If the answer is that we only startled them, the report says so.")

    # 20 glasses wearers
    s = add_slide(prs, "grad")
    text(s, "FOR THE PEOPLE WEARING THEM", 0.48, 0.55, 9, 0.26, size=12, color=WHITE, bold=True, tracking=120)
    text(s, "Keep the glasses.", 0.45, 0.95, 9, 0.6, size=32, color=WHITE, bold=True)
    lines = [
        "A camera you don't have to hold is a good camera.",
        "Vendetta uses the Bluetooth they already speak, and the blink they already show.",
        "The tap lands on the person who did not press record.",
        "A wearer who wants the same courtesy clips Vendetta on, too.",
    ]
    for i, line in enumerate(lines):
        text(s, line, 0.5, 1.8 + i * 0.7, 9, 0.5, size=16, color=WHITE)
    finish(s, "grad")
    notes(s, "Do not sneer at Meta or at anyone in the room who likes the glasses. The offer is a private tap. The glasses stay on the face that chose them. If someone says the LED already solves it, agree, then point at the gap: you only get that LED if you are looking at the frame.")

    # 21 risks
    s = add_slide(prs, "paper")
    label(s, "SAID OUT LOUD", 0.45, 0.28, ROSE_DEEP)
    text(s, "The ways this goes wrong.", 0.42, 0.54, 9, 0.4, size=24, color=INK, bold=True)
    risks = [
        ("A room of idle glasses.", "If presence and recording feel the same, the charm comes off. The two taps have to differ."),
        ("Cute as a disguise.", "A pretty object that secretly records the room is worse than a gadget. Vendetta listens for a signal. It does not capture."),
        ("The text can expose you.", "A message that fires at dinner can be louder than a buzz. Text is opt-in. Buzz is the default."),
        ("The exercise was a false premise.", "The next sentence had to be that nothing exists. The professor hears the plan first."),
    ]
    for i, (title, body) in enumerate(risks):
        y = 1.15 + i * 0.95
        text(s, title, 0.48, y, 9.0, 0.3, size=14, color=INK, bold=True)
        text(s, body, 0.48, y + 0.32, 9.0, 0.45, size=13, color=MUTED)
    finish(s, "paper")
    notes(s, "Volunteer this before they ask. If the room is still annoyed about the livestream line, stay on this slide and take it.")

    # 22 conclusion
    s = add_slide(prs, "grad")
    text(s, "CONCLUSION", 0.5, 0.85, 9, 0.26, size=12, color=WHITE, bold=True, tracking=180)
    text(s, "You may not have control\nover who is recording you.", 0.5, 1.3, 9, 1.3, size=26, color=WHITE, bold=True, leading=0.98)
    text(s, "You should be able to know\nif it is happening to you.", 0.5, 2.8, 9, 1.15, size=26, color=WHITE, bold=True, leading=0.98)
    text(s, "Vendetta is that knowledge, on something you will actually wear.", 0.5, 4.2, 9, 0.45, size=14, color=WHITE)
    finish(s, "grad")
    notes(s, "Use their sentence. Then one breath, and stop. Do not recap all 20 slides.")

    # 23 thank you
    s = add_slide(prs, "grad")
    text(s, "Vendetta", 0.5, 1.35, 9, 0.35, size=14, color=WHITE, bold=True, tracking=200, align="center")
    text(s, "Thank you.", 0.5, 1.85, 9, 1.0, size=48, color=WHITE, bold=True, align="center")
    text(s, "Questions.", 0.5, 3.15, 9, 0.4, size=18, color=WHITE, align="center")
    text(s, "Livia Aschheim    ·    [ Name ]    ·    [ Name ]", 0.5, 4.2, 9, 0.3, size=14, color=WHITE, align="center")
    finish(s, "grad")
    notes(s, "Be quiet after Questions. If the room is cold, add one line: if the exercise was not worth it, we want that on the record.")

    # 24 appendix
    s = add_slide(prs, "grad")
    text(s, "APPENDIX", 0.5, 1.7, 9, 0.3, size=13, color=WHITE, bold=True, tracking=200, align="center")
    text(s, "Do not project\nthe rest.", 0.5, 2.1, 9, 1.4, size=36, color=WHITE, bold=True, align="center", leading=0.95)
    text(s, "Run of show, hallway script, repairs, sources.", 0.5, 3.8, 9, 0.35, size=14, color=WHITE, align="center")
    finish(s, "grad")
    notes(s, "Stop sharing the screen here if you are presenting from this file.")

    # 25 run of show
    s = add_slide(prs, "paper")
    label(s, "RUN OF SHOW", 0.42, 0.22, ROSE_DEEP)
    text(s, "About nine minutes. The scare is not the grade.", 0.42, 0.46, 9, 0.32, size=16, color=INK, bold=True)
    rows = [
        ("0:00", "Sumi", "Five volunteers. Straight face."),
        ("0:30", "Hallway", "Read the script. They sit. Nobody records."),
        ("1:15", "Prompt", "75 seconds. Watch for distress, not for stories."),
        ("2:45", "Plot twist", "One second. Skip it if the room is already shaky."),
        ("3:00", "Clear", "Phones up before any joke."),
        ("3:30", "Vendetta", "Cute, how it works, the two taps, the text."),
        ("8:30", "Conclusion", "Their sentence. Then questions."),
    ]
    for i, (t, name, detail) in enumerate(rows):
        y = 0.9 + i * 0.58
        text(s, t, 0.42, y, 0.9, 0.35, size=13, color=ROSE_DEEP, bold=True)
        text(s, name, 1.4, y, 1.8, 0.35, size=13, color=INK, bold=True)
        text(s, detail, 3.3, y, 6.2, 0.4, size=13, color=MUTED)
    finish(s, "paper")
    notes(s, "Short on time: Sumi through Clear, then Vendetta, how it works, and the conclusion.")

    # 26 hallway
    s = add_slide(prs, "paper")
    label(s, "HALLWAY  ·  READ IT", 0.42, 0.24, ROSE_DEEP)
    text(s, "Nobody outside is recording anything.", 0.42, 0.5, 9, 0.35, size=18, color=INK, bold=True)
    script = [
        "Walk back in separately. Sit down.",
        "Phone face up, lock screen. Don't touch it.",
        "Do not open the camera. Do not go live. Do not take notes.",
        "Look ordinary. If you smirk, the exercise dies.",
        "When we say phones up, show the lock screen.",
        "If anyone looks upset, don't wait. Phones up first.",
    ]
    for i, line in enumerate(script):
        y = 1.0 + i * 0.65
        oval(s, 0.45, y, 0.32, 0.32, INK)
        text(s, str(i + 1), 0.45, y + 0.02, 0.32, 0.28, size=11, color=WHITE, bold=True, align="center")
        text(s, line, 0.95, y, 8.5, 0.35, size=14, color=INK)
    finish(s, "paper")
    notes(s, "Screenshot this onto the phone of whoever walks them out. Add: if one of you hits record as a joke, we stop and delete it in front of everyone.")

    # 27 lines
    s = add_slide(prs, "paper")
    label(s, "LINES", 0.42, 0.22, ROSE_DEEP)
    pairs = [
        ("Open", "This is Sumi. We need five volunteers outside."),
        ("Prompt", "How your week went is enough. You don't owe a confession."),
        ("Twist", "We had the volunteers livestream your discussions."),
        ("Clear", "Nobody livestreamed you. Nothing exists. Phones up."),
        ("Product", "Vendetta notices Meta glasses. It looks like a charm."),
        ("Limit", "Idle is one tap. Capturing stays. We do not name anyone."),
        ("Close", "You should be able to know if it is happening to you."),
    ]
    for i, (k, v) in enumerate(pairs):
        y = 0.55 + i * 0.64
        text(s, k.upper(), 0.42, y, 1.5, 0.4, size=12, color=ROSE_DEEP, bold=True)
        text(s, v, 2.05, y, 7.4, 0.45, size=14, color=INK)
    finish(s, "paper")
    notes(s, "If you forget everything else, say the clear line and the limit line.")

    # 28 if it breaks + sources
    s = add_slide(prs, "paper")
    label(s, "IF THEY ASK", 0.42, 0.2, ROSE_DEEP)
    qas = [
        ("Glasses already have an LED.", "Yes. We use it. The blink is on their frame. Vendetta puts that fact on your charm."),
        ("Can you detect a hidden mic?", "No. Vendetta notices Meta glasses, and the capture blink those glasses publish."),
        ("Won't it buzz all class?", "Idle is one tap. The pulse stays only while the capture light is on."),
        ("Isn't the text a privacy problem?", "You write it. You opt in. It names nobody and attaches nothing. Buzz is the default."),
    ]
    for i, (q, a) in enumerate(qas):
        y = 0.48 + i * 0.95
        text(s, q, 0.42, y, 9.1, 0.28, size=13, color=INK, bold=True)
        text(s, a, 0.42, y + 0.3, 9.1, 0.5, size=12, color=MUTED)
    finish(s, "paper")
    notes(s, """
Sources, read the morning you present. If a detail has changed, their page wins.

Meta privacy page: https://www.meta.com/ai-glasses/privacy/
Meta newsroom, July 2026: https://about.fb.com/news/2026/07/metas-ai-glasses-your-questions-answered/

The LED blinks for a photo and stays on through video. Meta says it has no off switch, and that covering or destroying it disables the camera. We do not describe how to tamper with it.

Presentation session: May 11, 2026, 10 points. Written report: Sunday, May 17, 2026, 15 points. The upload box also says Friday by 5:10pm. Confirm which file that is.

A volunteer who actually records is a hard stop.
""")

    out = "/workspace/Vendetta.pptx"
    prs.save(out)
    prs.save("/workspace/presentation/Vendetta-Pitch-EXPANDED.pptx")
    print(f"saved {out} slides={len(prs.slides)}")


if __name__ == "__main__":
    build()
