#!/usr/bin/env python3
"""Assignment 5 draft deck.

The live bit (slides 1–7) follows the group chat.
The product slides turn that feeling into a keychain pitch.
Working name: Halo. Change it in PRODUCT if the team picks another.

Rebuild:
    python3 presentation/build_deck.py
"""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

W, H = 13.333333, 7.5

CREAM = RGBColor(0xF4, 0xEF, 0xE6)
INK = RGBColor(0x16, 0x14, 0x12)
MUTED = RGBColor(0x6F, 0x68, 0x5E)
TERR = RGBColor(0xC4, 0x49, 0x2C)
BLACK = RGBColor(0x0E, 0x0D, 0x0C)
IVORY = RGBColor(0xF6, 0xF1, 0xE8)
DIM = RGBColor(0x3C, 0x3A, 0x36)
AMBER = RGBColor(0xE3, 0x9B, 0x12)
AMBER_INK = RGBColor(0x8A, 0x52, 0x00)
GREEN = RGBColor(0x1C, 0x68, 0x44)
CARD = RGBColor(0xFB, 0xF8, 0xF3)
LINE = RGBColor(0xE0, 0xD7, 0xC8)
WHITE = RGBColor(0xFF, 0xFC, 0xF8)
SOFT = RGBColor(0xE7, 0xF2, 0xEB)

FONT = "Arial"
PRODUCT = "Halo"


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


def oval(slide, x, y, w, h, fill, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h))
    rgb(shape.fill, fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.25)
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
        text(slide, "HALO    ·    DRAFT", 0.72, 7.08, 5.5, 0.26, size=11, color=muted, bold=True, tracking=160)
    elif kind == "appendix":
        text(slide, "APPENDIX    ·    DO NOT PROJECT", 0.72, 7.08, 8, 0.26, size=11, color=muted, bold=True, tracking=140)
    text(slide, f"{n:02d}", 11.7, 7.08, 0.9, 0.26, size=11, color=muted, bold=True, align="right")


def label(slide, value, x, y, color, w=8):
    text(slide, value, x, y, w, 0.28, size=13, color=color, bold=True, tracking=180)


def draw_fob(slide, x, y, scale=1.0, body=INK, led=AMBER):
    s = scale
    oval(slide, x + 0.62 * s, y, 1.15 * s, 1.15 * s, body)
    oval(slide, x + 0.86 * s, y + 0.24 * s, 0.67 * s, 0.67 * s, CREAM)
    rect(slide, x + 1.02 * s, y + 1.02 * s, 0.36 * s, 0.28 * s, body, radius=0.4)
    rect(slide, x + 0.42 * s, y + 1.22 * s, 1.55 * s, 2.05 * s, body, radius=0.18)
    oval(slide, x + 0.78 * s, y + 1.62 * s, 0.84 * s, 0.84 * s, led)
    oval(slide, x + 1.02 * s, y + 1.86 * s, 0.36 * s, 0.36 * s, RGBColor(0xFF, 0xE3, 0xA3))
    text(
        slide,
        "HALO",
        x + 0.42 * s,
        y + 2.58 * s,
        1.55 * s,
        0.32 * s,
        size=max(10, int(12 * s)),
        color=IVORY,
        bold=True,
        align="center",
        tracking=160,
    )


