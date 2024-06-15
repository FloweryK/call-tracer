import os
from callTracer import tracer


def test_tracer():
    @tracer
    def sample_function():
        pass

    # manually check
    sample_function()


def test_set_max_depth():
    tracer.set_max_depth(1)
    assert tracer.max_depth == 1


def test_set_path_cuts():
    tracer.set_path_cuts(['test_path'])
    assert 'test_path' in tracer.path_cuts


def test_set_path_filters():
    tracer.set_path_filters(['test_path'])
    assert 'test_path' in tracer.path_filters


def test_shorten_path():
    t = tracer(func=lambda x: x)
    t.set_path_cuts(path_cuts=['test_path'])
    assert 'test_path' not in t._shorten_path(os.path.join('path_1', 'test_path', 'path_2'))
