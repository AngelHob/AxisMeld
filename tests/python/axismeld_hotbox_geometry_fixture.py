# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Input coordinates for the public roomy-menu specification, not expected dispatch results.

No native state or private debug API is read. Callers independently assert real command,
pose and settings effects; native unit tests verify geometry separately.
"""
import math


def label_prefix_starts(columns, scale):
    """Observed whitespace after zero/one/two 20px icon slots, not label cropping.

    The caller keeps each suffix to its original right edge and compares the full
    independent BLF label template. Later word boundaries are not candidates.
    """
    starts = [0]
    for left, right in zip(columns, columns[1:]):
        # Four logical blank columns: invariant at 1x/2x, unlike scaling the
        # endpoint-inclusive difference between adjacent foreground columns.
        if right-left-1 < 4*scale:
            continue
        if any(abs(right-slots*20*scale) <= 8*scale for slots in (1, 2)):
            starts.append(int(right))
    return tuple(starts)


def visible_bounds(window, obstacles):
    """Trim a WINDOW rectangle by independently observed aligned overlap regions.

    ``obstacles`` contains ``(side, rect)`` pairs in window coordinates.  The caller
    decides visibility from the real UI state; hidden one-pixel Blender regions must
    not be supplied.
    """
    x, y, w, h = window
    window_left, window_right = x, x+w
    window_bottom, window_top = y, y+h
    left, right = window_left, window_right
    bottom, top = window_bottom, window_top
    for side, (ox, oy, ow, oh) in obstacles:
        # Eligibility is always against the original WINDOW.  Testing against the
        # already-trimmed rectangle would make perpendicular obstacles order-dependent.
        obstacle_left = max(window_left, ox)
        obstacle_right = min(window_right, ox+ow)
        obstacle_bottom = max(window_bottom, oy)
        obstacle_top = min(window_top, oy+oh)
        if obstacle_left >= obstacle_right or obstacle_bottom >= obstacle_top:
            continue
        if side == 'left':
            left = max(left, obstacle_right)
        elif side == 'right':
            right = min(right, obstacle_left)
        elif side == 'bottom':
            bottom = max(bottom, obstacle_top)
        elif side == 'top':
            top = min(top, obstacle_bottom)
        else:
            raise AssertionError(f'unknown visible-region side {side!r}')
    if left >= right or bottom >= top:
        raise AssertionError(f'visible obstacles consume WINDOW {window!r}')
    return left, bottom, right-left, top-bottom


def view_page(anchor, labels, measure, bounds, scale):
    """Views input geometry; measure is text-only, including compact captions."""
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    diagonal = math.sqrt(.5)
    slots = [(0, 1), (1, 0), (diagonal, -diagonal), (0, -1),
             (-diagonal, -diagonal), (-1, 0), (-diagonal, diagonal), (diagonal, diagonal)]
    for compact, with_style in ((False, True), (True, True), (True, False)):
        names = (['Persp', 'Side', 'Bottom', 'Front', 'Back', 'Top', 'Left'] if compact else
                 ['Perspective View', 'Right View', 'Bottom View', 'Front View',
                  'Back View', 'Top View', 'Left View'])
        widths = [measure(label) + 20 + 16 for label in names]
        widths = [max(widths)] * len(widths)
        for ry in (0,):
            rectangles = [(-aw/2, -12 if compact else -19, aw, 24 if compact else 38)]
            clear = True
            for w, (nx, ny) in zip(widths, slots):
                side = (w + aw)/2 + 8
                x = (0 if nx == 0 else math.copysign(side - (0 if ny == 0 else 16), nx)) - w/2
                y = (0 if ny == 0 else math.copysign((28 if compact else 35) * (2 if nx == 0 else 1), ny)) - 12
                clear &= all(x+w+3.999 <= ox or ox+ow+3.999 <= x or
                             y+24+3.999 <= oy or oy+oh+3.999 <= y
                             for ox, oy, ow, oh in rectangles)
                rectangles.append((x, y, w, 24))
            if with_style:
                w = measure('Hotbox Style') + 20 + 60
                rectangles.append((-w/2, min(r[1] for r in rectangles)-28, w, 24))
            left = min(r[0] for r in rectangles)
            right = max(r[0]+r[2] for r in rectangles)
            bottom = min(r[1] for r in rectangles)
            top = max(r[1]+r[3] for r in rectangles)
            if right-left > bw-24 or top-bottom > bh-24:
                break
            if not clear:
                continue
            cx = max(bx+12-left, min(ax+aw/2, bx+bw-12-right))
            cy = max(by+12-bottom, min(ay+ah/2, by+bh-12-top))
            def translated(r):
                x, y, w, h = r
                return ((x+cx)*scale, (y+cy)*scale, w*scale, h*scale)
            result = {'items': [None]*max(10, len(labels)), 'back': None,
                      'previous': None, 'next': None, 'capacity': len(names), 'first': 0}
            for i in range(7):
                result['items'][i] = translated(rectangles[i+1])
            # Legacy index9 is the non-drawn NE cancellation gap. Mirror
            # the actual NW rectangle without treating it as a visible item.
            nw=rectangles[7]
            result['items'][9]=translated((-nw[0]-nw[2],nw[1],nw[2],nw[3]))
            if with_style:
                result['items'][8] = translated(rectangles[-1])
            return result
    raise AssertionError(f'view fixture cannot fit in {bounds!r}')


def native_page(anchor, labels, measure, bounds, scale=1, marking_origin=None, first=0,
                submenu_indices=()):
    if not labels:
        raise AssertionError('Native list requires at least one label')
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    submenu_indices = frozenset(submenu_indices)
    w = max(measure(label) + (60 if i in submenu_indices else 40)
            for i, label in enumerate(labels))

    def position(h):
        x = ax+aw
        y = max(by+12, min(ay+ah-h, by+bh-12-h))
        if x+w <= bx+bw-12:
            return x, y
        x = ax-w
        if x >= bx+12:
            return x, y
        for cy in (ay+ah, ay-h):
            for cx in (max(bx+12, min(ax, bx+bw-12-w)), bx+12, bx+bw-12-w):
                if cy < by+12 or cy+h > by+bh-12:
                    continue
                if marking_origin:
                    ox, oy = (v/scale for v in marking_origin)
                    dx, dy = ox-max(cx, min(ox, cx+w)), oy-max(cy, min(oy, cy+h))
                    if dx*dx+dy*dy <= 12*12:
                        continue
                return cx, cy
        return None

    heights=[6 if label=='' else 24 for label in labels]
    for room in range(int(bh-24),5,-6):
        paged=sum(heights)>room
        if paged:
            available=room-48
            maximum=len(labels)
            used=0
            while maximum>0 and used+heights[maximum-1]<=available:
                maximum-=1;used+=heights[maximum]
            if maximum==len(labels):continue
            offset=min(max(first,0),maximum)
            end=offset;used=0
            while end<len(labels) and used+heights[end]<=available:
                used+=heights[end];end+=1
            h=used+48
        else:
            offset=0;end=len(labels);h=sum(heights)
        if end==offset:continue
        origin=position(h)
        if origin is None:continue
        x,y=origin
        items=[None]*len(labels)
        top=y+h
        previous=next_row=None
        if paged:
            top-=24;previous=(x*scale,top*scale,w*scale,24*scale)
        for index in range(offset,end):
            top-=heights[index]
            items[index]=(x*scale,top*scale,w*scale,heights[index]*scale)
        if paged:
            top-=24;next_row=(x*scale,top*scale,w*scale,24*scale)
        return {'items':items,'previous':previous,'next':next_row,'back':None,
                'capacity':end-offset,'first':offset}
    raise AssertionError(f'Native list cannot fit without covering its entry in {bounds!r}')


def native_list(anchor, labels, measure, bounds, scale=1, marking_origin=None):
    return native_page(anchor, labels, measure, bounds, scale, marking_origin)['items']


def style_list(anchor, measure, bounds, scale=1, marking_origin=None):
    return native_list(anchor, ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only'),
                       measure, bounds, scale, marking_origin)


def ellipse_page(anchor, labels, measure, bounds, scale=1, first=0, views=False):
    if views:
        return view_page(anchor, labels, measure, bounds, scale)
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    native_entries = {'Menu Rows', 'Hotbox Style', 'Transparency', 'Center Mouse Buttons', 'Tool Settings'}
    widths = [measure(label) + (60 if label in native_entries else 16) for label in labels]
    center_width = aw
    choices = []
    for capacity in range(min(len(labels), 8), 0, -1):
        paged = capacity < len(labels)
        offset = min(first, len(labels)-capacity) if paged else 0
        indices = ([-1] if paged else []) + list(range(offset, offset+capacity)) + ([-2] if paged else [])
        phase = math.pi/4 if len(indices) == 2 else math.pi/2
        slots = [(math.cos(phase-2*math.pi*i/len(indices)),
                  math.sin(phase-2*math.pi*i/len(indices))) for i in range(len(indices))]
        choices.append((indices, slots, paged, offset, capacity))
    for indices, slots, paged, offset, capacity in choices:
        for ry in range(24, int(bh)):
            rectangles = [(-center_width/2, -12, center_width, 24)]
            clear = True
            for index, (nx, ny) in zip(indices, slots):
                w = 38 if index < 0 else max(widths)
                candidate = (nx*1.7*ry-w/2, ny*ry-12, w, 24)
                x, y, w, h = candidate
                clear &= all(x+w+3.999 <= ox or ox+ow+3.999 <= x or
                             y+h+3.999 <= oy or oy+oh+3.999 <= y
                             for ox, oy, ow, oh in rectangles)
                rectangles.append(candidate)
            left = min(r[0] for r in rectangles)
            right = max(r[0]+r[2] for r in rectangles)
            bottom = min(r[1] for r in rectangles)
            top = max(r[1]+r[3] for r in rectangles)
            if right-left > bw-24 or top-bottom > bh-24:
                break
            if not clear:
                continue
            cx = max(bx+12-left, min(ax+aw/2, bx+bw-12-right))
            cy = max(by+12-bottom, min(ay+ah/2, by+bh-12-top))
            def translated(rectangle, natural=None):
                x, y, w, h = rectangle
                if natural is not None:
                    x, w = x+(w-natural)/2, natural
                return ((x+cx)*scale, (y+cy)*scale, w*scale, h*scale)
            result = {'items': [None]*len(labels), 'back': translated(rectangles[0]),
                      'previous': None, 'next': None, 'capacity': capacity, 'first': offset}
            for index, rectangle in zip(indices, rectangles[1:]):
                value = translated(rectangle, 38 if index < 0 else max(widths))
                if index < 0:
                    result['previous' if index == -1 else 'next'] = value
                else:
                    result['items'][index] = value
            return result
    raise AssertionError(f'ellipse fixture cannot fit {labels!r} in {bounds!r}')
