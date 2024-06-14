import pytest
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

    @tracer
    def sample_function():
        def nested_function():
            pass
        nested_function()

    # manually check
    sample_function()


def test_set_path_cuts():
    tracer.set_path_cuts(['test_path'])
    assert 'test_path' in tracer.path_cuts


def test_set_path_filters():
    tracer.set_path_filters(['test_path'])
    assert 'test_path' in tracer.path_filters


if __name__ == '__main__':
    pytest.main()