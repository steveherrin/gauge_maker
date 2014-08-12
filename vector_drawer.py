from __future__ import (print_function, division, absolute_import)

class VectorDrawer(object):
    def save(self, file):
        if hasattr(file, 'write'):
            self._save(f)
        else:
            try:
                with open(file, 'wb') as f:
                    self._save(f)
            except TypeError:
                raise TypeError("Argument to save must be a string or " +
                                " support a 'write' method.")

    def _save(self, buf):
        raise NotImplementedError()


class SVGDrawer(VectorDrawer):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._elements = []

    def _save(self, buf):
        buf.write('<svg height="{}" width="{}">\n'
                  .format(height, width))
        for element in self._elements:
            element.save(buf)
        buf.write('</svg>\n')

    def draw_line(self, start, end, color=None, width=None):
        new_line = SVGLine(start,
                           end,
                           color=color,
                           width=width)
        self._elements.append(new_line)

    def draw_path(self, start, fill='none', color=None, width=None):
        new_path = SVGPath(start,
                           fill=fill,
                           color=color,
                           width=width)
        self._elements.append(new_path)
        return new_path


class SVGElement(object):
    def save(self, buf):
        raise NotImplementedError()


class SVGLine(SVGElement):
    def __init__(self, start, end, **style):
        self.start = start
        self.end = end
        self.style = {}
        _move_between_dicts(style, 'color', self.style, 'stroke')
        _move_between_dicts(style, 'width', self.style, 'stroke-width')
        if len(style) > 0:
            raise ValueError("Unsupported style attributes: '{}'"
                             .format("' ,'".join(style)))

    def save(self, buf):
        buf.write('<line x1="{0.x}" y1="{0.y}" '.format(start))
        buf.write('x2="{0.x}" y2="{0.y}" '.format(end))
        buf.write('style="')
        for key, value in self.style:
            buf.write('{}:{};'.format(key, value))
        buf.write(' />\n')

class SVGPath(SVGElement):
    def __init__(self, start=None, actions=None, **style):
        self.style = {}
        _move_between_dicts(style, 'fill', self.style, 'fill')
        _move_between_dicts(style, 'color', self.style, 'stroke')
        _move_between_dicts(style, 'width', self.style, 'stroke-width')
        if len(style) > 0:
            raise ValueError("Unsupported style attributes: '{}'"
                             .format("' ,'".join(style)))
        if start and actions:
            raise ValueError("Specifying a start and actions is ambiguous.")
        actions = actions or []
        self._actions = list(actions)
        if start is not None:
            self.move_to(start)

    def save(self, buf):
        buf.write('<path d="')
        for action in self._actions:
            buf.write(' ' + action.get_string())
        buf.write('"')
        for key, value in self.style:
            buf.write(' {}="{}"'.format(key, value))
        buf.write(' />\n')

    def line_to(self, pt):
        self._actions.append(SVGPathLine(pt))

    def arc_to(self, pt, radius_x, radius_y=None, rotation=0,
               large_arc=False, sweep=False):
        self._actions.append(SVGPathArc(pt, radius_x, radius_y,
                                        rotation, large_arc, sweep))

    def move_to(self, pt):
        self._actions.append(SVGPathMove(pt))

    def close_path(self):
        self._actions.append(SVGPathClose())


class SVGPathAction(object):
    def get_string(self):
        raise NotImplementedError

class SVGPathMove(SVGPathAction):
    def __init__(self, pt):
        self.pt = pt

    def get_string(self):
        return 'M{0.x},{0.y}'.format(self.pt)

class SVGPathClose(SVGPathAction):
    def get_string(self):
        return 'Z'

class SVGPathLine(SVGPathAction):
    def __init__(self, pt):
        self.pt = pt

    def get_string(self):
        return 'L{0.x},{0.y}'.format(self.pt)

def SVGPathArc(SVGPathAction):
    def __init__(self, pt, radius_x, radius_y=None,
                 rotation=0, large_arc=False, sweep=False):
        self.pt = pt
        self.radius_x = radius_x
        if radius_y is None:
            radius_y = radius_x  # it might be 0, though this would be odd
        self.radius_y = radius_y
        self.rotation = rotation
        self.large_arc = large_arc
        self.sweep = sweep

    def get_string(self):
        return ('A{0},{1} {2} {3},{4}, {5.x},{5.y}'
                .format(self.radius_x, self.radius_y, self.rotation,
                        int(self.large_arc), int(self.sweep), self.pt))


def _move_between_dicts(old_dict, old_key, new_dict, new_key):
    if old_key in old_dict and old_dict[old_key] is not None:
        new_dict[new_key] = old_dict.pop(old_key)
