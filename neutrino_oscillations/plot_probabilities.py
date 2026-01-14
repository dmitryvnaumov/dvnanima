import numpy as np
import matplotlib.pyplot as plt
from osc_prob import prob_row_x

def plot_probabilities_x(
    initial_flavor,
    x_grid,
    theta12, theta23, theta13, delta_cp,
    dm21, dm31_abs,
    ordering="NO",
):
    P = prob_row_x(
        initial_flavor, x_grid,
        theta12, theta23, theta13, delta_cp,
        dm21, dm31_abs, ordering
    )

    plt.figure(figsize=(8, 4))
    plt.plot(x_grid, P[:, 0], label=rf"$P_{{{initial_flavor}e}}$")
    plt.plot(x_grid, P[:, 1], label=rf"$P_{{{initial_flavor}\mu}}$")
    plt.plot(x_grid, P[:, 2], label=rf"$P_{{{initial_flavor}\tau}}$")

    plt.xlabel(r"$x = L / L_{\mathrm{osc}}^{21}$")
    plt.ylabel("Probability")
    plt.ylim(0, 1)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

# ----------------------------- demo -----------------------------

if __name__ == "__main__":

    th12 = np.deg2rad(33.0)
    th23 = np.deg2rad(45.0)
    th13 = np.deg2rad(8.6)
    dcp  = 0.0

    dm21    = 7.5e-5
    dm31abs = 2.5e-3

    x_grid = np.linspace(0.0, 3.0, 1200)  # show 3 slow periods

    plot_probabilities_x(
        "e",
        x_grid,
        th12, th23, th13, dcp,
        dm21, dm31abs,
        ordering="NO",
    )
