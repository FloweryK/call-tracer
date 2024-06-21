import re
import os
from colorama import Fore
from calltracer import tracer


def test_tracer_decorator(capsys):
    @tracer
    def function_depth_0():
        function_depth_1()

    def function_depth_1():
        function_depth_2()

    def function_depth_2():
        pass

    # capture stdout
    function_depth_0()
    captured = capsys.readouterr()
    assert re.search(r"^  0", captured.out) is not None


def test_tracer_starter(capsys):
    def function_depth_0():
        function_depth_1()

    def function_depth_1():
        function_depth_2()

    def function_depth_2():
        pass

    # capture stdout
    tracer.start()
    function_depth_0()
    captured = capsys.readouterr()
    tracer.end()

    assert re.search(r"^  0", captured.out) is not None


def test_set_max_depth(capsys):
    tracer.set_max_depth(1)
    assert tracer.max_depth == 1

    @tracer
    def function_depth_0():
        function_depth_1()

    def function_depth_1():
        function_depth_2()

    def function_depth_2():
        pass

    # capture stdout
    function_depth_0()
    captured = capsys.readouterr()
    assert re.search(r"^  0", captured.out) is not None
    assert re.search(r"  1 \|   line \d+ =>", captured.out) is not None
    assert re.search(r"  2 \|   \|   line \d+ =>", captured.out) is None

    # return to default
    tracer.set_max_depth(4)


def test_set_path_cuts():
    tracer.set_path_cuts(['test_path'])
    assert 'test_path' in tracer.path_cuts

    # return to default
    tracer.set_path_cuts([])


def test_set_path_filters():
    tracer.set_path_filters(['test_path'])
    assert 'test_path' in tracer.path_filters

    # return to default
    tracer.set_path_filters([])


def test_set_show_args():
    tracer.set_show_args(True)
    assert tracer.is_show_args == True

    # return to default
    tracer.set_show_args(False)


def test_shorten_path():
    t = tracer(func=lambda x: x)
    t.set_path_cuts(path_cuts=['test_path'])
    assert 'test_path' not in t._shorten_path(os.path.join('path_1', 'test_path', 'path_2'))