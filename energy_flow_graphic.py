import xml.etree.ElementTree as ET

def text(svg, x, y, content, color, size=24, anchor="start"):
    """Add text element to SVG.
    
    Args:
        svg: SVG element to add text to.
        x (float): X coordinate of text.
        y (float): Y coordinate of text.
        content (str): Text content to display.
        color (str): Text color in hex or color name.
        size (int, optional): Font size in pixels. Defaults to 24.
        anchor (str, optional): Text anchor position. Defaults to "start".
    """
    t = ET.SubElement(
        svg,
        "text",
        {
            "x": str(x),
            "y": str(y),
            "fill": color,
            "font-size": str(size),
            "font-family": "Arial, sans-serif",
            "text-anchor": anchor,
        },
    )
    t.text = content


# ------------------------------------------------------------------
# Icons
# ------------------------------------------------------------------


def draw_icon_circle(svg, cx, cy, color, r=55):
    """Draw a circular background for an icon.
    
    Args:
        svg: SVG element to add circle to.
        cx (float): Center X coordinate.
        cy (float): Center Y coordinate.
        color (str): Fill color in hex or color name.
        r (float, optional): Circle radius. Defaults to 55.
    """
    ET.SubElement(
        svg,
        "circle",
        {
            "cx": str(cx),
            "cy": str(cy),
            "r": str(r),
            "fill": color,
        },
    )


def create_icon_group(svg, cx, cy):
    """Create a transformed group element for positioning icon content.
    
    Args:
        svg: SVG element to add group to.
        cx (float): Group center X coordinate.
        cy (float): Group center Y coordinate.
    
    Returns:
        Element: The created group element.
    """
    return ET.SubElement(
        svg,
        "g",
        {
            "transform": f"translate({cx},{cy})",
            "stroke": "white",
            "fill": "none",
            "stroke-width": "2.5",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
        },
    )

# PV icon background
def draw_pv_icon(svg, cx, cy, color, radius):
    """Draw a photovoltaic system icon with house and sun.
    
    Args:
        svg: SVG element to add icon to.
        cx (float): Icon center X coordinate.
        cy (float): Icon center Y coordinate.
        color (str): Background circle color in hex or color name.
        radius (float): Background circle radius.
    """
    draw_icon_circle(svg, cx, cy, color, radius)

    icon = create_icon_group(svg, cx, cy)

    # --------------------
    # Smaller house
    # --------------------

    # House body
    ET.SubElement(
        icon,
        "path",
        {
            "d": (
                "M -22 -3 "
                "L -22 28 "
                "L 22 28 "
                "L 22 -3"
            )
        },
    )

    # Outer roof
    ET.SubElement(
        icon,
        "path",
        {
            "d": (
                "M -30 -3 "
                "L 0 -34 "
                "L 30 -3"
            )
        },
    )

    # Inner roof
    ET.SubElement(
        icon,
        "path",
        {
            "d": (
                "M -24 -3 "
                "L 0 -28 "
                "L 24 -3"
            )
        },
    )

    # --------------------
    # Sun
    # --------------------

    SUN_X = -25
    SUN_Y = -30
    SUN_R = 4
    RAY_INNER = 7
    RAY_OUTER = 13

    # Sun center
    ET.SubElement(
        icon,
        "circle",
        {
            "cx": str(SUN_X),
            "cy": str(SUN_Y),
            "r": str(SUN_R),
        },
    )

    # Rays (N, S, W, E, NW, NE, SW, SE)
    ray_vectors = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
        (-0.707, -0.707),
        (0.707, -0.707),
        (-0.707, 0.707),
        (0.707, 0.707),
    ]

    for dx, dy in ray_vectors:
        ET.SubElement(
            icon,
            "line",
            {
                "x1": str(SUN_X + dx * RAY_INNER),
                "y1": str(SUN_Y + dy * RAY_INNER),
                "x2": str(SUN_X + dx * RAY_OUTER),
                "y2": str(SUN_Y + dy * RAY_OUTER),
            },
        )


