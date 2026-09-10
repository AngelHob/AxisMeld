# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Input coordinates for the public roomy-menu specification, not expected dispatch results.

No native state or private debug API is read. Callers independently assert real command,
pose and settings effects; native unit tests verify geometry separately.
"""
import math


def view_page(anchor, labels, measure, bounds, scale):
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    diagonal = math.sqrt(.5)
    slots = [(0, 1), (1, 0), (diagonal, -diagonal), (0, -1),
             (-diagonal, -diagonal), (-1, 0), (-diagonal, diagonal), (diagonal, diagonal)]
    for compact in (False, True):
        names = (['Persp', 'Side', 'Bottom', 'Front', 'Back', 'Top', 'Left'] if compact else
                 ['Perspective View', 'Right View', 'Bottom View', 'Front View',
                  'Back View', 'Top View', 'Left View', 'New Camera'])
        widths = [measure(label) + 16 for label in names]
        for ry in range(24, int(bh)):
            rectangles = [(-aw/2, -19, aw, 38)]  # Reserved hole, never a secondary button.
            clear = True
            for w, (nx, ny) in zip(widths, slots):
                x, y = nx*1.7*ry-w/2, ny*ry-12
                clear &= all(x+w+3.999 <= ox or ox+ow+3.999 <= x or
                             y+24+3.999 <= oy or oy+oh+3.999 <= y
                             for ox, oy, ow, oh in rectangles)
                rectangles.append((x, y, w, 24))
            if not compact:
                w = measure('Hotbox Style') + 60
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
            if not compact:
                result['items'][9] = translated(rectangles[8])
                result['items'][8] = translated(rectangles[9])
            return result
    raise AssertionError(f'view fixture cannot fit in {bounds!r}')


def native_list(anchor, labels, measure, bounds, scale=1, marking_origin=None):
    if not labels:
        raise AssertionError('Native list requires at least one label')
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    w = max(measure(label) for label in labels) + 40
    h = len(labels)*24
    x = ax+aw+10 if ax+aw+10+w <= bx+bw-12 else ax-10-w
    y = max(by+12, min(ay+ah-h, by+bh-12-h))
    if x < bx+12:
        positions = []
        for cy in (ay+ah+10, ay-10-h):
            for cx in (max(bx+12, min(ax, bx+bw-12-w)), bx+12, bx+bw-12-w):
                if cy < by+12 or cy+h > by+bh-12:
                    continue
                if marking_origin:
                    ox, oy = (v/scale for v in marking_origin)
                    dx, dy = ox-max(cx, min(ox, cx+w)), oy-max(cy, min(oy, cy+h))
                    if dx*dx+dy*dy <= 12*12:
                        continue
                positions.append((cx, cy))
        if not positions:
            raise AssertionError(f'Native list cannot fit without covering its entry in {bounds!r}')
        x, y = positions[0]
    return [(x*scale, (y+h-(i+1)*24)*scale, w*scale, 24*scale)
            for i in range(len(labels))]


def style_list(anchor, measure, bounds, scale=1, marking_origin=None):
    return native_list(anchor, ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only'),
                       measure, bounds, scale, marking_origin)


def ellipse_page(anchor, labels, measure, bounds, scale=1, first=0, views=False):
    if views:
        return view_page(anchor, labels, measure, bounds, scale)
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    native_entries = {'Menu Rows', 'Hotbox Style', 'Transparency'}
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
                value = translated(rectangle, 38 if index < 0 else widths[index])
                if index < 0:
                    result['previous' if index == -1 else 'next'] = value
                else:
                    result['items'][index] = value
            return result
    raise AssertionError(f'ellipse fixture cannot fit {labels!r} in {bounds!r}')
