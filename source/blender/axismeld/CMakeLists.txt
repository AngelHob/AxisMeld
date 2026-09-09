# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(INC
  PUBLIC .
)
set(INC_SYS
)
set(SRC
  intern/identity.cc
  AXM_hotbox_state.hh
  AXM_identity.hh
  AXM_transform_axis.hh
)
set(LIB
)

blender_add_lib(bf_axismeld "${SRC}" "${INC}" "${INC_SYS}" "${LIB}")
add_library(bf::axismeld ALIAS bf_axismeld)

if(WITH_GTESTS)
  set(TEST_SRC
    tests/hotbox_state_test.cc
    tests/identity_test.cc
    tests/transform_axis_test.cc
  )
  blender_add_test_suite_lib(axismeld "${TEST_SRC}" "${INC}" "${INC_SYS}" "bf::axismeld")
endif()