# Load icon
def draw_load_icon(svg, cx, cy, color, radius):
    """Draw an electrical load (outlet) icon.
    
    Args:
        svg: SVG element to add icon to.
        cx (float): Icon center X coordinate.
        cy (float): Icon center Y coordinate.
        color (str): Background circle color in hex or color name.
        radius (float): Background circle radius.
    """
    draw_icon_circle(svg, cx, cy, color, radius)

    icon = create_icon_group(svg, cx, cy)

    # Outer rounded square
    ET.SubElement(
        icon,
        "rect",
        {
            "x": "-32",
            "y": "-32",
            "width": "64",
            "height": "64",
            "rx": "10",
        },
    )

    # Inner frame
    ET.SubElement(
        icon,
        "rect",
        {
            "x": "-20",
            "y": "-20",
            "width": "40",
            "height": "40",
            "rx": "8",
        },
    )

    # Socket face
    ET.SubElement(
        icon,
        "circle",
        {
            "cx": "0",
            "cy": "0",
            "r": "14",
        },
    )

    # Contact holes
    for x in (-5, 5):
        ET.SubElement(
            icon,
            "circle",
            {
                "cx": str(x),
                "cy": "-1",
                "r": "2.2",
                "fill": "white",
                "stroke": "none",
            },
        )

    CLIP_Y1 = -5
    CLIP_Y2 = 5
    CLIP_X = 10

    # Left clip
    ET.SubElement(
        icon,
        "line",
        {
            "x1": str(-CLIP_X),
            "y1": str(CLIP_Y1),
            "x2": str(-CLIP_X),
            "y2": str(CLIP_Y2),
            "stroke": "white",
            "stroke-width": "2.5",
            "stroke-linecap": "round",
        },
    )

    # Right clip
    ET.SubElement(
        icon,
        "line",
        {
            "x1": str(CLIP_X),
            "y1": str(CLIP_Y1),
            "x2": str(CLIP_X),
            "y2": str(CLIP_Y2),
            "stroke": "white",
            "stroke-width": "2.5",
            "stroke-linecap": "round",
        },
    )


# Battery icon
def draw_battery_cell(parent, x, y, color, 
                      width=52,
                      height=16,
                      terminal_w=5,
                      terminal_h=6):
    """
    Draw a single battery cell centered at (x, y).
    """

    # Body
    ET.SubElement(
        parent,
        "rect",
        {
            "x": str(x - width / 2),
            "y": str(y - height / 2),
            "width": str(width),
            "height": str(height),
            "rx": "2",
            "fill": "white",
            "stroke": "white",
        },
    )

    # Positive terminal ("bulb")
    ET.SubElement(
        parent,
        "rect",
        {
            "x": str(x + width / 2),
            "y": str(y - terminal_h / 2),
            "width": str(terminal_w),
            "height": str(terminal_h),
            "fill": "white",
            "stroke": "white",
        },
    )

    # Minus sign (left)
    ET.SubElement(
        parent,
        "line",
        {
            "x1": str(x - 18),
            "y1": str(y),
            "x2": str(x - 10),
            "y2": str(y),
            "stroke": color,
            "stroke-width": "2.5",
        },
    )

    # Plus sign (right)
    ET.SubElement(
        parent,
        "line",
        {
            "x1": str(x + 10),
            "y1": str(y),
            "x2": str(x + 18),
            "y2": str(y),
            "stroke": color,
            "stroke-width": "2.5",
        },
    )

    ET.SubElement(
        parent,
        "line",
        {
            "x1": str(x + 14),
            "y1": str(y - 4),
            "x2": str(x + 14),
            "y2": str(y + 4),
            "stroke": color,
            "stroke-width": "2.5",
        },
    )