def card(slide, x, y, w, h, kicker, title, body, kicker_color=TERR):
    rect(slide, x, y, w, h, WHITE, line=LINE, radius=0.08)
    text(slide, kicker, x + 0.28, y + 0.24, w - 0.5, 0.26, size=12, color=kicker_color, bold=True, tracking=150)
    text(slide, title, x + 0.28, y + 0.54, w - 0.5, 0.9, size=22, color=INK, bold=True, leading=0.95)
    text(slide, body, x + 0.28, y + 1.5, w - 0.56, h - 1.75, size=15, color=MUTED, leading=1.05)


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "Halo — Assignment 5 presentation draft"
    prs.core_properties.subject = "Final project: a keychain that tells you when someone is recording"
    prs.core_properties.category = "Draft"
    prs.core_properties.author = "Session 2 team"

    # ----- 1. fake title -----
    s = add_slide(prs, CREAM)
    label(s, "A SMALL CHANGE OF PLAN", 0.78, 1.35, TERR)
    text(s, "Beside", 0.75, 1.75, 10, 1.35, size=84, color=INK, bold=True, leading=0.9)
    rule(s, 0.8, 3.25, 2.1, TERR, 3.5)
    text(s, "We changed our product.", 0.78, 3.5, 10, 0.6, size=32, color=INK, bold=True)
    text(s, "A mental health connection app.", 0.78, 4.2, 10, 0.5, size=24, color=MUTED)
    text(s, "Five volunteers. Step outside with us for a moment.", 0.78, 6.35, 10, 0.4, size=18, color=INK)
    footer(s, 1, "bit")
    notes(
        s,
        """
Say this straight, like a logistics update. Do not smile like you are about to prank them.

"Quick change before we start. We dropped the old idea. This is Beside. A mental health connection app. We need five volunteers. Leave your stuff. Come outside for ten seconds."

Pick five people who can keep a straight face. Not the professor. Before class, the day before, tell the professor what slides 1–7 are: a staged feeling, and nobody records. If they say no, start on the Halo title and skip the scare. Do not invent a softer version on the spot.

If the class never heard a prior product, drop the sentence "we changed our product" and say: "We want to start with a one-minute exercise. It's called Beside."
""",
    )

    # ----- 2. exercise -----
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
    footer(s, 2, "bit")
    notes(
        s,
        """
Volunteers are already back in their seats, phones face up on the lock screen, doing nothing.

Read the slide, then say: "Beside is the conversation. Phones on the table. Face up is fine. Don't touch them."

If someone will not put a phone down, let them. Do not collect phones. The point dies if it feels like a search.

Give the easier prompt out loud as permission, not as a joke: "How your week went is enough. You do not owe anyone an embarrassing story."

Then click to the prompt slide and start a 75-second timer. Stay at the front. Don't hover over the volunteers. Don't laugh at what you overhear. If the room is silent for ten seconds, repeat: "Two or three people. One true thing. Then we move on."
""",
    )

    # ----- 3. prompt hold -----
    s = add_slide(prs, CREAM)
    label(s, "SIXTY SECONDS", 0.78, 1.85, TERR, w=11)
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
    footer(s, 3, "bit")
    notes(
        s,
        """
This slide stays up. Do not talk over them. Seventy-five seconds is enough. Ninety is too long; people start performing.

Watch faces, not to collect stories, but to see if someone is actually distressed. If they are, end the exercise early: "That's a minute. Phones up, we're good." Then go straight to the clear slide (Nobody recorded you). Skip both black slides.

You are listening only for the energy in the room. You are not collecting material. Do not write down what anyone says. Tell the volunteers the same rule again if you see a notes app open.
""",
    )

    # ----- 4. reveal -----
    s = add_slide(prs, BLACK)
    text(s, "BEFORE WE GO ON", 0.78, 1.9, 10, 0.3, size=13, color=AMBER, bold=True, tracking=180)
    text(s, "The volunteers\nwere recording you.", 0.75, 2.35, 12, 2.5, size=60, color=IVORY, bold=True, leading=0.95)
    footer(s, 4, "bit", dark=True)
    notes(
        s,
        """
Click only after the minute is over. Say nothing for one full second. Then, flat:

"The five people who stepped outside put their phones down so they could record."

Look at the volunteers, not at whoever just shared a story. Do not repeat, paraphrase, or joke about anything that was said. Do not name a person.

If the room already feels bad, skip the next slide.
""",
    )

    # ----- 5. post -----
    s = add_slide(prs, BLACK)
    text(s, "ONE MORE THING", 0.78, 1.9, 10, 0.3, size=13, color=AMBER, bold=True, tracking=180)
    text(s, "We might post\nthe clips.", 0.75, 2.35, 12, 2.5, size=64, color=IVORY, bold=True, leading=0.95)
    footer(s, 5, "bit", dark=True)
    notes(
        s,
        """
One breath. That is the whole slide. Do not add "just kidding" yet. Do not add "or maybe we won't." Do not point at a specific person.

Do not wait for a laugh. A laugh here is at someone's expense.

If anyone looks genuinely upset, do not finish the sentence. Click immediately to the next slide and say the clear line first.

This slide is optional. Cut it if the first black slide already did the job, or if the professor asked you to keep the scare smaller.
""",
    )

    # ----- 6. release -----
    s = add_slide(prs, CREAM)
    label(s, "CLEAR", 0.78, 1.15, GREEN)
    text(s, "Nobody recorded you.", 0.75, 1.6, 12, 0.75, size=44, color=INK, bold=True)
    text(s, "Nothing was posted.", 0.75, 2.4, 12, 0.7, size=44, color=INK, bold=True)
    text(s, "Nothing exists.", 0.75, 3.2, 12, 0.7, size=44, color=INK, bold=True)
    rect(s, 0.78, 4.7, 8.6, 1.15, WHITE, line=LINE, radius=0.1)
    text(s, "Phones up. Lock screen. Camera closed.", 1.05, 4.85, 8.1, 0.4, size=20, color=INK, bold=True)
    text(s, "Show the room. Take your time.", 1.05, 5.32, 8.1, 0.35, size=16, color=MUTED)
    footer(s, 6, "bit")
    notes(
        s,
        """
This slide is not optional. Say it before you say anything clever.

"Nobody recorded you. I need you to see that before anything else. Phones up. Lock screens. There is no clip, no file, nothing to post. I'm sorry for those two seconds."

Volunteers raise phones high enough for the back row. Camera app closed. Voice memos closed. If a volunteer actually recorded, you stop the presentation and delete it in front of the room. That is the deal you made outside.

Do not ask anyone to repeat what they said. One optional question, only if the room has landed: "Hands up if you were about to say something you did not want online." Then move on. Do not comment on who raises a hand.
""",
    )

    # ----- 7. the requirement -----
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
    footer(s, 7, "bit")
    notes(
        s,
        """
Slow down. This is the hinge.

"We told you to put the useful object down and act normal. A normal conversation looks exactly like the last two minutes. The phone on the table could not tell you anything, because you were not looking at it. That is the requirement. Whatever we build has to work in that room."

Then: "Beside was the exercise. Here is the product."
""",
    )

    # ----- 8. real title -----
    s = add_slide(prs, CREAM)
    label(s, "THE ACTUAL PRODUCT", 0.78, 1.45, AMBER_INK)
    text(s, PRODUCT, 0.75, 1.85, 8, 1.15, size=72, color=INK, bold=True)
    text(s, "A keychain that tells you\nwhen someone is recording.", 0.78, 3.25, 8.2, 1.3, size=28, color=INK, leading=1.02)
    rule(s, 0.8, 4.85, 2.1, AMBER, 3.5)
    text(s, "Beside was the demo.", 0.78, 5.15, 7, 0.4, size=18, color=MUTED)
    text(s, "[ Name ]     ·     [ Name ]     ·     [ Name ]", 0.78, 6.35, 8, 0.35, size=14, color=MUTED)
    draw_fob(s, 9.55, 1.7, 1.15)
    footer(s, 8, "pitch")
    notes(
        s,
        """
"This is what we actually brought."

Halo is a working name. If the team hates it, change the word. Keep the behavior: a light and a buzz when capture is live nearby. Other names that fit the same behavior: Tell, Glint, Cue, Knock.

Fill in the three names before you present. Session 2 team, groups of three.

If you skipped the live bit, start here. First sentence: "We want a way to know, in the moment, that someone nearby is recording. The object is a keychain."
""",
    )

    # ----- 9. this room -----
    s = add_slide(prs, CREAM)
    label(s, "THIS ROOM", 0.78, 0.42, AMBER_INK)
    text(s, "Keep the glasses.", 0.75, 0.9, 12, 0.85, size=48, color=INK, bold=True)
    text(
        s,
        "A camera you don't have to hold is a better camera.\nHalo is for the person who didn't press record.",
        0.78,
        1.95,
        11.5,
        1.15,
        size=24,
        color=INK,
        leading=1.08,
    )
    rect(s, 0.78, 3.55, 5.7, 2.85, WHITE, line=LINE, radius=0.08)
    rect(s, 6.7, 3.55, 5.85, 2.85, WHITE, line=LINE, radius=0.08)
    text(s, "WHAT YOU ALREADY THINK", 1.05, 3.78, 5.2, 0.3, size=13, color=AMBER_INK, bold=True, tracking=120)
    text(
        s,
        "Hands free.\nThe shot is from your eyes.\nThe glasses are not the villain.",
        1.05,
        4.25,
        5.1,
        1.8,
        size=22,
        color=INK,
        leading=1.12,
    )
    text(s, "THE OTHER SEAT", 6.98, 3.78, 5.2, 0.3, size=13, color=TERR, bold=True, tracking=120)
    text(
        s,
        "They didn't press it.\nThey may not be looking\nat the frame.",
        6.98,
        4.25,
        5.2,
        1.8,
        size=22,
        color=INK,
        leading=1.12,
    )
    footer(s, 9, "pitch")
    notes(
        s,
        """
This is the win-them-over slide. Do not sneer at Meta, at glasses, or at anyone who likes them.

"You can like the glasses. We do. A camera at eye height that you don't have to fish out of a pocket is a good camera. Halo does not ask anyone to take them off. It is for the other person at the table, the one who did not agree to be the footage."

If someone jumps in with "they already have an LED," say "Yes. Next slide." Don't argue it early.
""",
    )

    # ----- 10. the gap -----
    s = add_slide(prs, CREAM)
    label(s, "THE GAP", 0.78, 0.38, AMBER_INK)
    text(s, "The blink only helps\nif you are looking.", 0.75, 0.78, 12, 1.55, size=40, color=INK, bold=True, leading=0.96)
    rect(s, 0.75, 2.7, 5.85, 3.85, WHITE, line=LINE, radius=0.08)
    rect(s, 6.8, 2.7, 5.8, 3.85, INK, radius=0.08)
    text(s, "GLASSES", 1.05, 2.95, 5.2, 0.3, size=13, color=AMBER_INK, bold=True, tracking=150)
    text(
        s,
        "A white capture LED.\nA blink for a photo.\nOn through a video.\nCover the light, the camera\nis supposed to stop.",
        1.05,
        3.4,
        5.2,
        2.8,
        size=20,
        color=INK,
        leading=1.08,
    )
    text(s, "THE PHONE ON THE TABLE", 7.1, 2.95, 5.2, 0.3, size=13, color=AMBER, bold=True, tracking=120)
    text(
        s,
        "A voice memo has no light.\nFace down looks like manners.\nWe told you not to touch it.\nYou still would not have known.",
        7.1,
        3.45,
        5.2,
        2.6,
        size=20,
        color=IVORY,
        leading=1.08,
    )
    footer(s, 10, "pitch")
    notes(
        s,
        """
Be precise. This room will punish a false claim.

Meta's AI glasses have a white capture LED. It blinks for a photo and stays on through a video. Meta says there is no off switch, and that covering or breaking the LED disables the camera. Cite their privacy page in the report. Do not say "glasses secretly record with no light." That is not the product, and it is not true of these glasses.

"The LED is real, and it is a good idea. It sits on the wearer's frame. You only get it if you happen to be looking there. Our demo did not use glasses. It used phones, face up, doing nothing, and the room still could not tell. A voice memo has no capture LED at all. That is the gap Halo is for."

Sources are on the last appendix slide. Read them before you present, in case the wording changed.
""",
    )

    # ----- 11. spec -----
    s = add_slide(prs, CREAM)
    label(s, "THE DEMO IS THE SPEC", 0.78, 0.4, AMBER_INK)
    text(s, "It has to work in the room\nwe just made.", 0.75, 0.85, 12, 1.4, size=36, color=INK, bold=True, leading=0.98)
    items = [
        ("01", "Phone down", "You are not looking at a screen, because the conversation got real."),
        ("02", "Acting normal", "No scanning people's faces or temples for a tiny light."),
        ("03", "During, not after", "The signal arrives while you can still choose what to say."),
        ("04", "You decide", "Ask, move, or keep talking. The object does not accuse anyone."),
    ]
    for i, (n, title, body) in enumerate(items):
        x = 0.75 + (i % 4) * 3.1
        rect(s, x, 3.55, 2.95, 2.85, WHITE, line=LINE, radius=0.08)
        text(s, n, x + 0.18, 3.72, 2.5, 0.3, size=13, color=AMBER_INK, bold=True, tracking=80)
        text(s, title, x + 0.18, 4.1, 2.6, 0.7, size=18, color=INK, bold=True)
        text(s, body, x + 0.18, 4.85, 2.6, 1.3, size=14, color=MUTED, leading=1.05)
    footer(s, 11, "pitch")
    notes(
        s,
        """
Point back at the exercise once, then stop talking about it.

"Four requirements, all from the last five minutes. If Halo needs you to open an app, it fails the first one. If it needs you to stare at someone's glasses, it fails the second. If it emails you tonight, it fails the third. If it says 'it was Alex,' it fails the fourth."
""",
    )

    # ----- 12. the object -----
    s = add_slide(prs, CREAM)
    label(s, "THE OBJECT", 0.78, 0.4, AMBER_INK)
    text(s, "One light.\nOne buzz.\nOne button.", 0.75, 0.9, 7.2, 2.5, size=44, color=INK, bold=True, leading=0.95)
    text(
        s,
        "About the size of a car key.\nOn the keys you already drop on the table.\nQuiet almost all the time. That is the design.",
        0.78,
        3.7,
        7.3,
        1.4,
        size=20,
        color=INK,
        leading=1.12,
    )
    rect(s, 0.78, 5.3, 7.4, 1.35, WHITE, line=LINE, radius=0.08)
    text(s, "PRESS ONCE", 1.02, 5.48, 3, 0.28, size=12, color=AMBER_INK, bold=True, tracking=120)
    text(s, "Snooze a lecture that's\nbeing recorded on purpose.", 1.02, 5.8, 3.3, 0.7, size=14, color=INK, leading=1.05)
    text(s, "PRESS TWICE", 4.5, 5.48, 3.3, 0.28, size=12, color=AMBER_INK, bold=True, tracking=120)
    text(s, "Say \"I'm live\" when your\nphone can't say it for you.", 4.5, 5.8, 3.4, 0.7, size=14, color=INK, leading=1.05)
    draw_fob(s, 9.7, 1.35, 1.2)
    footer(s, 12, "pitch")
    notes(
        s,
        """
Hold up a placeholder if you have one: cardboard, a key fob, even a taped LED. A physical object does more than this drawing.

"You don't pick it up. You don't unlock it. It lives on the keys that are already out. Once to be quiet through a class that's supposed to be recorded. Twice to admit you are recording, if your phone or your glasses have no beacon yet."

Do not invent a price, a weight in grams, or a battery life. If asked: "We don't have a bill of materials yet. A number before a parts list would be fiction. First prototype is a dev board."
""",
    )

    # ----- 13. why a keychain -----
    s = add_slide(prs, CREAM)
    label(s, "WHY THIS, AND NOT AN APP", 0.78, 0.38, AMBER_INK)
    text(s, "The useful object was\nthe one on the table.", 0.75, 0.82, 12, 1.45, size=36, color=INK, bold=True, leading=0.96)
    rows = [
        ("The phone", "Right object, wrong moment. It was face up and still useless, because looking at it meant leaving the conversation."),
        ("The LED on the frame", "Right idea, wrong direction. It tells the room only if the room is looking at the wearer."),
        ("The keychain", "Already out. Already yours. The signal arrives on your body, which is the one place you are not too busy to notice."),
    ]
    for i, (title, body) in enumerate(rows):
        y = 2.6 + i * 1.35
        text(s, f"0{i+1}", 0.8, y, 0.8, 0.4, size=16, color=AMBER_INK, bold=True)
        text(s, title, 1.8, y - 0.02, 9.5, 0.38, size=22, color=INK, bold=True)
        text(s, body, 1.8, y + 0.42, 10.2, 0.7, size=16, color=MUTED)
    footer(s, 13, "pitch")
    notes(
        s,
        """
"An app fails the demo we just ran. Every phone in the room was already a perfectly good computer, and it still couldn't help, because the social rule of a real conversation is that you put it down. Halo has to be the thing you are allowed to leave out."
""",
    )

    # ----- 14. how it knows -----
    s = add_slide(prs, CREAM)
    label(s, "HOW IT KNOWS", 0.78, 0.36, AMBER_INK)
    text(s, "One promise. Two maybes.", 0.75, 0.75, 12, 0.6, size=32, color=INK, bold=True)
    cols = [
        (AMBER_INK, "BUILD THIS", "I'm live", "Capture turns on a short-range Bluetooth beacon. A few meters. A flag, not a recording. Halo lights."),
        (TERR, "TEST, DON'T PROMISE", "Glint", "A faint infrared blink looks for a lens at desk range. Ordinary glasses can fool it. A prototype question, not the pitch."),
        (MUTED, "IF THE PHONE CAN'T", "The button", "Double-press means the wearer admits it. Nearby Halos light for that stretch, then go dark."),
    ]
    for i, (color, kicker, title, body) in enumerate(cols):
        x = 0.75 + i * 4.1
        rect(s, x, 1.75, 3.9, 4.0, WHITE, line=LINE, radius=0.08)
        text(s, kicker, x + 0.25, 1.98, 3.4, 0.5, size=13, color=color, bold=True, tracking=80)
        text(s, title, x + 0.25, 2.55, 3.4, 0.55, size=26, color=INK, bold=True)
        text(s, body, x + 0.25, 3.3, 3.4, 2.1, size=16, color=MUTED, leading=1.08)
    text(
        s,
        "A silent mic in a pocket is a miss. We will say that before anyone else does.",
        0.78,
        6.0,
        11.5,
        0.4,
        size=16,
        color=INK,
        bold=True,
    )
    footer(s, 14, "pitch")
    notes(
        s,
        """
Do not demo a fake detection and call it real. If the fob lights in the room, say which of the three caused it.

"The product we will defend is the beacon. Your phone, or your glasses if they can expose capture state, announces 'on' for a few meters. No audio rides along. No name. Halo is a receiver you can feel."

"We looked at a glint sensor because camera lenses reflect infrared differently than cloth. At a desk it sometimes works. Eyeglasses and watch crystals set it off. If the false alarms are constant, we kill it. It is not on the poster."

"And the hole: we cannot reliably hear a voice memo that does not want to be found. A product that pretends it can will accuse the wrong person. So we don't. The report leads with that limit."

If they ask about Meta's API: "We don't know of a public capture-state beacon. Until one exists, a glasses wearer uses the button, or a phone shortcut. They opt in. That's the feature we want them to like."
""",
    )

    # ----- 15. refusals -----
    s = add_slide(prs, CREAM)
    label(s, "WHAT IT REFUSES TO DO", 0.78, 0.4, AMBER_INK)
    text(s, "A warning, not a verdict.", 0.75, 0.85, 12, 0.7, size=36, color=INK, bold=True)
    refusals = [
        ("No recording", "Halo does not store audio, video, or a transcript of the room."),
        ("No names", "The light means nearby and right now. It does not mean who."),
        ("No bypass", "It does not cover, disable, or work around a capture LED."),
        ("No proof", "Dark does not mean safe. It means no willing signal, and no glint."),
    ]
    for i, (title, body) in enumerate(refusals):
        y = 1.9 + (i % 4) * 1.15
        text(s, title, 0.8, y, 3.4, 0.4, size=22, color=INK, bold=True)
        text(s, body, 4.4, y + 0.02, 8, 0.7, size=18, color=MUTED)
    footer(s, 15, "pitch")
    notes(
        s,
        """
Read the four refusals. They are the ethical product, not the fine print.

"If Halo ever tells you a classmate's name, we built the wrong thing. The scary version of this product is a detector that lets you accuse someone. The version we want is a light the willing devices agree to send."
""",
    )

    # ----- 16. win the glasses -----
    s = add_slide(prs, CREAM)
    label(s, "FOR THE PEOPLE WEARING THEM", 0.78, 0.38, AMBER_INK)
    text(s, "Make the willing ones\nobvious.", 0.75, 0.82, 12, 1.5, size=40, color=INK, bold=True, leading=0.96)
    steps = [
        ("1", "Capture starts.", "Camera or voice memo opens. Glasses begin a clip."),
        ("2", "The device admits it.", "A beacon, or the double-press. Same color on every Halo at the table."),
        ("3", "Covert looks different.", "A phone in someone's hand, and a dark keychain, is a question you can ask out loud."),
    ]
    for i, (n, title, body) in enumerate(steps):
        x = 0.75 + i * 4.1
        oval(s, x, 2.7, 0.48, 0.48, INK)
        text(s, n, x, 2.76, 0.48, 0.38, size=16, color=IVORY, bold=True, align="center")
        text(s, title, x, 3.35, 3.8, 0.7, size=22, color=INK, bold=True)
        text(s, body, x, 4.15, 3.7, 1.3, size=16, color=MUTED, leading=1.08)
    text(
        s,
        "You keep the glasses. The rest of the table gets the blink without staring at the frame.",
        0.78,
        5.85,
        11.6,
        0.55,
        size=18,
        color=INK,
        bold=True,
    )
    footer(s, 16, "pitch")
    notes(
        s,
        """
Land this slowly. It is the offer.

"If you wear the glasses, you already accepted a light. We are not adding a second lecture. We are moving the information you already agreed to show onto the keychains of the people who are looking at you, not at your temple."

"The social effect we actually want: recording that is willing looks normal, because the table lights up together. Recording that is hidden is the one that looks strange. Halo does not catch the hidden one. It makes the honest one legible."

Say the question people are allowed to ask: "Are you recording?" The product's job is to make that question ordinary, not to answer it with a name.
""",
    )

    # ----- 17. three moments -----
    s = add_slide(prs, CREAM)
    label(s, "THREE MOMENTS", 0.78, 0.38, AMBER_INK)
    text(s, "Most minutes, it does nothing.", 0.75, 0.8, 12, 0.6, size=32, color=INK, bold=True)
    moments = [
        ("Monday", "Seminar", "Someone's glasses are live for a photo of the board. One tap. You see them hold the moment up. Back to your notes."),
        ("Thursday", "Group project", "Phones are down. No beacon. Halo stays dark. You say the messy version of the week."),
        ("Saturday", "A party", "A glint keeps returning, if that sensor exists. You don't accuse anyone. You turn your chair, or you ask."),
    ]
    for i, (day, place, body) in enumerate(moments):
        y = 1.75 + i * 1.6
        rect(s, 0.75, y, 11.85, 1.45, WHITE, line=LINE, radius=0.08)
        text(s, day, 1.0, y + 0.28, 2.3, 0.35, size=14, color=AMBER_INK, bold=True, tracking=80)
        text(s, place, 1.0, y + 0.68, 2.4, 0.45, size=20, color=INK, bold=True)
        text(s, body, 3.6, y + 0.35, 8.6, 0.85, size=18, color=INK, leading=1.05)
    footer(s, 17, "pitch")
    notes(
        s,
        """
Optional if you are long. Cut this before you cut the gap, the refusals, or I'm live.

The middle row is the product working by staying quiet. Say that: "Thursday is the success case we care about. A detector that buzzes all day is just anxiety with a battery."
""",
    )

    # ----- 18. tests -----
    s = add_slide(prs, CREAM)
    label(s, "BEFORE WE WRITE THE REPORT", 0.78, 0.38, AMBER_INK)
    text(s, "Four tests. One of them\ncan kill the idea.", 0.75, 0.82, 12, 1.4, size=36, color=INK, bold=True, leading=0.96)
    tests = [
        ("01", "Notice", "Can someone feel one buzz mid-sentence, without looking down?"),
        ("02", "Distance", "Do four beacons light a fob across this table, and stay dark across the room?"),
        ("03", "Glint", "How fast do normal glasses false-alarm it? Constant means we drop the sensor."),
        ("04", "Today", "Did this scare make you want Halo, or just make you angry?"),
    ]
    for i, (n, title, body) in enumerate(tests):
        col = i % 2
        row = i // 2
        x = 0.75 + col * 6.3
        y = 2.6 + row * 2.0
        text(s, n, x, y, 1.0, 0.4, size=16, color=AMBER_INK, bold=True)
        text(s, title, x + 1.05, y - 0.02, 4.8, 0.4, size=22, color=INK, bold=True)
        text(s, body, x + 1.05, y + 0.5, 4.9, 1.1, size=16, color=MUTED, leading=1.05)
    footer(s, 18, "pitch")
    notes(
        s,
        """
Spend time on 04. It is the slide that makes the exercise legitimate.

"We are not going to count your faces today as user research. You were startled on purpose. After class, on paper, one question: do you want a signal like this, or did we only wind you up? If the answer is the second, the report says so. We would rather lose the product than write up a flinch as demand."

Ask the professor if a one-question slip after class is appropriate. Do not collect stories from the exercise. Do not ask for names.
""",
    )

    # ----- 19. risks -----
    s = add_slide(prs, CREAM)
    label(s, "SAID OUT LOUD", 0.78, 0.4, AMBER_INK)
    text(s, "The ways this goes wrong.", 0.75, 0.85, 12, 0.6, size=32, color=INK, bold=True)
    risks = [
        ("The stunt is not evidence.", "It produces a feeling once. The paper after class is the evidence."),
        ("A false accusation is worse than no product.", "So Halo never names a person, and a dark fob is not proof of safety."),
        ("Anxiety is a broken feature.", "Snooze has to be faster than the buzz is annoying, or people will take it off the keys."),
        ("The prompt was a false premise.", "The next sentence had to be that nothing exists. The professor hears the plan first. Next time, if there is a next time, the prompt is only 'how your week went.'"),
    ]
    for i, (title, body) in enumerate(risks):
        y = 1.75 + i * 1.2
        rule(s, 0.8, y, 0.45, AMBER, 3)
        text(s, title, 1.5, y - 0.18, 10.8, 0.38, size=18, color=INK, bold=True)
        text(s, body, 1.5, y + 0.24, 10.8, 0.6, size=15, color=MUTED)
    footer(s, 19, "pitch")
    notes(
        s,
        """
Volunteer this before they ask. It is worth more than a polished demo.

If the room is still annoyed about the exercise, stay on this slide and take it. Do not flee into features.
""",
    )

    # ----- 20. close -----
    s = add_slide(prs, CREAM)
    oval(s, 0.85, 2.15, 0.7, 0.7, AMBER)
    oval(s, 1.08, 2.38, 0.24, 0.24, RGBColor(0xFF, 0xE3, 0xA3))
    text(s, PRODUCT.upper(), 1.85, 2.25, 6, 0.55, size=18, color=AMBER_INK, bold=True, tracking=200, anchor="middle")
    text(s, "Know when someone\nis recording.", 0.78, 3.15, 10, 1.6, size=44, color=INK, bold=True, leading=0.96)
    text(s, "Before the sentence, not after.", 0.8, 5.0, 10, 0.45, size=22, color=INK)
    text(s, "Questions.", 0.8, 6.15, 4, 0.4, size=18, color=MUTED)
    footer(s, 20, "pitch")
    notes(
        s,
        """
Stop. Don't summarize the whole deck again.

"You already felt the second. Halo is that second, earlier, on your keys. Questions."

If the room is cold, you can add one line: "And if the answer is that the exercise was not worth it, we want that on the record."

Then be quiet.
""",
    )

    # ----- 21. appendix divider -----
    s = add_slide(prs, INK)
    text(s, "APPENDIX", 0.78, 2.3, 12, 0.4, size=14, color=AMBER, bold=True, tracking=200)
    text(s, "Do not project\nthe rest.", 0.75, 2.75, 12, 1.8, size=52, color=IVORY, bold=True, leading=0.96)
    text(s, "Run of show, hallway script, repairs, report, sources.", 0.8, 5.0, 11, 0.4, size=18, color=RGBColor(0xC8, 0xC0, 0xB4))
    footer(s, 21, "appendix", dark=True)
    notes(
        s,
        """
Stop sharing the screen here if you are presenting from this file. Everything after this slide is for the three of you.
""",
    )

    # ----- 22. run of show -----
    s = add_slide(prs, CREAM)
    label(s, "RUN OF SHOW", 0.72, 0.32, AMBER_INK)
    text(s, "About nine minutes. The scare is not the grade.", 0.72, 0.68, 12, 0.4, size=20, color=INK, bold=True)
    rows = [
        ("0:00", "Beside", "Ask for five volunteers. Straight face."),
        ("0:30", "Hallway", "One of you reads the script outside. They sit back down."),
        ("1:15", "Phones down", "Groups form. Permission to share something ordinary."),
        ("1:45", "Prompt", "75 seconds. You stay quiet. Watch for distress, not for stories."),
        ("3:00", "Black slides", "One second of silence. Skip the second slide if the room is already shaky."),
        ("3:15", "Clear", "Phones up before any joke. Nothing exists."),
        ("3:40", "The requirement", "Phone on the table, acting normal, still didn't know."),
        ("4:00", "Halo through close", "Gap, spec, object, beacon, refusals. Cut moments and tests if long."),
        ("9:00", "Questions", "Lead with the limit: we cannot catch a silent mic."),
    ]
    for i, (t, name, detail) in enumerate(rows):
        y = 1.2 + i * 0.58
        text(s, t, 0.72, y, 1.15, 0.4, size=14, color=AMBER_INK, bold=True)
        text(s, name, 1.95, y, 2.5, 0.4, size=15, color=INK, bold=True)
        text(s, detail, 4.5, y, 8.1, 0.45, size=15, color=MUTED)
    footer(s, 22, "appendix")
    notes(s, "If the professor caps you at five minutes, do Beside through Clear, then the gap, the object, and I'm live. Sit down.")

    # ----- 23. hallway -----
    s = add_slide(prs, CREAM)
    label(s, "HALLWAY  ·  READ IT, DON'T IMPROVISE", 0.72, 0.32, TERR)
    text(s, "Nobody outside is recording anything.", 0.72, 0.72, 12, 0.45, size=24, color=INK, bold=True)
    script = [
        "Walk back in separately. Sit down.",
        "Phone face up, on the lock screen. Don't touch it.",
        "Do not open the camera. Do not open voice memos. Do not take notes.",
        "Look ordinary. If you smirk, the exercise dies.",
        "When we say phones up, show the lock screen, camera closed.",
        "If anyone in the room looks actually upset, don't wait. Phones up first.",
    ]
    for i, line in enumerate(script):
        y = 1.5 + i * 0.78
        oval(s, 0.78, y + 0.04, 0.42, 0.42, INK)
        text(s, str(i + 1), 0.78, y + 0.08, 0.42, 0.34, size=14, color=IVORY, bold=True, align="center")
        text(s, line, 1.45, y + 0.05, 10.8, 0.5, size=20, color=INK)
    footer(s, 23, "appendix")
    notes(
        s,
        """
Screenshot this slide onto the phone of whoever walks them out, so it is not on the projector.

Add, out loud: "If one of you hits record as a joke, we stop the class and delete it in front of everyone. That is the whole job. You are acting, not capturing."
""",
    )

    # ----- 24. lines -----
    s = add_slide(prs, CREAM)
    label(s, "LINES", 0.75, 0.36, AMBER_INK)
    text(s, "Say these. Don't decorate them.", 0.72, 0.75, 12, 0.45, size=26, color=INK, bold=True)
    left = [
        ("Open", "We changed our product. We need five volunteers outside."),
        ("Exercise", "How your week went is enough. You don't owe an embarrassing story."),
        ("Reveal", "The volunteers were recording you."),
        ("Clear", "Nobody recorded you. Nothing exists. Phones up."),
    ]
    right = [
        ("Hinge", "Your phone was on the table. You still would not have known."),
        ("Glasses", "Keep them. The LED is real. It only helps if you are looking."),
        ("Limit", "We cannot catch a silent mic. We will not pretend we can."),
        ("Close", "Know when someone is recording. Before the sentence, not after."),
    ]
    for i, (k, v) in enumerate(left):
        y = 1.5 + i * 1.25
        text(s, k.upper(), 0.75, y, 5.5, 0.28, size=12, color=AMBER_INK, bold=True, tracking=120)
        text(s, v, 0.75, y + 0.32, 5.6, 0.75, size=16, color=INK)
    for i, (k, v) in enumerate(right):
        y = 1.5 + i * 1.25
        text(s, k.upper(), 7.0, y, 5.6, 0.28, size=12, color=TERR, bold=True, tracking=120)
        text(s, v, 7.0, y + 0.32, 5.6, 0.75, size=16, color=INK)
    footer(s, 24, "appendix")
    notes(s, "If you forget everything else, say the Clear line and the Limit line. Those two protect the grade and the room.")

    # ----- 25. if it breaks -----
    s = add_slide(prs, CREAM)
    label(s, "IF IT BREAKS", 0.75, 0.36, TERR)
    text(s, "Leave the bit. Keep the product.", 0.72, 0.75, 12, 0.45, size=26, color=INK, bold=True)
    cases = [
        ("Someone won't share", "Say: then talk about lunch. Beside doesn't get to demand a confession. Move on."),
        ("Someone is upset", "Clear slide, immediately. Skip the rest of the scare. Let them step out. Talk after class, not from the front."),
        ("A volunteer actually recorded", "Stop. Delete it in front of the room. Tell the professor. Do not continue the pitch that day."),
        ("The professor hates it", "You still have slides 8 through 20. Start at Halo. The product does not need the scare to make sense."),
        ("They say glasses already blink", "Agree. Go to the gap slide. Phones and voice memos are the hole. The LED faces the wrong way for a real conversation."),
        ("They ask for a price or a market", "We don't have a parts list yet. A price before that is fiction. Campus, one table, is the only market we claim."),
    ]
    for i, (title, body) in enumerate(cases):
        col = i % 2
        row = i // 2
        x = 0.72 + col * 6.3
        y = 1.45 + row * 1.75
        text(s, title, x, y, 6.0, 0.4, size=16, color=INK, bold=True)
        text(s, body, x, y + 0.42, 6.0, 1.05, size=14, color=MUTED, leading=1.05)
    footer(s, 25, "appendix")
    notes(s, "The third row is a hard stop, not a judgment call.")

    # ----- 26. report -----
    s = add_slide(prs, CREAM)
    label(s, "WRITTEN REPORT  ·  15 POINTS", 0.75, 0.32, AMBER_INK)
    text(s, "Due Sunday, May 17, 2026.", 0.72, 0.68, 12, 0.4, size=26, color=INK, bold=True)
    sections = [
        ("1", "The scene", "What the room was, including that several people like recording glasses."),
        ("2", "The exercise", "What you staged, what you refused to record, and how the room actually reacted."),
        ("3", "The requirement", "Phone down, acting normal, signal during the conversation, no accusation."),
        ("4", "The product", "Keychain, light, buzz, snooze, double-press. Working name and why."),
        ("5", "What is real", "The beacon. Range of a few meters. A flag, not a clip."),
        ("6", "What is a test", "Glint. False alarms from ordinary glasses. Kill condition."),
        ("7", "What you will not claim", "Silent mics. Names. Bypassing a capture LED. A price. A market size."),
        ("8", "The glasses offer", "Willing capture becomes the normal-looking case."),
        ("9", "Evidence", "The after-class question, separate from the flinch. Quotes only with permission."),
        ("10", "Team", "Who built, who spoke, what you would prototype next."),
    ]
    for i, (n, title, body) in enumerate(sections):
        col = i // 5
        row = i % 5
        x = 0.72 + col * 6.3
        y = 1.3 + row * 1.05
        text(s, n, x, y, 0.45, 0.3, size=14, color=AMBER_INK, bold=True)
        text(s, title, x + 0.5, y, 5.5, 0.3, size=15, color=INK, bold=True)
        text(s, body, x + 0.5, y + 0.32, 5.5, 0.55, size=13, color=MUTED)
    footer(s, 26, "appendix")
    notes(
        s,
        """
Syllabus language, copied from the assignment page:

Presentation in the last session, 2026-05-11, 10 points.
Written materials due Sunday 2026-05-17, 15 points.
The upload box also says due Friday by 5:10pm, 10 points, file upload. Confirm on the course page which Friday that is, and don't upload the report into the slides slot.

The details were going to be discussed in class. If that discussion added requirements, they win over this outline.
""",
    )

    # ----- 27. blanks -----
    s = add_slide(prs, CREAM)
    label(s, "FILL IN BEFORE YOU PRESENT", 0.75, 0.36, TERR)
    blanks = [
        ("Names", "Three names on the Halo title. Speaker A, B, and C below."),
        ("The professor", "Tell them the day before. The black slides are a feeling. Nobody records. If they veto it, start at slide 8."),
        ("A prop", "Cardboard fob, or a real keychain with a dot of amber tape. Hold it up at slide 12."),
        ("The beacon, honestly", "If you have not built one, do not flicker an LED and call it Bluetooth. Say 'this is the behavior.'"),
        ("The survey line", "One question after class, on paper, unsigned unless they want credit: want this, or just startled?"),
        ("The name", "Halo is a placeholder. Pick it or replace it everywhere. The drawing has the word on it."),
        ("Citations", "Read the two Meta pages on the sources slide the morning of. Quote the LED, don't paraphrase from memory."),
        ("Friday upload", "Confirm whether 5:10pm Friday is this file. Export PDF as a backup in case the room's computer hates pptx fonts."),
    ]
    for i, (title, body) in enumerate(blanks):
        col = i % 2
        row = i // 2
        x = 0.72 + col * 6.3
        y = 1.05 + row * 1.4
        text(s, title, x, y, 6.0, 0.32, size=16, color=INK, bold=True)
        text(s, body, x, y + 0.36, 6.0, 0.85, size=14, color=MUTED, leading=1.02)
    footer(s, 27, "appendix")
    notes(s, "A is the open and the hallway. B is the only person who touches the black slides and the clear slide. C takes Halo through the close. All three answer questions.")

    # ----- 28. speakers -----
    s = add_slide(prs, CREAM)
    label(s, "WHO SPEAKS", 0.75, 0.38, AMBER_INK)
    text(s, "One person owns the scare.\nThey also own the apology.", 0.72, 0.8, 12, 1.2, size=28, color=INK, bold=True, leading=1.0)
    roles = [
        ("A", "The setup", "Beside, the volunteers, the hallway, phones down. Ends when the timer starts."),
        ("B", "The two seconds", "Both black slides and the clear slide. Calm voice. No jokes. If this person freezes, A reads the clear line."),
        ("C", "The product", "From the requirement slide through questions. Does not re-tell the stories."),
    ]
    for i, (n, title, body) in enumerate(roles):
        x = 0.75 + i * 4.1
        rect(s, x, 2.5, 3.9, 3.3, WHITE, line=LINE, radius=0.08)
        text(s, n, x + 0.25, 2.7, 3.4, 0.5, size=28, color=AMBER_INK, bold=True)
        text(s, title, x + 0.25, 3.3, 3.4, 0.45, size=20, color=INK, bold=True)
        text(s, body, x + 0.25, 3.9, 3.4, 1.5, size=15, color=MUTED, leading=1.05)
    footer(s, 28, "appendix")
    notes(s, "B should rehearse the clear line until it sounds like relief, not like a punchline. Practice the handoff: B says 'that is the requirement' and C starts.")

    # ----- 29. q and a -----
    s = add_slide(prs, CREAM)
    label(s, "IF THEY ASK", 0.75, 0.32, AMBER_INK)
    qas = [
        ("Glasses already have an LED.", "Yes. It sits on the frame. We used phones. A voice memo has no LED, and you only see the blink if you look at the temple."),
        ("Can you detect a hidden mic?", "No. The beacon is opt-in. Glint looks for lenses, misses mics, and false-alarms. Dark is not proof."),
        ("Then it's just an app.", "The phone can send the flag. You feel it on the keys, because the demo put every phone on the table."),
        ("What about people who don't opt in?", "Halo stays dark. We will not fake a catch. The aim is a room where willing capture is the one that looks normal."),
    ]
    for i, (q, a) in enumerate(qas):
        y = 0.85 + i * 1.45
        text(s, q, 0.75, y, 12, 0.35, size=18, color=INK, bold=True)
        text(s, a, 0.75, y + 0.4, 11.8, 0.8, size=16, color=MUTED)
    footer(s, 29, "appendix")
    notes(
        s,
        """
More answers, if you need them:

Privacy of the beacon itself: it says capture is on. It does not send a name, audio, or a photo. Short range. Off when capture is off. Snooze is local.

Cost: no bill of materials yet. First prototype is a dev board and a battery. We will not invent a $29 price.

Did you manipulate the class? Yes. The point was a feeling, and a feeling is not data. Nothing was recorded. If they hated it, that goes in the writeup.

Is this anti-glasses? No. The offer is that glasses wearers keep the camera and the rest of the table gets a signal as clear as the one they already accepted.

What if two tables are close? That's test 02. If the beacon reaches the next group, we turn the power down until it doesn't.

What about a lecture being recorded on purpose? One press, snooze for the period. A product that buzzes for eighty minutes comes off the keyring by week two.
""",
    )

    # ----- 30. sources -----
    s = add_slide(prs, CREAM)
    label(s, "SOURCES FOR THE LED CLAIM", 0.75, 0.38, AMBER_INK)
    text(s, "Read them the morning you present.", 0.72, 0.8, 12, 0.4, size=24, color=INK, bold=True)
    text(
        s,
        "Meta publishes a capture LED on its AI glasses. It blinks for a photo\nand stays on through a video. Meta says the light has no off switch,\nand that covering or destroying it disables the camera.",
        0.75,
        1.5,
        12,
        1.3,
        size=18,
        color=INK,
        leading=1.08,
    )
    rect(s, 0.75, 3.15, 11.85, 1.35, WHITE, line=LINE, radius=0.08)
    text(s, "META PRIVACY PAGE", 1.0, 3.32, 11, 0.3, size=12, color=AMBER_INK, bold=True, tracking=120)
    text(s, "https://www.meta.com/ai-glasses/privacy/", 1.0, 3.7, 11, 0.45, size=18, color=INK)
    rect(s, 0.75, 4.7, 11.85, 1.35, WHITE, line=LINE, radius=0.08)
    text(s, "META NEWSROOM, JULY 2026", 1.0, 4.88, 11, 0.3, size=12, color=AMBER_INK, bold=True, tracking=120)
    text(s, "https://about.fb.com/news/2026/07/metas-ai-glasses-your-questions-answered/", 1.0, 5.25, 11.2, 0.5, size=16, color=INK)
    text(
        s,
        "If a detail has changed by presentation day, their page wins and this slide loses.",
        0.78,
        6.25,
        11.5,
        0.4,
        size=15,
        color=MUTED,
    )
    footer(s, 30, "appendix")
    notes(
        s,
        """
Do not cite this from memory if someone challenges you. Open the page.

The July 2026 newsroom post is the clearer FAQ: white capture LED, blinks for a photo, continues through video, no off switch, camera disables if the LED is covered or tampered with. The product claim in our deck is narrower than Meta's claim: even a real LED only helps the person who is looking at it, and a phone recording audio has no equivalent light.

We are not claiming Halo detects tampering, and we are not describing how to tamper with anything.
""",
    )

    out = "presentation/Halo-Assignment5-DRAFT.pptx"
    prs.save(out)
    print(f"saved {out} slides={len(prs.slides)}")


if __name__ == "__main__":
    build()
