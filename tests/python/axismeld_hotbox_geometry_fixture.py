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
        widths = [measure(label) + 40 for label in names]
        for ry in range(24, int(bh)):
            rectangles = [(-aw/2, -19, aw, 38)]  # Reserved hole, never a secondary button.
            clear = True
            for w, (nx, ny) in zip(widths, slots):
                x, y = nx*1.7*ry-w/2, ny*ry-19
                clear &= all(x+w+9.999 <= ox or ox+ow+9.999 <= x or
                             y+38+9.999 <= oy or oy+oh+9.999 <= y
                             for ox, oy, ow, oh in rectangles)
                rectangles.append((x, y, w, 38))
            if not compact:
                w = measure('Hotbox Style') + 40
                rectangles.append((-w/2, min(r[1] for r in rectangles)-48, w, 38))
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


def style_list(anchor, measure, bounds, scale=1):
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    w = max(measure(label) for label in ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only')) + 40
    h = 3*48-10
    x = ax+aw+10 if ax+aw+10+w <= bx+bw-12 else max(bx+12, ax-10-w)
    y = max(by+12, min(ay+38-h, by+bh-12-h))
    return [(x*scale, (y+h-38-i*48)*scale, w*scale, 38*scale) for i in range(3)]


def ellipse_page(anchor, labels, measure, bounds, scale=1, first=0, views=False):
    if views:
        return view_page(anchor, labels, measure, bounds, scale)
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    widths = [measure(label) + 40 for label in labels]
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
            rectangles = [(-center_width/2, -19, center_width, 38)]
            clear = True
            for index, (nx, ny) in zip(indices, slots):
                w = 38 if index < 0 else max(widths)
                candidate = (nx*1.7*ry-w/2, ny*ry-19, w, 38)
                x, y, w, h = candidate
                clear &= all(x+w+9.999 <= ox or ox+ow+9.999 <= x or
                             y+h+9.999 <= oy or oy+oh+9.999 <= y
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
