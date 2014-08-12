from __future__ import (print_function, division, absolute_import)
from vector_drawer import SVGDrawer
import numpy as np
from math import pi, atan2, cos, sin

class Point(object):
    def __init__(self, x, y):
        self.vector = np.array((x, y))

    def __repr__(self):
        return "Point({0[0]}, {0[1]})".format(self.vector)

    @property
    def x(self):
        return self.vector[0]

    @property
    def y(self):
        return self.vector[1]

    @property
    def r(self):
        return self.norm

    @property
    def phi(self):
        return atan2(self.y, self.x)

    @property
    def norm(self):
        return np.linalg.norm(self.vector)

    def __mul__(self, other):
        return Point(*(self.vector * other))

    def __rmul__(self, other):
        return self * other

    def __div__(self, other):
        return Point(*(self.vector // other))

    def __truediv__(self, other):
        return Point(*(self.vector / other))

    def __neg__(self):
        return -1 * self

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(*(self.vector + other.vector))
        else:
            return Point(*(self.vector + other))

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self + (-1) * other

    def __rsub__(self, other):
        return other + (-1) * self

    def __iter__(self):
        return self.vector.__iter__()

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return np.array_equal(self.vector, other.vector)

    def __hash__(self):
        return hash(self.vector)


class GaugeDrawer(object):
    width = 2.0
    height = 1.0
    scale = 1200
    zero_pt = Point(.25, .5)
    mid_pt = Point(1.0, .25)
    end_pt = Point(1.75, .5)
    thick_line = 0.020
    thin_line = 0.010
    major_tick_length= 0.1
    minor_tick_length = major_tick_length / 3
    text_size = 0.075

    def __init__(self, major_tick_values,
                 major_tick_labels=None,
                 n_minor_ticks=1):
        self.center, self.radius = solve_circle_3pts((self.zero_pt,
                                                      self.mid_pt,
                                                      self.end_pt))
        major_tick_labels = major_tick_labels or map(str, major_tick_values)
        in_order = sorted(zip(major_tick_values,
                              major_tick_labels))
        self.major_tick_values = [tick[0] for tick in in_order]
        self.major_tick_labels = [tick[1] for tick in in_order]
        self.minor_tick_values = []
        for lo_maj, hi_maj in zip(major_tick_values[:-1],
                                  major_tick_values[1:]):
            self.minor_tick_values.extend(
                divide_interval(lo_maj, hi_maj, n_minor_ticks,
                                include_lo=False, include_hi=False))

        self.zero_angle = self._get_angle_from_pt(self.zero_pt)
        self.zero_value = self.major_tick_values[0]
        self.end_angle = self._get_angle_from_pt(self.end_pt)
        self.end_value = self.major_tick_values[-1]

    def _get_angle_from_value(self, value):
        angle_range = self.end_angle - self.zero_angle
        value_range = self.end_value - self.zero_value

        rel_angle = float(value - self.zero_value) / value_range * angle_range

        return self.zero_angle + rel_angle

    def _get_angle_from_pt(self, point):
        rel_pt = point - self.center
        mirrored_pt = Point(rel_pt.x, -rel_pt.y)  # SVG y-axis points down
        angle_to_x_axis = mirrored_pt.phi
        angle_to_y_axis = pi/2 - angle_to_x_axis
        while (angle_to_y_axis > pi):
            angle_to_y_axis -= 2*pi
        while (angle_to_y_axis <= -pi):
            angle_to_y_axis += 2*pi
        return angle_to_y_axis

    def _get_point_from_angle(self, angle):
        angle_to_x = pi/2 - angle
        x = self.radius * cos(angle_to_x)
        y = -self.radius * sin(angle_to_x)  # SVG y-axis points down
        return Point(x, y) + self.center

    def _get_point_from_value(self, value):
        angle = self._get_angle_from_value(value)
        return self._get_point_from_angle(angle)

    def draw(self, filename):
        svg = SVGDrawer(self._scale(self.width), self._scale(self.height))
        self._draw_arc(svg)
        self._draw_major_ticks(svg)
        self._draw_minor_ticks(svg)
        self._draw_labels(svg)
        with open(filename, 'w') as f:
            svg.save(f)

    def _draw_arc(self, svg):
        # start at end so the curves are convex
        path = svg.draw_path(start=self._scale_pt(self.end_pt),
                             fill='none', color='black',
                             width=self._scale(self.thick_line))
        path.arc_to(self._scale_pt(self.zero_pt),
                    self._scale(self.radius))

    def _draw_major_ticks(self, svg):
        for tick_value in self.major_tick_values:
            self._draw_tick(svg, tick_value, self.major_tick_length,
                            self.thick_line)

    def _draw_minor_ticks(self, svg):
        for tick_value in self.minor_tick_values:
            self._draw_tick(svg, tick_value, self.minor_tick_length,
                            self.thin_line)

    def _draw_tick(self, svg, value, length, thick):
        start, end = self._get_major_tick_limits(value, length)
        svg.draw_line(self._scale_pt(start),
                      self._scale_pt(end),
                      color='black', width=self._scale(thick))

    def _draw_labels(self, svg):
        for value, label in zip(self.major_tick_values,
                                self.major_tick_labels):
            _, text_center = self._get_major_tick_limits(
                value, 1.15 * self.major_tick_length)
            angle = 180.0 / pi * self._get_angle_from_value(value)
            svg.draw_text(self._scale_pt(text_center), label,
                          size=self._scale(self.text_size),
                          color='black',
                          family='Helvetica',
                          anchor='middle',
                          rotate_angle=angle)

    def _get_major_tick_limits(self, value, length):
        point = self._get_point_from_value(value)
        radial = point - self.center
        radial_dir = radial / radial.norm
        start = point - 0.5 * self.thick_line * radial_dir
        end = point + length*radial_dir
        return start, end

    def _scale(self, value):
        return int(round(value * self.scale))

    def _scale_pt(self, pt):
        return Point(*(self._scale(val) for val in pt))

def solve_circle_3pts(three_points):
    """ Find the center, radius of a circle
        passing through the given 3 points
        Algorithm from:
        http://www.abecedarical.com/zenosamples/zs_circle3pts.html
    """
    three_points = [Point(*pt) for pt in three_points]
    a = np.array([[pt.x, pt.y, 1] for pt in three_points])
    m11 = np.linalg.det(a)

    if m11 == 0:
        raise ValueError("The points are collinear.")

    a = np.array([[pt.x**2 + pt.y**2, pt.y, 1] for pt in three_points])
    m12 = np.linalg.det(a)

    a = np.array([[pt.x**2 + pt.y**2, pt.x, 1] for pt in three_points])
    m13 = np.linalg.det(a)

    a = np.array([[pt.x**2 + pt.y**2, pt.x, pt.y] for pt in three_points])
    m14 = np.linalg.det(a)

    center = Point(0.5 * m12 / m11, -0.5 * m13 / m11)
    r = np.sqrt(center.x**2 + center.y**2 + m14/m11)

    return center, r

def divide_interval(lo, hi, n, include_lo=True, include_hi=False):
    """ Returns n values starting at lo and evenly dividing the
        range between lo and hi.

        If include_lo is True, the first value will be lo
        If include_hi is True, the last value will be hi.
        Otherwise, the values returned will not include the limits.
        Defaults are include_lo=True, include_hi=False

        Example:
        --------
        >>> divide_interval(0, 5, 5)
        [0, 1, 2, 3, 4]
        >>> divide_interval(0, 5, 6, include_hi=True)
        [0, 1, 2, 3, 4, 5]
    """
    values = []
    if not include_lo:
        n += 1
    if not include_hi:
        n += 1
    values = [lo + i * float(hi - lo) / (n - 1) for i in xrange(n)]
    if not include_lo:
        values.pop(0)
    if not include_hi:
        values.pop(-1)
    return values
