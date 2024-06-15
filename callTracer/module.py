import os
import sys
import colorama
from colorama import Fore
from types import FrameType


def _get_frame_depth(frame: FrameType):
    depth = -2
    current_frame = frame
    while current_frame.f_back:
        current_frame = current_frame.f_back
        depth += 1
    return depth


def _get_frame_info(frame: FrameType):
    # get class name if exists
    class_name = ''
    if 'self' in frame.f_locals and frame.f_locals['self'] is not None:
        class_name = frame.f_locals['self'].__class__.__name__ + '.'
    elif 'cls' in frame.f_locals and frame.f_locals['cls'] is not None:
        cls = frame.f_locals['cls']
        if hasattr(cls, '__name__'):
            class_name = cls.__name__ + '.'
    
    # get function name
    function_name = frame.f_code.co_name
    
    return {
        'path': frame.f_code.co_filename,
        'line': frame.f_lineno,
        'name': class_name + function_name
    }


def _is_parent_method_call(frame: FrameType):
    if 'self' in frame.f_locals:
        self_instance = frame.f_locals['self']
        current_class = self_instance.__class__
        for base_class in current_class.__bases__:
            if hasattr(base_class, frame.f_code.co_name):
                return True
    return False


class tracer:
    # configs
    max_depth = 4
    path_cuts = []
    path_filters = []

    # internal parameters
    prev_depth = -1
    depth_offset = -1

    # default filters
    DEFAULT_PATH_CUTS = []
    DEFAULT_PATH_FILTERS = ['frozen importlib']

    def __init__(self, func):
        colorama.init()
        self.func = func

    def __call__(self, *args, **kwargs):
        sys.settrace(self.trace_function_calls)
        result = self.func(*args, **kwargs)
        sys.settrace(None)
        return result
    
    @classmethod
    def set_max_depth(cls, max_depth):
        cls.max_depth = max_depth
    
    @classmethod
    def set_path_cuts(cls, path_cuts):
        cls.path_cuts = cls.DEFAULT_PATH_CUTS + path_cuts
    
    @classmethod
    def set_path_filters(cls, path_filters):
        cls.path_filters = cls.DEFAULT_PATH_FILTERS + path_filters
    
    def trace_function_calls(self, frame: FrameType, event: str, _):
        # only trace 'call' and 'return' events
        if event not in ('call', 'return'):
            return
        
        # caller and callee info
        callee = _get_frame_info(frame)
        caller = _get_frame_info(frame.f_back)

        # filter by filename
        if any((filter_str in caller['path'] or filter_str in callee['path']) for filter_str in self.path_filters):
            return

        # calculate callee's depth
        depth = _get_frame_depth(frame)
        if depth < 0: 
            return
        if self.prev_depth != -1 and abs(depth - self.prev_depth) > 1:
            return
        self.prev_depth = depth

        # adjust depth with offset
        if self.depth_offset == -1:
            self.depth_offset = depth
        depth -= self.depth_offset

        # print
        if depth <= self.max_depth:
            is_parent_call = _is_parent_method_call(frame)
            print(self._format_trace_output(depth, event, caller, callee, is_parent_call))
        
        return self.trace_function_calls
    
    def _shorten_path(self, path):
        for path_cut in self.path_cuts:
            parts = path.split(os.path.sep + path_cut + os.path.sep)[1:]
            if parts:
                path = ''.join(parts)
        return path
    
    def _format_trace_output(self, depth, event, caller, callee, is_parent_call):
        text = f"{str(depth).rjust(3)} " + '|   ' * depth
        text += f"{Fore.CYAN}{event.upper().ljust(6)}{Fore.RESET}"
        text += f" ({self._shorten_path(caller['path'])} {Fore.YELLOW}line {caller['line']}{Fore.RESET}) {Fore.GREEN}{caller['name']}{Fore.RESET}"
        text += f" {' => ' if event == 'call' else ' <= '}"
        text += f" ({self._shorten_path(callee['path'])} {Fore.YELLOW}line {callee['line']}{Fore.RESET}) {Fore.GREEN}{callee['name']}{Fore.RESET}"
        if is_parent_call:
            text += f" {Fore.MAGENTA}[parent call]{Fore.RESET}"
        return text
    