def draw_battery_icon(svg, cx, cy, color, radius):
    """Draw a battery storage icon with two cells.
    
    Args:
        svg: SVG element to add icon to.
        cx (float): Icon center X coordinate.
        cy (float): Icon center Y coordinate.
        color (str): Background circle and battery color in hex or color name.
        radius (float): Background circle radius.
    """
    draw_icon_circle(svg, cx, cy, color, radius)

    icon = create_icon_group(svg, cx, cy)

    BATTERY_WIDTH = 56
    BATTERY_HEIGHT = 18
    BATTERY_SPACING = 24

    draw_battery_cell(icon, 0, -BATTERY_SPACING/2, color,
                    BATTERY_WIDTH,
                    BATTERY_HEIGHT)

    draw_battery_cell(icon, 0, BATTERY_SPACING/2, color,
                    BATTERY_WIDTH,
                    BATTERY_HEIGHT)


# Grid icon
def draw_grid_icon(svg, cx, cy, color, radius):
    """Draw a power grid icon with mast and transmission lines.
    
    Args:
        svg: SVG element to add icon to.
        cx (float): Icon center X coordinate.
        cy (float): Icon center Y coordinate.
        color (str): Background circle color in hex or color name.
        radius (float): Background circle radius.
    """
    draw_icon_circle(svg, cx, cy, color, radius)

    icon = create_icon_group(svg, cx, cy)

    STRUCTURE_WIDTH = 4

    # Main mast
    ET.SubElement(
        icon,
        "line",
        {
            "x1": "0",
            "y1": "-28",
            "x2": "0",
            "y2": "28",
            "stroke-width": str(STRUCTURE_WIDTH),
        },
    )

    # Top crossarm
    ET.SubElement(
        icon,
        "line",
        {
            "x1": "-40",
            "y1": "-18",
            "x2": "40",
            "y2": "-18",
            "stroke-width": str(STRUCTURE_WIDTH),
        },
    )

    # Lower crossarm
    ET.SubElement(
        icon,
        "line",
        {
            "x1": "-30",
            "y1": "-4",
            "x2": "30",
            "y2": "-4",
            "stroke-width": str(STRUCTURE_WIDTH),
        },
    )

    # Upper power lines
    ET.SubElement(
        icon,
        "path",
        {
            "d": "M -40 -14 Q -20 -8 0 -14",
            "fill": "none",
        },
    )

    ET.SubElement(
        icon,
        "path",
        {
            "d": "M 0 -14 Q 20 -8 40 -14",
            "fill": "none",
        },
    )

    # Lower power lines
    ET.SubElement(
        icon,
        "path",
        {
            "d": "M -30 0 Q -15 5 0 0",
            "fill": "none",
        },
    )

    ET.SubElement(
        icon,
        "path",
        {
            "d": "M 0 0 Q 15 5 30 0",
            "fill": "none",
        },
    )

# ------------------------------------------------------------------
# Energy flow ribbons
# ------------------------------------------------------------------

