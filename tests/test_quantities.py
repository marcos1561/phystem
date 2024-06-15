import unittest
import numpy as np

from phystem.data_utils import grids

class TestGrids(unittest.TestCase):
    def test_regular_coords(self):
        grid = grids.RegularGrid(
            length=20,
            height=10,
            num_cols=5,
            num_rows=10,
        )

        self.assertEqual(grid.cell_size, (4, 1))

        points = np.array([
            [-7, -4.4],
            [1, 1.1],
            [100, -0.5],
            [-100, -4.9],
            [-100, -100],
            [100, 100],
            [3, -2.5],
        ])

        expected = np.array([
            [0, 0],
            [2, 6],
            [5, 4],
            [-1, 0],
            [-1, -1],
            [5, 10],
            [3, 2],
        ])
        expected_filter = np.array([
            [0, 0],
            [2, 6],
            [3, 2],
        ])

        coords = grid.coords(points)
        filter_coords = grid.filter_coords(coords)
        print("coords", coords)
        print("filter_coords", filter_coords)

        self.assertTrue((expected == coords).all())
        self.assertTrue((expected_filter == filter_coords).all())