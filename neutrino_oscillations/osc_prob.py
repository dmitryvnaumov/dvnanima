import numpy as np

# ----------------------------- PMNS -----------------------------

def pmns_matrix(theta12, theta23, theta13, delta_cp):
    """
    PDG convention PMNS matrix (unitary).
    Angles in radians, delta_cp in radians.
    U has flavor rows (e, mu, tau) and mass columns (1,2,3):
        |να> = sum_i U_{αi} |νi>
    """
    s12, c12 = np.sin(theta12), np.cos(theta12)
    s23, c23 = np.sin(theta23), np.cos(theta23)
    s13, c13 = np.sin(theta13), np.cos(theta13)

    e_minus = np.exp(-1j * delta_cp)
    e_plus  = np.exp(+1j * delta_cp)

    U = np.array([
        [ c12*c13,                              s12*c13,                              s13*e_minus ],
        [-s12*c23 - c12*s23*s13*e_plus,         c12*c23 - s12*s23*s13*e_plus,         s23*c13     ],
        [ s12*s23 - c12*c23*s13*e_plus,        -c12*s23 - s12*c23*s13*e_plus,         c23*c13     ],
    ], dtype=complex)

    return U


# ----------------------- phases in x = L / Losc(21) ----------------------

def phases_from_x(x, dm21, dm31_abs, ordering="NO"):
    """
    Dimensionless variable:
        x = L / L_osc(21)
    where L_osc(21) = 4π E / Δm^2_21 (in natural units).
    In this variable, phases can be written (up to a common irrelevant phase):
        phi_1 = 0
        phi_2 = 2π x
        phi_3 = 2π x * (Δm^2_31 / Δm^2_21)   for NO
    For IO we choose m3^2 as reference (set to 0), consistent with ordering.

    Inputs:
      x        : float or array
      dm21     : Δm^2_21 > 0 (eV^2)
      dm31_abs : |Δm^2_31|  (eV^2)
      ordering : "NO" or "IO"

    Returns:
      phi : array shape (N,3) (or (3,) for scalar) with phases (phi1,phi2,phi3)
    """
    x = np.asarray(x, dtype=float)
    scalar_input = (x.ndim == 0)
    if scalar_input:
        x = x[None]

    r = dm31_abs / dm21  # ratio that drives "fast" oscillations

    if ordering == "NO":
        # m1^2=0, m2^2=dm21, m3^2=dm31
        m2_over_dm21 = np.array([0.0, 1.0, r], dtype=float)
    elif ordering == "IO":
        # choose m3^2=0, m1^2=dm31_abs, m2^2=dm31_abs+dm21
        m2_over_dm21 = np.array([r, r + 1.0, 0.0], dtype=float)
    else:
        raise ValueError("ordering must be 'NO' or 'IO'")

    phi = 2.0 * np.pi * np.outer(x, m2_over_dm21)  # (N,3)

    return phi[0] if scalar_input else phi


# ------------------------ probabilities -------------------------

_FLAV = {"e": 0, "mu": 1, "tau": 2}

def prob_matrix_3fl_x(
    x,
    theta12, theta23, theta13, delta_cp,
    dm21, dm31_abs,
    ordering="NO",
):
    """
    Full 3x3 probability matrix P_{alpha->beta}(x) in terms of:
        x = L / L_osc(21)

    Inputs:
      x        : float or array (dimensionless)
      dm21     : Δm^2_21 > 0 (eV^2)
      dm31_abs : |Δm^2_31|  (eV^2)
      ordering : "NO" or "IO"

    Output:
      P : shape (N,3,3) if x is array, else (3,3)
          indices are (alpha, beta).
    """
    x = np.asarray(x, dtype=float)
    scalar_input = (x.ndim == 0)
    if scalar_input:
        x = x[None]

    U = pmns_matrix(theta12, theta23, theta13, delta_cp)
    phi = phases_from_x(x, dm21, dm31_abs, ordering=ordering)  # (N,3)
    phase = np.exp(-1j * phi)

    N = x.shape[0]
    A = np.zeros((N, 3, 3), dtype=complex)

    # A_{alpha->beta} = sum_i U_{beta i} U^*_{alpha i} e^{-i phi_i}
    for i in range(3):
        outer = np.outer(U[:, i], np.conjugate(U[:, i]))  # beta, alpha
        A += phase[:, i][:, None, None] * outer.T[None, :, :]

    P = (np.abs(A) ** 2).real

    return P[0] if scalar_input else P


def prob_row_x(
    initial_flavor,
    x,
    theta12, theta23, theta13, delta_cp,
    dm21, dm31_abs,
    ordering="NO",
):
    """
    Return row (P_{alpha e}, P_{alpha mu}, P_{alpha tau}) for chosen initial alpha.
    Output shape: (N,3) or (3,) for scalar x.
    """
    alpha = _FLAV[initial_flavor]
    P = prob_matrix_3fl_x(
        x, theta12, theta23, theta13, delta_cp,
        dm21, dm31_abs, ordering
    )
    return P[alpha, :] if P.ndim == 2 else P[:, alpha, :]


# --------------------------- sanity checks ---------------------------

def sanity_checks_x():
    th12 = np.deg2rad(33.0)
    th23 = np.deg2rad(45.0)
    th13 = np.deg2rad(8.6)
    dcp  = 0.0

    dm21    = 7.5e-5
    dm31abs = 2.5e-3

    xs = np.linspace(0.0, 5.0, 400)  # 5 periods of the slow (21) scale

    P = prob_matrix_3fl_x(xs, th12, th23, th13, dcp, dm21, dm31abs, ordering="NO")

    # Row sums
    assert np.allclose(P.sum(axis=2), 1.0, atol=1e-10), "Row sums not 1."
    # Bounds
    assert np.all(P >= -1e-12) and np.all(P <= 1.0 + 1e-12), "Out of [0,1]."
    # Identity at x=0
    P0 = prob_matrix_3fl_x(0.0, th12, th23, th13, dcp, dm21, dm31abs, ordering="NO")
    assert np.allclose(P0, np.eye(3), atol=1e-12), "P(x=0) should be identity."

    print("Sanity checks in x: OK")




# ----------------------------- demo -----------------------------

if __name__ == "__main__":
    sanity_checks_x()
    
__all__ = [
    "pmns_matrix",
    "phases_from_x",
    "prob_matrix_3fl_x",
    "prob_row_x",
    "sanity_checks_x",
]
