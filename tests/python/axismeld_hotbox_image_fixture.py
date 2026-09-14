# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent screenshot geometry; no native layout or command state is read."""
import numpy as np


def observed_menu_rectangles(mask, minimum_width, minimum_height):
    """Four-neighbour components preserve actual gaps between native columns.

    Input is an observed background-color boolean mask, in bottom-up image pixels.
    Returns (xmin,ymin,xmax,ymax), sorted left to right.
    """
    parents=[];boxes=[];previous=[]
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    def join(a,b):
        a,b=find(a),find(b)
        if a==b:return
        parents[b]=a
        boxes[a]=[min(boxes[a][0],boxes[b][0]),min(boxes[a][1],boxes[b][1]),
                  max(boxes[a][2],boxes[b][2]),max(boxes[a][3],boxes[b][3])]
    for y in range(mask.shape[0]):
        xs=np.flatnonzero(mask[y]);current=[]
        for span in np.split(xs,np.flatnonzero(np.diff(xs)>1)+1):
            if not len(span):continue
            x0,x1=int(span[0]),int(span[-1])+1
            i=len(parents);parents.append(i);boxes.append([x0,y,x1,y+1]);current.append((x0,x1,i))
        start=0
        for x0,x1,i in current:
            while start<len(previous) and previous[start][1]<=x0:start+=1
            j=start
            while j<len(previous) and previous[j][0]<x1:
                join(i,previous[j][2]);j+=1
        previous=current
    result=[tuple(boxes[i]) for i in range(len(parents)) if find(i)==i
            and boxes[i][2]-boxes[i][0]>minimum_width and boxes[i][3]-boxes[i][1]>minimum_height]
    return sorted(result,key=lambda r:r[0])


def menu_background_mask(pixels):
    rgb=pixels[:,:,:3]
    return ((rgb[:,:,0]>.3)&(rgb[:,:,2]>.25)&
            (np.minimum(rgb[:,:,0],rgb[:,:,2])>2.2*rgb[:,:,1]))


def observed_radial_rectangles(pixels, scale, expected_directions):
    """Locate a direct Object/Create/component ring after its actual translation.

    Uses the diagnostic magenta theme shared by content GUI observers. It does
    not infer motion from companion count, height, column count or source press.
    """
    boxes=[r for r in observed_menu_rectangles(menu_background_mask(pixels),35*scale,13*scale)
           if r[3]-r[1]<=27*scale]
    if not boxes: raise AssertionError('No actual radial button backgrounds')
    # Native toolbar controls can share the diagnostic theme. Identify a full
    # directional constellation, rather than treating the highest colored box
    # in the entire window as its North button.
    candidates=[]
    for north in boxes:
        for south in boxes:
            ny=(north[1]+north[3])/2;sy=(south[1]+south[3])/2
            nx=(north[0]+north[2])/2;sx=(south[0]+south[2])/2
            if not 70*scale<ny-sy<180*scale or abs(nx-sx)>20*scale: continue
            cx=(nx+sx)/2;cy=(ny+sy)/2;found={};duplicate=False
            for rect in boxes:
                rx=(rect[0]+rect[2])/2;ry=(rect[1]+rect[3])/2
                if not sy<=ry<=ny or abs(rx-cx)>400*scale: continue
                dx=rx-cx;dy=ry-cy
                direction=('N' if dy>16*scale else 'S' if dy < -16*scale else '')
                direction+=('E' if dx>20*scale else 'W' if dx < -20*scale else '')
                if not direction: continue
                if direction in found: duplicate=True;break
                found[direction]=rect
            if not duplicate and set(found)==set(expected_directions):
                candidates.append({'rects':found,'center':(cx,cy)})
    if len(candidates)!=1:
        raise AssertionError(f'Expected one complete observed radial constellation, got {candidates!r}; boxes={boxes!r}')
    return candidates[0]
