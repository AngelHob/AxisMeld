# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Input coordinates for the public roomy-menu specification, not expected dispatch results.

No native state or private debug API is read. Callers independently assert real command,
pose and settings effects; native unit tests verify geometry separately.
"""
import math


def ellipse_page(anchor, labels, measure, bounds, scale=1, first=0, views=False):
    ax, ay, aw, ah = (v / scale for v in anchor)
    bx, by, bw, bh = (v / scale for v in bounds)
    widths = [measure(label) + 40 for label in labels]
    if views:
        names = ['Persp', 'Side', 'Bottom', 'Front', 'Back', 'Top', 'Left']
        widths = [measure(label) + 40 for label in names]
        diagonal = math.sqrt(.5)
        slots = [(0, 1), (1, 0), (diagonal, -diagonal), (0, -1),
                 (-diagonal, -diagonal), (-1, 0), (-diagonal, diagonal)]
        choices = [(list(range(7)), slots, False, 0, 7)]
        center_width = measure('Hotbox Style') + 40
    else:
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
                w = 38 if index < 0 else widths[index] if views else max(widths)
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
            if views:
                result['items'][8] = result['back']
            return result
    raise AssertionError(f'ellipse fixture cannot fit {labels!r} in {bounds!r}')
