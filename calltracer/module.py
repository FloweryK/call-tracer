import sys
import pathlib
import colorama
from colorama import Fore
from types import FrameType


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
    DEFAULT_PATH_CUTS = [str(pathlib.Path().resolve()), 'site-packages']
    DEFAULT_PATH_FILTERS = ['frozen importlib']

    # configs
    max_depth = 4
    path_cuts = DEFAULT_PATH_CUTS
    path_filters = DEFAULT_PATH_FILTERS
    is_show_args = False

    history = []
    depth = 0
    step = 0

    def __init__(self, func):
        colorama.init()
        self.func = func

    def __call__(self, *args, **kwargs):
        # reset
        tracer.history = []
        tracer.depth = 0

        # trace
        sys.settrace(self.trace_function_calls)
        result = self.func(*args, **kwargs)
        sys.settrace(None)

        # print
        self._print()
        return result
    
    @classmethod
    def start(cls):
        # reset
        cls.history = []
        cls.depth = 0
        sys.settrace(cls.trace_function_calls)
    
    @classmethod
    def end(cls):
        sys.settrace(None)
        cls._print()
        
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
        # this statismethod should be a static method in order to be thrown into sys.settrace
        # only trace 'call' and 'return' events
        if event not in ('call', 'return'):
            return tracer.trace_function_calls
        
        # caller and callee info
        callee = _get_frame_info(frame)
        caller = _get_frame_info(frame.f_back)
        caller_caller = _get_frame_info(frame.f_back.f_back) if frame.f_back.f_back else None

        # filter by filename
        if any((filter_str in caller['path'] or filter_str in callee['path']) for filter_str in tracer.path_filters):
            return

        # adjust depth (for return)
        if event == 'return':
            tracer.depth -= 1

        if (callee['name'] != 'tracer.end') and (tracer.depth <= tracer.max_depth):
            if caller['name'] == 'tracer.__call__':
                tracer.history.append((tracer.step, tracer.depth, event, caller_caller, callee, _is_parent_method_call(frame)))
            else:
                tracer.history.append((tracer.step, tracer.depth, event, caller, callee, _is_parent_method_call(frame)))    
        
        # adjust depth (for call)
        if event == 'call':
            tracer.depth += 1
        
        # adjust step
        tracer.step += 1
        
        return tracer.trace_function_calls
    
    @staticmethod
    def _shorten_path(path):
        for path_cut in tracer.path_cuts:
            parts = path.split(path_cut)[1:]
            if parts:
                path = ''.join(parts)
        return path
    
    @staticmethod
    def _print():
        print('STEP DEPTH')

        step_prev = -1
        for step, depth, event, caller, callee, is_parent_call in tracer.history:
            if step_prev + 1 != step:
                print('...'.rjust(4))
            
            # depth
            text = f"{str(step).rjust(4)} {str(depth).rjust(5)} " + '|   ' * depth
            text += f"{Fore.CYAN}{event.upper().ljust(7)}{Fore.RESET}"

            # caller
            text += f" ({tracer._shorten_path(caller['path'])} {Fore.YELLOW}line {caller['line']}{Fore.RESET}) {Fore.GREEN}{caller['name']}{Fore.RESET}"

            # event 
            text += f" {'=>' if event == 'call' else '<='}"

            # callee
            text += f" ({tracer._shorten_path(callee['path'])} {Fore.YELLOW}line {callee['line']}{Fore.RESET}) {Fore.GREEN}{callee['name']}{Fore.RESET}"

            # parent call
            if is_parent_call:
                text += f" {Fore.MAGENTA}[parent method]{Fore.RESET}"

            # args information (call event only)
            if tracer.is_show_args and (event == 'call'):
                for arg, value in callee['args'].items():
                    if arg in ('self', 'cls') or isinstance(value, type):
                        continue
                    text += "\n"
                    text += f"{str('').rjust(3)} " + '|   ' * depth
                    text += f"{Fore.MAGENTA}{arg}{Fore.RESET} = {value}"

            # adjust depth for return
            if event == 'return':
                depth -= 1
            
            step_prev = step
            
            print(text)