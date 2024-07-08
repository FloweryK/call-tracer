import sys
import colorama
from colorama import Fore
from types import FrameType


def _get_frame_depth(frame: FrameType):
    depth = 0
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
        'name': class_name + function_name,
        'args': frame.f_locals
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
    # default filters
    DEFAULT_PATH_CUTS = ['site-packages']
    DEFAULT_PATH_FILTERS = ['frozen importlib']

    # configs
    max_depth = 4
    path_cuts = DEFAULT_PATH_CUTS
    path_filters = DEFAULT_PATH_FILTERS
    is_show_args = False

    # internal parameters
    prev_depth = None
    depth_offset = None
    
    # initialize colorama
    colorama.init()

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        sys.settrace(self.trace_function_calls)
        result = self.func(*args, **kwargs)
        sys.settrace(None)
        return result
    
    @classmethod
    def start(cls):
        # reset the parameters
        cls.prev_depth = None
        cls.depth_offset = None
        sys.settrace(cls.trace_function_calls)
    
    @classmethod
    def end(cls):
        # reset the parameters
        cls.prev_depth = None
        cls.depth_offset = None
        sys.settrace(None)
        
    
    @classmethod
    def set_max_depth(cls, max_depth):
        cls.max_depth = max_depth
    
    @classmethod
    def set_path_cuts(cls, path_cuts):
        cls.path_cuts = cls.DEFAULT_PATH_CUTS + path_cuts
    
    @classmethod
    def set_path_filters(cls, path_filters):
        cls.path_filters = cls.DEFAULT_PATH_FILTERS + path_filters

    @classmethod
    def set_show_args(cls, is_show_args):
        cls.is_show_args = is_show_args
    
    @staticmethod
    def trace_function_calls(frame: FrameType, event: str, arg):
        # only trace 'call' and 'return' events
        if event not in ('call', 'return'):
            return
        
        # caller and callee info
        callee = _get_frame_info(frame)
        caller = _get_frame_info(frame.f_back)

        # filter by filename
        if any((filter_str in caller['path'] or filter_str in callee['path']) for filter_str in tracer.path_filters):
            return

        # calculate callee's depth
        depth = _get_frame_depth(frame)
        if tracer.prev_depth is not None and abs(depth - tracer.prev_depth) > 1:
            return
        tracer.prev_depth = depth

        # adjust depth with offset
        if tracer.depth_offset is None:
            tracer.depth_offset = depth
        depth -= tracer.depth_offset

        # print
        if depth <= tracer.max_depth:
            is_parent_call = _is_parent_method_call(frame)

            if callee['name'] != 'tracer.end':
                print(tracer._format_trace_output(depth, event, caller, callee, is_parent_call))
        
        return tracer.trace_function_calls
    
    @staticmethod
    def _shorten_path(path):
        for path_cut in tracer.path_cuts:
            parts = path.split(path_cut)[1:]
            if parts:
                path = ''.join(parts)
        return path
    
    @staticmethod
    def _format_trace_output(depth, event, caller, callee, is_parent_call):
        # call information
        text = f"{str(depth).rjust(3)} " + '|   ' * depth
        if depth != 0:
            text += f"{Fore.YELLOW}line {caller['line']}{Fore.RESET}"
            text += f" {'=> ' if event == 'call' else '<= '}"
        text += f"{Fore.CYAN}{event.upper().ljust(6)}{Fore.RESET}"
        text += f" ({tracer._shorten_path(callee['path'])} {Fore.YELLOW}line {callee['line']}{Fore.RESET}) {Fore.GREEN}{callee['name']}{Fore.RESET}"
        if is_parent_call:
            text += f" {Fore.MAGENTA}[parent call]{Fore.RESET}"
        
        # args information (call event only)
        if tracer.is_show_args and (event == 'call'):
            for arg, value in callee['args'].items():
                if arg in ('self', 'cls') or isinstance(value, type):
                    continue
                text += "\n"
                text += f"{str('').rjust(3)} " + '|   ' * (depth+1)
                text += f"{Fore.MAGENTA}{arg}{Fore.RESET} = {value}"

        return text
