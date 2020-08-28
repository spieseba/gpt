/*
    GPT - Grid Python Toolkit
    Copyright (C) 2020  Christoph Lehner (christoph.lehner@ur.de, https://github.com/lehner/gpt)
                  2020  Daniel Richtmann (daniel.richtmann@ur.de)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/
template<typename vCoeff_t>
struct FinestLevelFineVec { };
template<>
struct FinestLevelFineVec<vComplexD> {
  typedef vSpinColourVectorD type;
};
template<>
struct FinestLevelFineVec<vComplexF> {
  typedef vSpinColourVectorF type;
};

template<typename vCoeff_t>
cgpt_fermion_operator_base* cgpt_create_coarsenedmatrix(PyObject* args) {

  auto grid_c = get_pointer<GridCartesian>(args,"grid_c"); // should actually take an 'F_', and an 'U_' grid
  int make_hermitian = get_int(args,"make_hermitian");
  int level = get_int(args,"level"); // 0 = fine, increases with coarser levels
  int nbasis = get_int(args,"nbasis");

#define BASIS_SIZE(n) \
  if(n == nbasis) { \
    if(level == 0) { \
      typedef CoarsenedMatrix<typename FinestLevelFineVec<vCoeff_t>::type, iSinglet<vCoeff_t>, n> CMat; \
      auto cm = new CMat(*grid_c, make_hermitian); \
      for (int p=0; p<9; p++) { \
        auto l = get_pointer<cgpt_Lattice_base>(args,"A",p);\
        cm->A[p] = compatible<iMSinglet ##n<vCoeff_t>>(l)->l;  \
      } \
      return new cgpt_coarse_operator<CMat>(cm); \
    } else {                                                           \
      typedef CoarsenedMatrix<iVSinglet ## n<vCoeff_t>, iSinglet<vCoeff_t>, n> CMat; \
      auto cm = new CMat(*grid_c, make_hermitian); \
      for (int p=0; p<9; p++) { \
        auto l = get_pointer<cgpt_Lattice_base>(args,"A",p);\
        cm->A[p] = compatible<iMSinglet ##n<vCoeff_t>>(l)->l;  \
      } \
      return new cgpt_coarse_operator<CMat>(cm); \
      } \
    } else
#include "../basis_size.h"
#undef BASIS_SIZE
  { ERR("Unknown basis size %d", (int)nbasis); }
}
