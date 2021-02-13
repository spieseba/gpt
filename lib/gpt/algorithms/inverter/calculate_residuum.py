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
import gpt as g


class calculate_residuum:
    def __init__(self, tag=None):
        self.tag = "" if tag is None else f" [{tag}]"

    def __call__(self, mat):
        def inv(dst, src):
            for i in range(len(dst)):
                eps = g.norm2(mat * dst[i] - src[i]) ** 0.5
                nrm = g.norm2(src[i]) ** 0.5
                g.message(
                    f"Residuum for source {i}/{len(dst)}{self.tag}: {eps} (absolute) {eps/nrm} (relative)"
                )

        otype, grid, cb = None, None, None
        if isinstance(mat, g.matrix_operator):
            otype, grid, cb = mat.otype, mat.grid, mat.cb

        return g.matrix_operator(
            mat=inv,
            inv_mat=mat,
            otype=otype,
            accept_guess=(True, False),
            grid=grid,
            cb=cb,
            accept_list=True,
        )