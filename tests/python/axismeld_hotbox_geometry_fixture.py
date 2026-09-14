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


_native_surface = None
_native_parents = {}


def native_fixture_surface(bounds):
    """Set independently observed whole-window pixel bounds for input prediction.

    Views geometry remains region-local. No native layout/debug data is queried.
    """
    global _native_surface
    bounds = tuple(bounds) if bounds is not None else None
    if bounds is None or bounds != _native_surface:
        _native_parents.clear()
    _native_surface = bounds


def native_page(anchor, labels, measure, bounds, scale=1, marking_origin=None, first=0,
                submenu_indices=()):
    """Complete native columns. Legacy ``first`` is accepted but cannot hide rows."""
    if not labels:
        raise AssertionError('Native list requires at least one label')
    anchor = tuple(anchor)
    parent = _native_parents.get(anchor)
    # A child of an expanded parent remains on that same drawing surface.
    initial = parent['bounds'] if parent else tuple(bounds)
    surfaces = [initial]
    if _native_surface is not None and _native_surface != initial:
        surfaces.append(_native_surface)
    ax, ay, aw, ah = (v/scale for v in anchor)
    indices = frozenset(submenu_indices)
    row_width = max(measure(label)+(60 if i in indices else 40)
                    for i,label in enumerate(labels))
    heights = [6 if not label else 24 for label in labels]
    parent_rects = parent['columns'] if parent else [anchor]
    pl = min(r[0] for r in parent_rects)/scale
    pr = max(r[0]+r[2] for r in parent_rects)/scale
    pb = min(r[1] for r in parent_rects)/scale
    pt = max(r[1]+r[3] for r in parent_rects)/scale
    def origin_clear(x,y,w,h):
        if marking_origin is None: return True
        ox,oy = (v/scale for v in marking_origin)
        dx,dy = ox-max(x,min(ox,x+w)), oy-max(y,min(oy,y+h))
        return dx*dx+dy*dy > 144
    for surface_index,surface in enumerate(surfaces):
        bx,by,bw,bh=(v/scale for v in surface)
        for room in range(int(bh-24),23,-6):
            ranges=[]
            for prefer_separator in (True,False):
                ranges=[];start=0
                while start<len(labels):
                    end=start;used=0;split=None
                    while end<len(labels) and used+heights[end]<=room:
                        used+=heights[end];end+=1
                        if not labels[end-1] and used>=room/2: split=(end,used)
                    if end==start: break
                    if prefer_separator and end<len(labels) and split: end,used=split
                    ranges.append((start,end,used));start=end
                width=len(ranges)*(row_width+4)-4
                if start==len(labels) and width<=bw-24: break
            if not ranges or start!=len(labels) or width>bw-24: continue
            # Editor retries the entire composition on its larger surface before
            # keeping a region-local multi-column result.
            if len(ranges)>1 and surface_index+1<len(surfaces): break
            height=max(r[2] for r in ranges)
            y=max(by+12,min(ay+ah-height,by+bh-12-height))
            candidates=[(pr,y),(pl-width,y)]
            for cy in (pt,pb-height):
                candidates.extend((cx,cy) for cx in
                                  (max(bx+12,min(ax,bx+bw-12-width)),bx+12,bx+bw-12-width))
            placed=None
            for x,y in candidates:
                if x<bx+12 or y<by+12 or x+width>bx+bw-12 or y+height>by+bh-12: continue
                if any(x<r[0]/scale+r[2]/scale and x+width>r[0]/scale and
                       y<r[1]/scale+r[3]/scale and y+height>r[1]/scale for r in parent_rects): continue
                if not origin_clear(x,y,width,height): continue
                placed=(x,y);break
            if placed is None:
                for y in (by+12,by+bh-12-height):
                    for x in (bx+12,bx+bw-12-width):
                        covers=x<ax+aw and x+width>ax and y<ay+ah and y+height>ay
                        if (not covers or parent is None) and origin_clear(x,y,width,height):
                            placed=(x,y);break
                    if placed is not None: break
            if placed is None: continue
            x,y=placed;items=[None]*len(labels);columns=[]
            for column,(start,end,used) in enumerate(ranges):
                left=x+column*(row_width+4);top=y+height
                columns.append((left*scale,(top-used)*scale,row_width*scale,used*scale))
                for index in range(start,end):
                    top-=heights[index]
                    items[index]=(left*scale,top*scale,row_width*scale,heights[index]*scale)
            result={'items':items,'previous':None,'next':None,'back':None,
                    'capacity':len(labels),'first':0,'columns':columns,'bounds':surface}
            for item in items: _native_parents[tuple(item)]=result
            return result
    raise AssertionError(f'Complete native list cannot fit {labels!r} in {surfaces!r}')


def native_list(anchor, labels, measure, bounds, scale=1, marking_origin=None):
    return native_page(anchor, labels, measure, bounds, scale, marking_origin)['items']


def style_list(anchor, measure, bounds, scale=1, marking_origin=None):
    return native_list(anchor, ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only'),
                       measure, bounds, scale, marking_origin)


def ellipse_page(anchor, labels, measure, bounds, scale=1, first=0, views=False):
    if views:
        return view_page(anchor, labels, measure, bounds, scale)
    # Non-marking directories are ordinary native lists; only Views is radial.
    submenu_names = {'Views', 'Menu Rows', 'Hotbox Style', 'Transparency',
                     'Center Mouse Buttons', 'Tool Settings', 'Nested Entries'}
    return native_page(anchor, labels, measure, bounds, scale, first=first,
                       submenu_indices=[i for i,label in enumerate(labels) if label in submenu_names])
