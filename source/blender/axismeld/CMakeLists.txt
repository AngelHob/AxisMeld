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
  intern/hotbox_menu.cc
  AXM_hotbox_menu.hh
  AXM_hotbox_state.hh
  AXM_identity.hh
  AXM_transform_axis.hh
)
set(LIB
)

blender_add_lib(bf_axismeld "${SRC}" "${INC}" "${INC_SYS}" "${LIB}")
add_library(bf::axismeld ALIAS bf_axismeld)

if(WITH_GTESTS)
  set(menu_fixture "${CMAKE_CURRENT_BINARY_DIR}/hotbox_menu_fixture.hh")
  add_custom_command(
    OUTPUT ${menu_fixture}
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/hotbox_menu_fixture.py ${menu_fixture}
    DEPENDS
      tests/hotbox_menu_fixture.py
      ${CMAKE_SOURCE_DIR}/scripts/modules/axismeld/hotbox_catalog.py
    VERBATIM
  )
  add_custom_target(axismeld_menu_fixture DEPENDS ${menu_fixture})
  list(APPEND INC ${CMAKE_CURRENT_BINARY_DIR})
  set(TEST_SRC
    tests/hotbox_menu_test.cc
    tests/hotbox_state_test.cc
    tests/identity_test.cc
    tests/transform_axis_test.cc
  )
  blender_add_test_suite_lib(axismeld "${TEST_SRC}" "${INC}" "${INC_SYS}" "bf::axismeld")
  if(WITH_TESTS_SINGLE_BINARY)
    add_dependencies(axismeld_tests axismeld_menu_fixture)
  else()
    add_dependencies(axismeld_hotbox_menu_test axismeld_menu_fixture)
  endif()
endif()
