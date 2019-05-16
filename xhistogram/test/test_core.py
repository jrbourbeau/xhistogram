import numpy as np

from itertools import combinations
import dask.array as dsa

from ..core import histogram
from .fixtures import empty_dask_array

import pytest


@pytest.mark.parametrize('block_size', [None, 1, 2])
def test_histogram_results_1d(block_size):
    nrows, ncols = 5, 20
    data = np.random.randn(nrows, ncols)
    bins = np.linspace(-4, 4, 10)

    h = histogram(data, bins=bins, axis=1, block_size=block_size)
    assert h.shape == (nrows, len(bins)-1)

    # make sure we get the same thing as histogram
    hist, _ = np.histogram(data, bins=bins)
    np.testing.assert_array_equal(hist, h.sum(axis=0))

    # now try with no axis
    h_na = histogram(data, bins=bins, block_size=block_size)
    np.testing.assert_array_equal(hist, h_na)


@pytest.mark.parametrize('block_size', [None, 1, 2])
def test_histogram_results_1d_weighted(block_size):
    nrows, ncols = 5, 20
    data = np.random.randn(nrows, ncols)
    bins = np.linspace(-4, 4, 10)
    h = histogram(data, bins=bins, axis=1, block_size=block_size)
    weights = 2*np.ones_like(data)
    h_w = histogram(data, bins=bins, axis=1, weights=weights,
                    block_size=block_size)
    np.testing.assert_array_equal(2*h, h_w)


@pytest.mark.skip(reason="Weight broadcasting on numpy arrays is not yet implemented")
@pytest.mark.parametrize('block_size', [None, 1, 2])
def test_histogram_results_1d_weighted_broadcasting(block_size):
    nrows, ncols = 5, 20
    data = np.random.randn(nrows, ncols)
    bins = np.linspace(-4, 4, 10)
    # try with array broadcasting - does it work? not yet
    # with this shape, the weight is different for each histogram but constant
    # for each entry along axis 0
    weights = 2*np.ones((1, ncols))
    h_w = histogram(data, bins=bins, axis=1, weights=weights,
                    block_size=block_size)
    np.testing.assert_array_equal(2*h, h_w)



def test_histogram_results_2d():
    nrows, ncols = 5, 20
    data_a = np.random.randn(nrows, ncols)
    data_b = np.random.randn(nrows, ncols)
    nbins_a = 9
    bins_a = np.linspace(-4, 4, nbins_a + 1)
    nbins_b = 10
    bins_b = np.linspace(-4, 4, nbins_b + 1)

    h = histogram(data_a, data_b, bins=[bins_a, bins_b])
    assert h.shape == (nbins_a, nbins_b)

    hist, _, _ = np.histogram2d(data_a.ravel(), data_b.ravel(),
                                bins=[bins_a, bins_b])
    np.testing.assert_array_equal(hist, h)


@pytest.mark.parametrize('block_size', [None, 5])
@pytest.mark.parametrize('use_dask', [False, True])
def test_histogram_shape(use_dask, block_size):
    """These tests just verify that arrays with the right shape come out.
    They don't verify correctness."""

    shape = 10, 15, 12, 20
    if use_dask:
        b = empty_dask_array(shape, chunks=(1,) + shape[1:])
    else:
        b = np.random.randn(*shape)
    bins = np.linspace(-4, 4, 27)

    # no axis
    c = histogram(b, bins=bins, block_size=block_size)
    assert c.shape == (len(bins) - 1,)
    # same thing
    for axis in [(0, 1, 2, 3), (0, 1, 3, 2), (3, 2, 1, 0), (3, 2, 0, 1)]:
        c = histogram(b, bins=bins, axis=axis)
        assert c.shape == (len(bins) - 1,)
        if use_dask:
            assert isinstance(c, dsa.Array)

    # scalar axis (check positive and negative)
    for axis in list(range(4)) + list(range(-1, -5, -1)):
        c = histogram(b, bins=bins, axis=axis, block_size=block_size)
        shape = list(b.shape)
        del shape[axis]
        expected_shape = tuple(shape) + (len(bins) - 1,)
        assert c.shape == expected_shape
        if use_dask:
            assert isinstance(c, dsa.Array)

    # two axes
    for i, j in combinations(range(4), 2):
        axis = (i, j)
        c = histogram(b, bins=bins, axis=axis, block_size=block_size)
        shape = list(b.shape)
        partial_shape = [shape[k] for k in range(b.ndim) if k not in axis]
        expected_shape = tuple(partial_shape) + (len(bins) - 1,)
        assert c.shape == expected_shape
        if use_dask:
            assert isinstance(c, dsa.Array)