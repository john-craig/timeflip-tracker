import subprocess
from timeflip_tracker.logger import get_logger

def invoke_hook(hook, args):
    timeflip_logger = get_logger()
    timeflip_logger.info(f"Invoking hook '{hook}' with args {args}")

    hook_string = hook
    for arg in args:
        hook_string = f"{hook_string} '{arg}'"

    p = subprocess.run(hook_string, shell=True)

    if p.returncode:
        timeflip_logger.warning(f"Hook '{hook}' failed")
    