"""
This is an example configuration file for pdb++.

Put it into ~/.pdbrc.py to use it.
"""

import pdbpp

from pygments.styles import get_style_by_name


class Config(pdbpp.DefaultConfig):
    # prompt = "(Pdb++) "
    sticky_by_default = True  # shows full code context at every step

    use_pygments = True
    pygments_formatter_class = "pygments.formatters.TerminalTrueColorFormatter"
    # get available style names with the snippet below
    pygments_formatter_kwargs = {"style": get_style_by_name("gruvbox-dark")}

    editor = "vim"

    def setup(self, pdb):
        # make 'l' an alias to 'longlist'
        Pdb = pdb.__class__
        Pdb.do_l = Pdb.do_longlist
        Pdb.do_st = Pdb.do_sticky


if __name__ == "__main__":
    from pygments.styles import get_all_styles

    all_styles = get_all_styles()
    print(list(all_styles))