def line_intersection(p1, p2, p3, p4):
    """
    Calculate the intersection point of two lines.

    Parameters:
        p1, p2: (x, y) endpoints of line 1
        p3, p4: (x, y) endpoints of line 2

    Returns:
        (x, y) intersection point, or None if lines are parallel.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 1e-12:
        return None  # Parallel or coincident lines

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) -
          (x1 - x2) * (x3 * y4 - y3 * x4)) / denom

    py = ((x1 * y2 - y1 * x2) * (y3 - y4) -
          (y1 - y2) * (x3 * y4 - y3 * x4)) / denom

    return (px, py)


def arrow_path_v(x0, y0, width=8, shaft_len=320, stem_len=285,
                  head_len=None, tail_len=None) -> str:
    """
    Make bended arrow with tip and notch. 
    Default path:
        "M-2 0"
        "v10"
        "l2 2"
        "l2-2"
        "v-10"
        "v-12"
        "l-22"
        "l-2-2"
        "Z"

    Args:
        x0 (float): Start x coordinate.
        y0 (float): Start y coordinate.
        width (int, optional): Arrow width. Defaults to 8.
        shaft_len (int, optional): Straight arrow part length. Defaults to 40.
        stem_len (int, optional): Straight tip part length. Defaults to 40.
        head_len (int, optional): Head tip length. Defaults to 8.
        tail_len (int, optional): Tail notch length. Defaults to None.

    Returns:
        str: Svg path of the bended arrow
    """
    if tail_len is None:
        tail_len = width/2
    if head_len is None:
        head_len = width/2

    half_w = width / 2

    return " ".join([
        f"M{x0-half_w} {y0}",
        f"v{shaft_len}",
        f"l{head_len} {half_w}",
        f"l{head_len} {-half_w}",
        f"v{-shaft_len}",
        f"v{-stem_len}",
        f"l{-tail_len} {half_w}",
        f"l{-tail_len} {-half_w}",
        "Z",
    ])


def arrow_path_h(x0, y0, width=8, shaft_len=350, stem_len=350,
                  head_len=None, tail_len=None) -> str:
    """
    Make bended arrow with tip and notch. 
    Default path:
        "M-0-2"
        "h-10"
        "l-2 2"
        "l2 2"
        "h10 "
        "h12"
        "l-2-2 "
        "l2-2"
        "Z"

    Args:
        x0 (float): Start x coordinate.
        y0 (float): Start y coordinate.
        width (int, optional): Arrow width. Defaults to 8.
        shaft_len (int, optional): Straight arrow part length. Defaults to 40.
        stem_len (int, optional): Straight tip part length. Defaults to 40.
        head_len (int, optional): Head tip length. Defaults to None.
        tail_len (int, optional): Tail notch length. Defaults to None.

    Returns:
        str: Svg path of the bended arrow
    """
    if tail_len is None:
        tail_len = width/2
    if head_len is None:
        head_len = width/2

    half_w = width / 2

    return " ".join([
        f"M{x0} {y0-half_w}",
        f"h{-shaft_len}",
        f"l{-head_len} {half_w}",
        f"l{head_len} {half_w}",
        f"h{shaft_len}",
        f"h{stem_len}",
        f"l{-tail_len} {-half_w}",
        f"l{tail_len} {-half_w}",
        "Z",
    ])


def arrow_path_ll(x0, y0, width=8, shaft_len=100, stem_len=100,
                  head_len=None, tail_len=None) -> str:
    """
    Make bended arrow with tip and notch. 
    Default path:
        "M0 10"
        "c-0-6-4-10-10-10"
        "l-8 0"
        "l-2 2"
        "l2 2"
        "l8-0"
        "c4-0 6 2 6 6"
        "l0 10"
        "l2-2"
        "l2 2"
        "L0 10"
        "Z"

    Args:
        x0 (float): Start x coordinate.
        y0 (float): Start y coordinate.
        width (int, optional): Arrow width. Defaults to 8.
        shaft_len (int, optional): Straight arrow part length. Defaults to 40.
        stem_len (int, optional): Straight tip part length. Defaults to 40.
        head_len (int, optional): Head tip length. Defaults to 8.
        tail_len (int, optional): Tail notch length. Defaults to None.

    Returns:
        str: Svg path of the bended arrow
    """
    if tail_len is None:
        tail_len = width/2
    if head_len is None:
        head_len = width/2

    half_w = width / 2

    return " ".join([
        f"M{x0-2.5*width} {y0}",
        f"c0 {-1.5*width} {-width} {-2.5*width} {-2.5*width} {-2.5*width}",
        f"h{-shaft_len}",
        f"l{-head_len} {half_w}",
        f"l{head_len} {half_w}",
        f"h{shaft_len}",
        f"c{width} 0 {1.5*width} {half_w} {1.5*width} {1.5*width}",
        f"v{stem_len}",
        f"l{tail_len} {-half_w}",
        f"l{tail_len} {half_w}",
        f"V{y0}",
        "Z",
    ])


def arrow_path_tr(x0, y0, width=8, shaft_len=100, stem_len=100,
                  head_len=None, tail_len=None) -> str:
    """
    Make bended arrow with tip and notch. 
    Default path:
        "M-0-10"
        "c0 6 4 10 10 10"
        "l8-0 "
        "l2-2"
        "l-2-2"
        "l-8 0"
        "c-4 0-6-2-6-6"
        "l-0-10"
        "l-2 2"
        "l-2-2"
        "L-0-10"
        "Z"

    Args:
        x0 (float): Start x coordinate.
        y0 (float): Start y coordinate.
        width (int, optional): Arrow width. Defaults to 8.
        shaft_len (int, optional): Straight arrow part length. Defaults to 40.
        stem_len (int, optional): Straight tip part length. Defaults to 40.
        head_len (int, optional): Head tip length. Defaults to 8.
        tail_len (int, optional): Tail notch length. Defaults to None.

    Returns:
        str: Svg path of the bended arrow
    """
    if tail_len is None:
        tail_len = width/2
    if head_len is None:
        head_len = width/2

    half_w = width / 2

    return " ".join([
        f"M{x0+2.5*width} {y0}",
        f"c0 {1.5*width} {width} {2.5*width} {2.5*width} {2.5*width}",
        f"h{shaft_len}",
        f"l{head_len} {-half_w}",
        f"l{-head_len} {-half_w}",
        f"h{-shaft_len}",
        f"c{-width} 0 {-1.5*width} {-half_w} {-1.5*width} {-1.5*width}",
        f"v{-stem_len}",
        f"l{-tail_len} {half_w}",
        f"l{-tail_len} {-half_w}",
        f"V{y0}",
        "Z",
    ])


def arrow_path_tl(x0, y0, width=8, shaft_len=100, stem_len=100,
                  head_len=None, tail_len=None) -> str:
    """
    Make bended arrow with tip and notch. 
    Default path:
        "M-0-10"
        "c0 6-4 10-10 10"
        "l-8 0"
        "l-2-2"
        "l2-2"
        "l8 0"
        "c4 0 6-2 6-6"
        "l-0-10"
        "l2 2"
        "l2-2"
        "L-0-10"
        "Z"

    Args:
        x0 (float): Start x coordinate.
        y0 (float): Start y coordinate.
        width (int, optional): Arrow width. Defaults to 8.
        shaft_len (int, optional): Straight arrow part length. Defaults to 40.
        stem_len (int, optional): Straight tip part length. Defaults to 40.
        head_len (int, optional): Head tip length. Defaults to 8.
        tail_len (int, optional): Tail notch length. Defaults to None.

    Returns:
        str: Svg path of the bended arrow
    """
    if tail_len is None:
        tail_len = width/2
    if head_len is None:
        head_len = width/2

    half_w = width / 2


    return " ".join([
        f"M{x0-2.5*width} {y0}",
        f"c0 {1.5*width} {-width} {2.5*width} {-2.5*width} {2.5*width}",
        f"h{-shaft_len}",
        f"l{-head_len} {-half_w}",
        f"l{head_len} {-half_w}",
        f"h{shaft_len}",
        f"c{width} 0 {1.5*width} {-half_w} {1.5*width} {-1.5*width}",
        f"v{-stem_len}",
        f"l{tail_len} {half_w}",
        f"l{tail_len} {-half_w}",
        f"V{y0}",
        "Z",
    ])


def add_text(svg, x, y, txt, size=14):
    """Add text element to SVG with default styling.
    
    Args:
        svg: SVG element to add text to.
        x (float): X coordinate of text.
        y (float): Y coordinate of text.
        txt (str): Text content to display.
        size (int, optional): Font size in pixels. Defaults to 14.
    """
    t = ET.SubElement(
        svg,
        "text",
        {
            "x": str(x),
            "y": str(y),
            "font-size": str(size),
            "font-family": "Arial",
            "fill": "#222",
        },
    )
    t.text = txt


def add_arrows(svg, point, colors, widths, 
               h_shaft=350, h_stem=350, v_shaft=320, v_stem=285) -> None:
    """Add energy flow arrows at the specified point.
    
    Args:
        svg: SVG element to add arrows to.
        point (tuple): (x, y) coordinates for arrow intersection point.
        colors (list): List of 5 colors for [ll, tl, tr, v, h] arrows.
        widths (list): List of 5 widths for [ll, tl, tr, v, h] arrows.
        h_shaft (int, optional): Horizontal arrow shaft length. Defaults to 350.
        h_stem (int, optional): Horizontal arrow stem length. Defaults to 350.
        v_shaft (int, optional): Vertical arrow shaft length. Defaults to 320.
        v_stem (int, optional): Vertical arrow stem length. Defaults to 285.
    """
    x, y = point
    w_ll, w_tl, w_tr, w_v, w_h = widths
    c_ll, c_tl, c_tr, c_v, c_h = colors

    ET.SubElement(
        svg,
        "path",
        {
            "d": arrow_path_tl(x+2.5*w_tl-w_v/2, 
                               y-2.5*w_tl-w_h/2, 
                               width=w_tl,
                               shaft_len=h_shaft-2.5*w_tl-w_v/2,
                               stem_len=v_stem-2.5*w_tl-w_h/2),
            "fill": c_tl,
        },
    )

    ET.SubElement(
        svg,
        "path",
        {
            "d": arrow_path_tr(x-2.5*w_tr+w_v/2, 
                               y-2.5*w_tr-w_h/2, 
                               width=w_tr,
                               shaft_len=h_stem-2.5*w_tr-w_v,
                               stem_len=v_stem-2.5*w_tr-w_h/2),
            "fill": c_tr,
        },
    )

    ET.SubElement(
        svg,
        "path",
        {
            "d": arrow_path_ll(x+2.5*w_ll-w_v/2, 
                               y+2.5*w_ll+w_h/2, 
                               width=w_ll,
                               shaft_len=h_shaft-2.5*w_ll-w_v/2,
                               stem_len=v_shaft-2.5*w_ll-w_h/2),
            "fill": c_ll,
        },
    )

    ET.SubElement(
        svg,
        "path",
        {
            "d": arrow_path_v(x, y, width=w_v,
                              shaft_len=v_shaft,
                              stem_len=v_stem),
            "fill": c_v,
        },
    )

    ET.SubElement(
        svg,
        "path",
        {
            "d": arrow_path_h(x, y, width=w_h,
                              shaft_len=h_shaft,
                              stem_len=h_stem),
            "fill": c_h,
        },
    )


def make_figure(w_light_grey, w_dark_grey, w_yellow, 
                w_dark_green, w_green) -> ET.Element:
    """Create energy flow diagram SVG figure.
    
    Args:
        w_light_grey (float): Width of light gray ribbon (grid feed-in).
        w_dark_grey (float): Width of dark gray ribbon (grid import).
        w_yellow (float): Width of yellow ribbon (direct consumption).
        w_dark_green (float): Width of dark green ribbon (battery discharging).
        w_green (float): Width of green ribbon (battery charging).
    
    Returns:
        Element: The SVG element containing the energy flow diagram.
    """
    # Ribbon widths
    LIGHT_GREY_WIDTH = w_light_grey
    DARK_GREEN_WIDTH = w_dark_green
    YELLOW_WIDTH = w_yellow
    DARK_GRAY_WIDTH = w_dark_grey
    GREEN_WIDTH = w_green

    # Extent
    WIDTH = 1200
    HEIGHT = 1000

    # Colors
    GREEN = "#7BC000"
    DARK_GREEN = "#3A7E00"
    YELLOW = "#F2B500"
    LIGHT_GRAY = "#BEBEBE"
    DARK_GRAY = "#666666"
    TEXT = "#333333"

    # Icons positions
    PV_X = 600
    PV_Y = 90

    LOAD_X = 120
    LOAD_Y = 470

    BATTERY_X = 1050
    BATTERY_Y = 470

    GRID_X = 600
    GRID_Y = 900

    ICON_RADIUS = 60

    # Legend position
    LEGEND_X = 720
    LEGEND_Y = 590

    # circle quadrants
    color_quadrants = [DARK_GRAY, YELLOW, GREEN, LIGHT_GRAY, DARK_GREEN]
    widths = [DARK_GRAY_WIDTH, YELLOW_WIDTH, GREEN_WIDTH, LIGHT_GREY_WIDTH, DARK_GREEN_WIDTH]

    # create svg
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(WIDTH),
            "height": str(HEIGHT),
            "viewBox": f"0 0 {WIDTH} {HEIGHT}",
        },
    )

    # Draw icons
    draw_pv_icon(svg, PV_X, PV_Y, GREEN, ICON_RADIUS)
    draw_load_icon(svg, LOAD_X, LOAD_Y, GREEN, ICON_RADIUS)
    draw_battery_icon(svg, BATTERY_X, BATTERY_Y, GREEN, ICON_RADIUS)
    draw_grid_icon(svg, GRID_X, GRID_Y, GREEN, ICON_RADIUS)

    # Icon texts
    text(svg, 725, 100, "Photovoltaic", TEXT, 32)
    text(svg, 725, 135, "System", TEXT, 32)

    text(svg, 60, 320, "Electrical", TEXT, 32)
    text(svg, 60, 355, "Loads", TEXT, 32)

    text(svg, 985, 320, "Battery", TEXT, 32)
    text(svg, 985, 355, "System", TEXT, 32)

    text(svg, 440, 845, "Power", TEXT, 32)
    text(svg, 440, 880, "Grid", TEXT, 32)

    # Crossing point
    cross_point = line_intersection((PV_X,PV_Y), (GRID_X, GRID_Y),
                                    (LOAD_X, LOAD_Y), (BATTERY_X, BATTERY_Y))

    add_arrows(svg, cross_point, color_quadrants, widths)


    # ------------------------------------------------------------------
    # Legend
    # ------------------------------------------------------------------

    legend_items = [
        (YELLOW, "Direct PV Consumption"),
        (GREEN, "Battery Charging"),
        (DARK_GREEN, "Battery Discharging"),
        (LIGHT_GRAY, "Grid Export (surplus)"),
        (DARK_GRAY, "Grid Import (deficit)"),
    ]

    for i, (color, label) in enumerate(legend_items):
        y = LEGEND_Y + i * 55

        ET.SubElement(
            svg,
            "rect",
            {
                "x": str(LEGEND_X),
                "y": str(y),
                "width": "40",
                "height": "30",
                "fill": color,
            },
        )

        text(svg, 780, y + 24, label, TEXT, 32)
    return svg


if __name__ == "__main__":

    # Ribbon widths
    LIGHT_GREY_WIDTH = 60
    DARK_GREEN_WIDTH = 10
    YELLOW_WIDTH = 50
    DARK_GRAY_WIDTH = 30
    GREEN_WIDTH = 40

    # make figure
    svg = make_figure(LIGHT_GREY_WIDTH, DARK_GRAY_WIDTH,
                      YELLOW_WIDTH, DARK_GREEN_WIDTH, 
                      GREEN_WIDTH)

    # Save
    ET.ElementTree(svg).write(
        "pv_energy_flow.svg",
        encoding="utf-8",
        xml_declaration=True,
    )

    print("Created pv_energy_flow.svg")
