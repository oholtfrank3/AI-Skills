"""
Shared publication style for a manuscript figure set (Kretchmer group).
Import and call `apply()` at the top of every figure script so the whole set is
visually consistent (serif fonts, colour-blind-safe palette, inward ticks, 300 dpi).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# colour-blind-safe (Wong/Okabe-Ito); use these consistently across all figures
C = {
    'blue':   '#0072B2',
    'orange': '#D55E00',
    'green':  '#009E73',
    'pink':   '#CC79A7',
    'sky':    '#56B4E9',
    'yellow': '#E69F00',
    'grey':   '#666666',
}
# ordered cycle for multi-trace plots
CYCLE = [C['blue'], C['orange'], C['green'], C['pink'], C['sky'], C['yellow']]


def apply():
    plt.rcParams.update({
        'font.family': 'serif', 'font.serif': ['DejaVu Serif'],
        'mathtext.fontset': 'dejavuserif',
        'font.size': 11, 'axes.labelsize': 12, 'axes.titlesize': 12,
        'xtick.labelsize': 10, 'ytick.labelsize': 10, 'legend.fontsize': 9.5,
        'axes.linewidth': 0.9, 'axes.labelpad': 4,
        'xtick.direction': 'in', 'ytick.direction': 'in',
        'xtick.top': True, 'ytick.right': True,
        'xtick.major.size': 4, 'ytick.major.size': 4,
        'xtick.minor.size': 2.3, 'ytick.minor.size': 2.3,
        'xtick.minor.visible': True, 'ytick.minor.visible': True,
        'lines.linewidth': 1.7, 'legend.frameon': False,
        'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
    })


def panel_tag(ax, tag, loc='upper left', **kw):
    """Bold (a)/(b)... panel label in axis corner."""
    x, y, ha, va = {
        'upper left':  (0.03, 0.95, 'left', 'top'),
        'upper right': (0.97, 0.95, 'right', 'top'),
        'lower left':  (0.03, 0.05, 'left', 'bottom'),
        'lower right': (0.97, 0.05, 'right', 'bottom'),
    }[loc]
    ax.text(x, y, tag, transform=ax.transAxes, fontweight='bold',
            ha=ha, va=va, **kw)


def save(fig, stem, here):
    import os
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(here, f'{stem}.{ext}'))
    print(f"  wrote {stem}.{{pdf,png}}")
