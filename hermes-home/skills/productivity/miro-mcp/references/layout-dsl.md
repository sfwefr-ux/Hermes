# Layout DSL Reference (from layout_get_dsl)

## Coordinate Systems

**Board-level items (no parent=):**
- Center of board is (0, 0). x → right, y → down.

**Frame children (parent=FRAME):**
- (0, 0) = top-left corner of the frame.
- x, y mark the CENTER of the child item.
- Must fit: 0 <= x <= frame_w, 0 <= y <= frame_h.

**DOC and TABLE (special):**
- x, y = TOP-LEFT corner in all coordinate systems (not center!)

## Single-line Items

```
id TYPE [parent=REF] key=value... "content"
```

### FRAME
```
f1 FRAME x=0 y=0 w=1200 h=900 fill=#F5F5F5 "My Frame"
```

### STICKY
```
s1 STICKY parent=f1 x=200 y=200 w=200 color=yellow shape=rectangle "<p>Line 1</p><p>Line 2</p>"
```
Colors: gray, light_yellow, yellow, orange, light_green, green, dark_green, cyan, light_pink, pink, violet, red, light_blue, blue, dark_blue, black

### SHAPE
```
sh1 SHAPE parent=f1 x=400 y=400 w=180 h=80 type=rectangle fill=#23C27F color=#FFFFFF font=open_sans size=18 valign=middle "Label"
```
Types: rectangle, round_rectangle, circle, triangle, rhombus, parallelogram, trapezoid, pentagon, hexagon, octagon, star, cross, cloud, can, left_arrow, right_arrow, left_right_arrow, left_brace, right_brace, wedge_round_rectangle_callout, flow_chart_predefined_process

### TEXT
```
t1 TEXT parent=f1 x=400 y=50 w=600 font=open_sans size=24 align=center color=#333333 "Title"
```

### CARD
```
c1 CARD parent=f1 x=200 y=400 w=320 h=200 theme=#FF0000 desc="Details here" "Card Title"
```

## Block Items (heredoc)

### DOC
```
d1 DOC x=0 y=500 <<<
# Markdown Title

**Bold** and *italic* text.

- List item 1
- List item 2
>>>
```
Width: fixed 800px. Height: auto-grows with content.

### TABLE
```
tb1 TABLE x=0 y=1200 "Table Title" <<<
Task:text | Owner:text | Status:select(To Do#FF0000, In Progress#FFA500, Done#00FF00)
---
Design API | Alice | To Do
Implement auth | Bob | In Progress
>>>
```
Column types: `text`, `select(Display#RRGGBB, ...)`, `latest_update` (read-only)

Row IDs (on read-back): `[rowId] value1 | value2 | value3`

## HTML in Content

Use HTML tags for rich text in STICKY/SHAPE/TEXT/CARD:
- Multi-paragraph: `"<p>First</p><p>Second</p>"`
- Links: `"<p>See <a href=\"https://example.com\">docs</a></p>"`
