"""
Stratoptic - Visualization Module
===================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
Version     : 0.1.0

Two rendering modes:
  1. Scientific (Matplotlib) — publication-quality static figures
  2. Interactive (Plotly)    — zoomable, hoverable, exportable HTML
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional
from tmm import TMMResult, Structure


# =============================================================================
# STYLE CONSTANTS
# =============================================================================

STRATOPTIC_COLORS = {
    "R": "#E63946",   # reflectance  — red
    "T": "#2196F3",   # transmittance — blue
    "A": "#4CAF50",   # absorbance   — green
    "bg": "#0D1B2A",  # dark background
    "grid": "#1E3A5F",
    "text": "#E0E0E0",
    "accent": "#00B4D8",
}

PUBLICATION_COLORS = {
    "R": "#C0392B",
    "T": "#2980B9",
    "A": "#27AE60",
}


# =============================================================================
# SCIENTIFIC MODE — Matplotlib
# =============================================================================

def plot_spectrum(
    result: TMMResult,
    structure: Optional[Structure] = None,
    show_all: bool = True,
    show_R: bool = True,
    show_T: bool = True,
    show_A: bool = True,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    style: str = "publication"   # "publication" | "dark"
) -> plt.Figure:
    """
    Plot R/T/A spectra — publication-quality static figure.

    Parameters
    ----------
    result     : TMMResult from TMMEngine.calculate()
    structure  : Structure object — used for auto-title if provided
    show_all   : if True, override show_R/T/A and show everything
    show_R/T/A : individual spectrum visibility
    title      : custom plot title
    save_path  : if provided, save figure to this path (e.g. 'spectrum.pdf')
    style      : 'publication' (white bg) | 'dark' (dark bg)

    Returns
    -------
    matplotlib Figure
    """
    if show_all:
        show_R = show_T = show_A = True

    # ── Style setup ──────────────────────────────────────────────────
    if style == "dark":
        plt.style.use("dark_background")
        colors = STRATOPTIC_COLORS
        bg_color  = "#0D1B2A"
        ax_color  = "#0F2133"
        txt_color = "#E0E0E0"
        grid_color = "#1E3A5F"
    else:
        plt.style.use("default")
        colors = PUBLICATION_COLORS
        bg_color  = "white"
        ax_color  = "white"
        txt_color = "black"
        grid_color = "#CCCCCC"

    # ── Figure setup ─────────────────────────────────────────────────
    n_plots = sum([show_R, show_T, show_A])
    if n_plots == 0:
        raise ValueError("At least one of show_R, show_T, show_A must be True.")

    fig = plt.figure(figsize=(10, 4 + 2 * (n_plots > 1)), facecolor=bg_color)

    if n_plots == 3:
        # Combined plot — all three on one axes
        ax = fig.add_subplot(111, facecolor=ax_color)
        axes = [ax]
        combined = True
    else:
        # Separate subplots
        fig, axes_arr = plt.subplots(
            n_plots, 1,
            figsize=(10, 3 * n_plots),
            facecolor=bg_color,
            sharex=True
        )
        axes = [axes_arr] if n_plots == 1 else list(axes_arr)
        for ax in axes:
            ax.set_facecolor(ax_color)
        combined = False

    wl = result.wavelengths
    ax_main = axes[0]

    # ── Plot spectra ──────────────────────────────────────────────────
    if combined:
        if show_R:
            ax_main.plot(wl, result.R * 100, color=colors["R"],
                         lw=2.0, label="Reflectance (R)")
        if show_T:
            ax_main.plot(wl, result.T * 100, color=colors["T"],
                         lw=2.0, label="Transmittance (T)")
        if show_A:
            ax_main.plot(wl, result.A * 100, color=colors["A"],
                         lw=2.0, label="Absorbance (A)")

        ax_main.set_ylabel("Intensity (%)", color=txt_color, fontsize=12)
        ax_main.set_ylim(-2, 102)
        ax_main.legend(
            loc="upper right", framealpha=0.2,
            labelcolor=txt_color, fontsize=10
        )
    else:
        plot_specs = []
        if show_R: plot_specs.append(("R", result.R, "Reflectance (R)"))
        if show_T: plot_specs.append(("T", result.T, "Transmittance (T)"))
        if show_A: plot_specs.append(("A", result.A, "Absorbance (A)"))

        for ax, (key, data, label) in zip(axes, plot_specs):
            ax.plot(wl, data * 100, color=colors[key], lw=2.0, label=label)
            ax.set_ylabel(f"{label} (%)", color=txt_color, fontsize=11)
            ax.set_ylim(-2, 102)
            ax.legend(loc="upper right", framealpha=0.2,
                      labelcolor=txt_color, fontsize=10)
            ax.tick_params(colors=txt_color)
            for spine in ax.spines.values():
                spine.set_edgecolor(grid_color)
            ax.grid(True, color=grid_color, alpha=0.5, linewidth=0.7)

    # ── Shared axis formatting ────────────────────────────────────────
    for ax in axes:
        ax.set_xlabel("Wavelength (nm)", color=txt_color, fontsize=12)
        ax.set_xlim(wl[0], wl[-1])
        ax.tick_params(colors=txt_color, labelsize=10)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.grid(True, color=grid_color, alpha=0.5, linewidth=0.7)
        ax.grid(True, which="minor", color=grid_color, alpha=0.2, linewidth=0.4)
        for spine in ax.spines.values():
            spine.set_edgecolor(grid_color)

    # ── Title ─────────────────────────────────────────────────────────
    if title is None:
        pol_label = result.polarization.upper()
        angle_str = f"{result.angle}°"
        if structure:
            layers_str = " / ".join(
                [structure.incident.name] +
                [f"{l.material.name}({l.thickness:.0f}nm)" for l in structure.layers] +
                [structure.substrate.name]
            )
            title = f"Stratoptic — {layers_str}\npolarization: {pol_label}  |  angle: {angle_str}"
        else:
            title = f"Stratoptic — TMM Spectrum\npolarization: {pol_label}  |  angle: {angle_str}"

    fig.suptitle(title, color=txt_color, fontsize=12, y=1.01, ha="center")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight",
                    facecolor=bg_color)
        print(f"  Saved: {save_path}")

    return fig


# =============================================================================
# INTERACTIVE MODE — Plotly
# =============================================================================

def plot_interactive(
    result: TMMResult,
    structure: Optional[Structure] = None,
    title: Optional[str] = None,
    save_html: Optional[str] = None,
    theme: str = "dark"   # "dark" | "light"
) -> go.Figure:
    """
    Interactive R/T/A spectrum with Plotly.

    Features: zoom, pan, hover values, toggle traces, PNG/SVG export.

    Parameters
    ----------
    result     : TMMResult
    structure  : Structure — used for auto-title
    title      : custom title
    save_html  : if provided, save as self-contained HTML file
    theme      : 'dark' | 'light'

    Returns
    -------
    plotly Figure (call .show() to display)
    """
    wl = result.wavelengths

    # ── Theme ────────────────────────────────────────────────────────
    if theme == "dark":
        template   = "plotly_dark"
        paper_bg   = "#0D1B2A"
        plot_bg    = "#0F2133"
        grid_color = "#1E3A5F"
        font_color = "#E0E0E0"
    else:
        template   = "plotly_white"
        paper_bg   = "white"
        plot_bg    = "#F8F9FA"
        grid_color = "#DDDDDD"
        font_color = "#222222"

    # ── Title ────────────────────────────────────────────────────────
    if title is None:
        pol_label = result.polarization.upper()
        if structure:
            layers_str = " / ".join(
                [structure.incident.name] +
                [f"{l.material.name}({l.thickness:.0f}nm)"
                 for l in structure.layers] +
                [structure.substrate.name]
            )
            title = (f"Stratoptic — {layers_str} | "
                     f"pol: {pol_label} | angle: {result.angle}°")
        else:
            title = (f"Stratoptic — TMM Spectrum | "
                     f"pol: {pol_label} | angle: {result.angle}°")

    # ── Traces ───────────────────────────────────────────────────────
    hover = (
        "<b>λ = %{x:.1f} nm</b><br>"
        "%{meta}: <b>%{y:.2f}%</b><extra></extra>"
    )

    traces = [
        go.Scatter(
            x=wl, y=result.R * 100,
            name="Reflectance (R)",
            meta="R",
            mode="lines",
            line=dict(color="#E63946", width=2.5),
            hovertemplate=hover,
            fill="tozeroy",
            fillcolor="rgba(230, 57, 70, 0.08)"
        ),
        go.Scatter(
            x=wl, y=result.T * 100,
            name="Transmittance (T)",
            meta="T",
            mode="lines",
            line=dict(color="#2196F3", width=2.5),
            hovertemplate=hover,
            fill="tozeroy",
            fillcolor="rgba(33, 150, 243, 0.08)"
        ),
        go.Scatter(
            x=wl, y=result.A * 100,
            name="Absorbance (A)",
            meta="A",
            mode="lines",
            line=dict(color="#4CAF50", width=2.5),
            hovertemplate=hover,
            fill="tozeroy",
            fillcolor="rgba(76, 175, 80, 0.08)"
        ),
    ]

    # ── Layout ───────────────────────────────────────────────────────
    layout = go.Layout(
        title=dict(
            text=title,
            font=dict(size=14, color=font_color),
            x=0.5, xanchor="center"
        ),
        template=template,
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(color=font_color, family="Arial"),
        xaxis=dict(
            title="Wavelength (nm)",
            gridcolor=grid_color,
            gridwidth=1,
            showline=True,
            linecolor=grid_color,
            mirror=True,
            range=[wl[0], wl[-1]],
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            title="Intensity (%)",
            gridcolor=grid_color,
            gridwidth=1,
            showline=True,
            linecolor=grid_color,
            mirror=True,
            range=[-2, 102],
            tickfont=dict(size=12),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0.2)",
            bordercolor=grid_color,
            borderwidth=1,
        ),
        hovermode="x unified",
        margin=dict(l=60, r=30, t=80, b=60),
        height=500,
    )

    fig = go.Figure(data=traces, layout=layout)

    # ── Export buttons ───────────────────────────────────────────────
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0, y=1.12,
                showactive=True,
                buttons=[
                    dict(label="All",
                         method="update",
                         args=[{"visible": [True, True, True]}]),
                    dict(label="R only",
                         method="update",
                         args=[{"visible": [True, False, False]}]),
                    dict(label="T only",
                         method="update",
                         args=[{"visible": [False, True, False]}]),
                    dict(label="A only",
                         method="update",
                         args=[{"visible": [False, False, True]}]),
                ],
            )
        ]
    )

    if save_html:
        fig.write_html(save_html, include_plotlyjs="cdn")
        print(f"  Saved interactive: {save_html}")

    return fig


# =============================================================================
# LAYER STACK DIAGRAM
# =============================================================================

def plot_stack(
    structure: Structure,
    style: str = "dark"
) -> plt.Figure:
    """
    Visual diagram of the thin film layer stack.

    Shows each layer as a colored bar with material name and thickness.

    Parameters
    ----------
    structure : Structure
    style     : 'dark' | 'publication'
    """
    if style == "dark":
        bg_color  = "#0D1B2A"
        ax_color  = "#0F2133"
        txt_color = "#E0E0E0"
        plt.style.use("dark_background")
    else:
        bg_color  = "white"
        ax_color  = "white"
        txt_color = "black"
        plt.style.use("default")

    layers = structure.layers
    n_layers = len(layers)

    # Assign colors by refractive index magnitude
    def layer_color(n_val):
        n_norm = min(max((abs(n_val) - 1.0) / 3.5, 0), 1)
        r = int(0 + n_norm * 0)
        g = int(100 + n_norm * 100)
        b = int(200 - n_norm * 150)
        return f"#{r:02X}{g:02X}{b:02X}"

    fig, ax = plt.subplots(figsize=(5, 2 + n_layers * 0.8),
                           facecolor=bg_color)
    ax.set_facecolor(ax_color)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, n_layers + 2)
    ax.axis("off")

    # Incident medium
    ax.text(0.5, n_layers + 1.5,
            f"↓  Incident: {structure.incident.name}  (n={structure.incident.n})",
            ha="center", va="center", color=txt_color, fontsize=10)

    # Layers
    for i, layer in enumerate(layers):
        y = n_layers - i
        color = layer_color(layer.material.n)
        rect = plt.Rectangle((0.05, y + 0.05), 0.9, 0.85,
                              color=color, alpha=0.85, zorder=2)
        ax.add_patch(rect)
        label = (f"{layer.material.name}   "
                 f"n={layer.material.n}  |  "
                 f"d={layer.thickness:.1f} nm")
        ax.text(0.5, y + 0.47, label,
                ha="center", va="center",
                color="white", fontsize=10, fontweight="bold", zorder=3)

    # Substrate
    rect_sub = plt.Rectangle((0.05, 0.05), 0.9, 0.85,
                              color="#334455", alpha=0.9, zorder=2)
    ax.add_patch(rect_sub)
    ax.text(0.5, 0.47,
            f"Substrate: {structure.substrate.name}  (n={structure.substrate.n})",
            ha="center", va="center",
            color=txt_color, fontsize=10, fontweight="bold", zorder=3)

    fig.suptitle("Stratoptic — Layer Stack",
                 color=txt_color, fontsize=13, y=1.01)
    plt.tight_layout()
    return fig
