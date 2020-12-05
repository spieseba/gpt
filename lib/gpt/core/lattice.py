#
#    GPT - Grid Python Toolkit
#    Copyright (C) 2020  Christoph Lehner (christoph.lehner@ur.de, https://github.com/lehner/gpt)
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import cgpt, gpt, numpy, sys
from gpt.core.expr import factor

mem_book = {}


def get_mem_book():
    return mem_book


class lattice_view_constructor:
    def __init__(self, parent):
        self.parent = parent

    def __getitem__(self, key):
        pos, tidx, shape = gpt.map_key(self.parent, key)
        return gpt.lattice_view(self.parent, pos, tidx)


class lattice(factor):
    __array_priority__ = 1000000

    def __init__(self, first, second=None, third=None):
        self.metadata = {}
        cb = None
        if type(first) == gpt.grid:
            self.grid = first
            if type(second) == str:
                # from desc
                p = second.split(";")
                self.otype = gpt.str_to_otype(p[0])
                cb = gpt.str_to_cb(p[1])
                self.v_obj = [
                    cgpt.create_lattice(self.grid.obj, t, self.grid.precision)
                    for t in self.otype.v_otype
                ]
            else:
                self.otype = second
                if third is not None:
                    self.v_obj = third
                else:
                    self.v_obj = [
                        cgpt.create_lattice(self.grid.obj, t, self.grid.precision)
                        for t in self.otype.v_otype
                    ]
        elif type(first) == gpt.lattice:
            # Note that copy constructor only creates a compatible lattice but does not copy its contents!
            self.grid = first.grid
            self.otype = first.otype
            self.v_obj = [
                cgpt.create_lattice(self.grid.obj, t, self.grid.precision)
                for t in self.otype.v_otype
            ]
            cb = first.checkerboard()
        else:
            raise Exception("Unknown lattice constructor")

        # use first pointer to index page in memory book
        mem_book[self.v_obj[0]] = (self.grid, self.otype, gpt.time())
        if cb is not None:
            self.checkerboard(cb)

    def __del__(self):
        del mem_book[self.v_obj[0]]
        for o in self.v_obj:
            cgpt.delete_lattice(o)

    def advise(self, t):
        if type(t) != str:
            t = t.tag
        for o in self.v_obj:
            cgpt.lattice_advise(o, t)
        return self

    def prefetch(self, t):
        if type(t) != str:
            t = t.tag
        for o in self.v_obj:
            cgpt.lattice_prefetch(o, t)
        return self

    def checkerboard(self, val=None):
        if val is None:
            if self.grid.cb.n == 1:
                return gpt.none

            cb = cgpt.lattice_get_checkerboard(self.v_obj[0])  # all have same cb, use 0
            if cb == gpt.even.tag:
                return gpt.even
            elif cb == gpt.odd.tag:
                return gpt.odd
            else:
                assert 0
        else:
            if val != gpt.none:
                assert self.grid.cb.n != 1
                for o in self.v_obj:
                    cgpt.lattice_change_checkerboard(o, val.tag)

    def describe(self):
        # creates a string without spaces that can be used to construct it again (may be combined with self.grid.describe())
        return self.otype.__name__ + ";" + self.checkerboard().__name__

    def global_bytes(self):
        return self.otype.nfloats * self.grid.gsites * self.grid.precision.nbytes

    def rank_bytes(self):
        return self.global_bytes() // self.grid.Nprocessors

    @property
    def view(self):
        return lattice_view_constructor(self)

    def __setitem__(self, key, value):
        # short code path to zero lattice
        if (
            type(key) == slice
            and key == slice(None, None, None)
            and type(value) == int
            and value == 0
        ):
            for o in self.v_obj:
                cgpt.lattice_set_to_zero(o)
            return

        # general code path, map key
        pos, tidx, shape = gpt.map_key(self, key)

        # convert input to proper numpy array
        value = gpt.util.tensor_to_value(value, dtype=self.grid.precision.complex_dtype)
        if value is None:
            value = memoryview(bytearray())

        # needed bytes and optional cyclic upscaling
        nbytes_needed = len(pos) * numpy.prod(shape) * self.grid.precision.nbytes * 2
        value = cgpt.copy_cyclic_upscale(value, nbytes_needed)

        # create plan
        plan = gpt.copy_plan(self, value)
        plan.destination += gpt.lattice_view(self, pos, tidx)
        plan.source += gpt.global_memory_view(
            self.grid, [[self.grid.processor, value, 0, value.nbytes]]
        )
        xp = plan()

        xp(self, value)

    def __getitem__(self, key):
        pos, tidx, shape = gpt.map_key(self, key)

        value = numpy.ndarray(
            (len(pos), *shape), dtype=self.grid.precision.complex_dtype, order="C"
        )

        plan = gpt.copy_plan(value, self)
        plan.destination += gpt.global_memory_view(
            self.grid, [[self.grid.processor, value, 0, value.nbytes]]
        )
        plan.source += gpt.lattice_view(self, pos, tidx)
        xp = plan()

        xp(value, self)

        # if only a single element is returned and we have the full shape,
        # wrap in a tensor
        if len(value) == 1 and shape == self.otype.shape:
            return gpt.util.value_to_tensor(value[0], self.otype)

        return value

    def mview(self):
        return [cgpt.lattice_memory_view(o) for o in self.v_obj]

    def __repr__(self):
        return "lattice(%s,%s)" % (self.otype.__name__, self.grid.precision.__name__)

    def __str__(self):
        if len(self.v_obj) == 1:
            return self.__repr__() + "\n" + cgpt.lattice_to_str(self.v_obj[0])
        else:
            s = self.__repr__() + "\n"
            for i, x in enumerate(self.v_obj):
                s += "-------- %d to %d --------\n" % (
                    self.otype.v_n0[i],
                    self.otype.v_n1[i],
                )
                s += cgpt.lattice_to_str(x)
            return s

    def __iadd__(self, expr):
        gpt.eval(self, expr, ac=True)
        return self

    def __isub__(self, expr):
        gpt.eval(self, -expr, ac=True)
        return self

    def __imatmul__(self, expr):
        gpt.eval(self, expr, ac=False)
        return self

    def __imul__(self, expr):
        gpt.eval(self, self * expr, ac=False)
        return self

    def __itruediv__(self, expr):
        gpt.eval(self, self / expr, ac=False)
        return self
