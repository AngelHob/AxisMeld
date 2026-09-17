# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure weight planning contracts; runnable without Blender or a scene."""

from copy import deepcopy
import importlib
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))


class SkinWeightPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.api = importlib.import_module('axismeld.skin_weight_plan')
        except ModuleNotFoundError as error:
            if error.name != 'axismeld.skin_weight_plan':
                raise
            cls.api = None

    def setUp(self):
        self.assertIsNotNone(self.api, 'Pure skin weight planner is missing')

    def plan(self, vertices, deform_groups, locked_groups=(), **options):
        return self.api.plan_weights(vertices, deform_groups, locked_groups, **options)

    def test_normalize_scales_positive_deform_weights_per_vertex(self):
        result = self.plan({4: {1: 0.125, 2: 0.375}, 9: {1: 0.8}}, {1, 2})
        self.assertEqual(result, {
            'changes': {4: {1: 0.25, 2: 0.75}, 9: {1: 1.0}},
            'zero_vertices': 0, 'changed_vertices': 2,
        })

    def test_normalize_preserves_locked_values_and_remaining_proportions(self):
        result = self.plan({0: {1: 0.25, 2: 0.1, 3: 0.2}}, {1, 2, 3}, {1})
        self.assertEqual(set(result['changes'][0]), {2, 3})
        self.assertAlmostEqual(result['changes'][0][2], 0.25)
        self.assertAlmostEqual(result['changes'][0][3], 0.5)

    def test_caller_can_merge_permanent_and_active_locks(self):
        result = self.plan({0: {1: 0.25, 2: 0.25, 3: 0.1}}, {1, 2, 3}, {1, 2})
        self.assertEqual(result['changes'], {0: {3: 0.5}})

    def test_normalize_never_changes_non_deform_groups(self):
        result = self.plan({0: {1: 0.2, 99: 0.9}}, {1}, {99})
        self.assertEqual(result['changes'], {0: {1: 1.0}})

    def test_normalize_preserves_zero_members_without_creating_influences(self):
        result = self.plan({0: {1: 0.0, 2: 0.2}}, {1, 2, 3})
        self.assertEqual(result['changes'], {0: {2: 1.0}})

    def test_zero_deform_vertices_are_unchanged_and_counted(self):
        result = self.plan({0: {}, 1: {1: 0.0}, 2: {99: 0.9}}, {1, 2})
        self.assertEqual(result, {'changes': {}, 'zero_vertices': 3, 'changed_vertices': 0})

    def test_normalized_vertices_do_not_create_changes(self):
        result = self.plan({0: {1: 0.25, 2: 0.75}, 1: {1: 1.0}}, {1, 2})
        self.assertEqual(result, {'changes': {}, 'zero_vertices': 0, 'changed_vertices': 0})

    def test_float32_roundtrip_without_actual_weight_change_is_a_noop(self):
        rna_weights = {
            group: struct.unpack('f', struct.pack('f', weight))[0]
            for group, weight in enumerate((0.2, 0.6, 0.2))
        }
        result = self.plan({0: rna_weights, 1: {0: 1.0}}, {0, 1, 2})
        self.assertEqual(result, {'changes': {}, 'zero_vertices': 0, 'changed_vertices': 0})

    def test_changed_weights_use_blender_float32_storage_precision(self):
        result = self.plan({0: {1: 0.2, 2: 0.3}}, {1, 2})
        self.assertEqual(result['changes'], {0: {
            1: 0.4000000059604645, 2: 0.6000000238418579,
        }})

    def test_lock_sum_one_zeroes_only_unlocked_positive_weights(self):
        result = self.plan({0: {1: 1.0, 2: 0.2, 3: 0.0}}, {1, 2, 3}, {1})
        self.assertEqual(result['changes'], {0: {2: 0.0}})

    def test_lock_sum_greater_than_one_rejects_normalize(self):
        with self.assertRaises(ValueError):
            self.plan({0: {1: 0.7, 2: 0.4, 3: 0.2}}, {1, 2, 3}, {1, 2})

    def test_locked_nonzero_vertex_without_distributable_weights_is_rejected(self):
        with self.assertRaises(ValueError):
            self.plan({0: {1: 0.3, 2: 0.0}}, {1, 2}, {1})

    def test_float32_locked_sum_roundoff_within_tolerance_is_accepted(self):
        for locked_weight in (0.4999998, 0.5000002):
            with self.subTest(locked_weight=locked_weight):
                result = self.plan({0: {1: locked_weight, 2: locked_weight}}, {1, 2}, {1, 2})
                self.assertEqual(result['changes'], {})
                self.assertEqual(result['zero_vertices'], 0)

    def test_float32_tolerance_does_not_accept_material_lock_sum_errors(self):
        for locked_weight in (0.499999, 0.500001):
            with self.subTest(locked_weight=locked_weight), self.assertRaises(ValueError):
                self.plan({0: {1: locked_weight, 2: locked_weight}}, {1, 2}, {1, 2})

    def test_roundoff_over_one_does_not_generate_negative_weights(self):
        result = self.plan({0: {1: 0.5000002, 2: 0.5000002, 3: 0.2}}, {1, 2, 3}, {1, 2})
        self.assertEqual(result['changes'], {0: {3: 0.0}})

    def test_tiny_positive_weights_are_normalized_without_underflow(self):
        result = self.plan({0: {1: 1e-320, 2: 1e-320}}, {1, 2})
        self.assertEqual(result['changes'], {0: {1: 0.5, 2: 0.5}})

    def test_prune_uses_strict_threshold_and_retains_equality(self):
        result = self.plan({0: {1: 0.009, 2: 0.01, 3: 0.5}}, {1, 2, 3},
                           operation='PRUNE', normalize_after=False)
        self.assertEqual(result['changes'], {0: {1: None}})

    def test_prune_default_renormalizes_remaining_weights(self):
        result = self.plan({0: {1: 0.009, 2: 0.2, 3: 0.6}}, {1, 2, 3}, operation='PRUNE')
        self.assertEqual(set(result['changes'][0]), {1, 2, 3})
        self.assertIsNone(result['changes'][0][1])
        self.assertAlmostEqual(result['changes'][0][2], 0.25)
        self.assertAlmostEqual(result['changes'][0][3], 0.75)

    def test_prune_never_removes_locked_or_non_deform_members(self):
        result = self.plan({0: {1: 0.001, 2: 0.002, 99: 0.003}}, {1, 2}, {1},
                           operation='PRUNE', normalize_after=False)
        self.assertEqual(result['changes'], {0: {2: None}})

    def test_prune_keeps_strongest_true_bone_even_when_unrelated_group_is_larger(self):
        result = self.plan({0: {1: 0.003, 2: 0.005, 99: 0.9}}, {1, 2}, operation='PRUNE')
        self.assertEqual(result['changes'], {0: {1: None, 2: 1.0}})

    def test_prune_strongest_tie_uses_smallest_group_index(self):
        result = self.plan({0: {8: 0.003, 3: 0.003, 5: 0.003}}, {8, 3, 5},
                           operation='PRUNE', normalize_after=False)
        self.assertEqual(result['changes'], {0: {8: None, 5: None}})

    def test_locked_positive_weight_makes_extra_strongest_protection_unnecessary(self):
        result = self.plan({0: {1: 0.001, 2: 0.008}}, {1, 2}, {1},
                           operation='PRUNE', normalize_after=False)
        self.assertEqual(result['changes'], {0: {2: None}})

    def test_locked_zero_weight_does_not_replace_last_positive_influence(self):
        result = self.plan({0: {1: 0.0, 2: 0.003, 3: 0.002}}, {1, 2, 3}, {1},
                           operation='PRUNE', normalize_after=False)
        self.assertEqual(result['changes'], {0: {3: None}})

    def test_prune_can_explicitly_remove_all_positive_influences(self):
        result = self.plan({0: {1: 0.003, 2: 0.005, 99: 0.9}}, {1, 2},
                           operation='PRUNE', keep_strongest=False)
        self.assertEqual(result, {
            'changes': {0: {1: None, 2: None}}, 'zero_vertices': 1, 'changed_vertices': 1,
        })

    def test_prune_leaves_original_zero_sum_vertices_unchanged(self):
        result = self.plan({0: {1: 0.0, 2: 0.0, 99: 0.9}}, {1, 2}, operation='PRUNE')
        self.assertEqual(result, {'changes': {}, 'zero_vertices': 1, 'changed_vertices': 0})

    def test_prune_removes_zero_members_of_positive_vertices(self):
        result = self.plan({0: {1: 0.0, 2: 1.0}}, {1, 2}, operation='PRUNE')
        self.assertEqual(result['changes'], {0: {1: None}})

    def test_prune_threshold_zero_and_one_are_valid(self):
        vertices = {0: {1: 0.0, 2: 0.3, 3: 1.0}}
        result = self.plan(vertices, {1, 2, 3}, operation='PRUNE', threshold=0, normalize_after=False)
        self.assertEqual(result['changes'], {})
        result = self.plan(vertices, {1, 2, 3}, operation='PRUNE', threshold=1, normalize_after=False)
        self.assertEqual(result['changes'], {0: {1: None, 2: None}})

    def test_prune_without_normalization_does_not_enforce_lock_sum(self):
        result = self.plan({0: {1: 0.7, 2: 0.4, 3: 0.003}}, {1, 2, 3}, {1, 2},
                           operation='PRUNE', normalize_after=False)
        self.assertEqual(result['changes'], {0: {3: None}})

    def test_prune_with_normalization_rejects_undistributable_locked_remainder(self):
        with self.assertRaises(ValueError):
            self.plan({0: {1: 0.3, 2: 0.003}}, {1, 2}, {1}, operation='PRUNE')

    def test_valid_plan_does_not_mutate_or_alias_input(self):
        vertices = {0: {1: 0.003, 2: 0.5, 99: 0.8}}
        before = deepcopy(vertices)
        result = self.plan(vertices, {1, 2}, operation='PRUNE')
        self.assertEqual(vertices, before)
        result['changes'][0][2] = 0.2
        self.assertEqual(vertices, before)

    def test_later_invalid_vertex_rejects_whole_batch_without_mutation(self):
        vertices = {0: {1: 0.1, 2: 0.1}, 1: {1: 0.3, 2: 0.0}}
        before = deepcopy(vertices)
        with self.assertRaises(ValueError):
            self.plan(vertices, {1, 2}, {1})
        self.assertEqual(vertices, before)

    def test_invalid_weights_raise_value_error(self):
        for weight in (-0.1, 1.01, float('nan'), float('inf'), -float('inf'), '0.2', None, True):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                self.plan({0: {1: weight}}, {1})

    def test_invalid_vertex_or_group_indices_raise_value_error(self):
        for vertices, deform, locked in (
                ({-1: {1: 0.5}}, {1}, set()),
                ({'0': {1: 0.5}}, {1}, set()),
                ({True: {1: 0.5}}, {1}, set()),
                ({0: {-1: 0.5}}, {1}, set()),
                ({0: {1: 0.5}}, {'1'}, set()),
                ({0: {1: 0.5}}, {1}, {False}),
        ):
            with self.subTest(vertices=vertices, deform=deform, locked=locked), self.assertRaises(ValueError):
                self.plan(vertices, deform, locked)

    def test_invalid_containers_raise_value_error(self):
        for vertices, deform, locked in ((None, {1}, set()), ([], {1}, set()),
                                         ({0: []}, {1}, set()), ({0: {}}, None, set()),
                                         ({0: {}}, {1}, None)):
            with self.subTest(vertices=vertices, deform=deform, locked=locked), self.assertRaises(ValueError):
                self.plan(vertices, deform, locked)

    def test_invalid_options_raise_value_error(self):
        for options in ({'operation': 'CLEAN'}, {'operation': None}, {'threshold': -0.1},
                        {'threshold': 1.1}, {'threshold': float('nan')}, {'threshold': '0.1'},
                        {'threshold': True}, {'keep_strongest': 1}, {'normalize_after': None}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.plan({0: {1: 0.5}}, {1}, **options)

    def test_empty_target_or_deform_range_is_a_valid_noop(self):
        self.assertEqual(self.plan({}, {1}), {
            'changes': {}, 'zero_vertices': 0, 'changed_vertices': 0,
        })
        self.assertEqual(self.plan({0: {99: 0.7}}, set()), {
            'changes': {}, 'zero_vertices': 1, 'changed_vertices': 0,
        })


if __name__ == '__main__':
    unittest.main()
