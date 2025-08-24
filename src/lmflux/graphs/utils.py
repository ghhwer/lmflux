try:
    from IPython.display import Markdown, display, clear_output # type: ignore
    from IPython import get_ipython # type: ignore
    _ipython = get_ipython()
    IPYTHON_AVAILABLE = _ipython is not None
except Exception:  # ImportError or any other failure
    IPYTHON_AVAILABLE = False

def show_markdown(markdown, flush=False):
    """
    Render any Markdown Text in ipython
    """
    if not IPYTHON_AVAILABLE:
        print(markdown, flush=flush)
    clear_output(True)
    display(Markdown(markdown))

