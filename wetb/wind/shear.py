'''
Created on 16/06/2014

@author: MMPE
'''

from scipy.optimize.optimize import fmin
import numpy as np


def _z_u(z_u_lst):
    z = np.array([z for z, _ in z_u_lst])
    u = np.array([np.mean(np.array([u])[:]) for _, u in z_u_lst])
    return z, u

def power_shear(alpha, z_ref, u_ref, z):
    """Power shear

    Parameters
    ----------
    alpha : int or float
        The alpha shear parameter
    z_ref : int or float
        The reference height
    z : int, float or array_like
        The heights of interest
    u_ref : int or float
        The wind speed of the reference height

    Returns
    -------
    power_shear : array-like
        Wind speeds at height z

    Excample
    --------
    >>> power_shear(.5, 70, [20,50,70], 9)
    [ 4.81070235  7.60638829  9.        ]
    """
    return u_ref * (np.array(z) / z_ref) ** alpha


def fit_power_shear(z_u_lst):
    """Estimate power shear parameter, alpha, from the mean wind at hub height and one additional height

    Parameters
    ----------
    z_u_lst : [(z_ref, u_z_ref), (z1, u_z1),...]
        - z_ref: Reference height\n
        - u_z_ref: Wind speeds or mean wind speed at z_ref
        - z1: another height
        - u_z1: Wind speeds or mean wind speeds at z1

    Returns
    -------
    alpha : float
        power shear parameter

    Excample
    --------
    >>> fit_power_shear([(85, 9.0), (21, 4.47118)])
    0.50036320835
    """
    z, u = _z_u(z_u_lst)
    z_hub, u_hub = z[0], u[0]
    alpha, _ = np.polyfit(np.log(z / z_hub), np.log(u / u_hub), 1)
    return alpha

def fit_power_shear_ref(z_u_lst, z_ref):
    """Estimate power shear parameter, alpha, from two or morea specific reference height using polynomial fit.

    Parameters
    ----------
    z_u_lst : [(z1, u_z1), (z2, u_z2),...]
        - z1: Some height
        - u_z1: Wind speeds or mean wind speed at z1
        - z2: another height
        - u_z2: Wind speeds or mean wind speeds at z2
    z_ref : float or int
        Reference height (hub height)

    Returns
    -------
    alpha : float
        power shear parameter
    u_ref : float
        Wind speed at reference height

    Excample
    --------
    >>> fit_power_shear_ref([(85, 8.88131), (21, 4.41832)],  87.13333)
    [ 0.49938238  8.99192568]
    """
    def shear_error(x, z_u_lst, z_ref):
        alpha, u_ref = x
        return np.sum([(np.mean(u) - u_ref * (z / z_ref) ** alpha) ** 2 for z, u in z_u_lst])
    return fmin(shear_error, (.1, 10), (z_u_lst, z_ref), disp=False)



def log_shear(u_star, z0, z, Obukhov_length=None):
    """logarithmic shear

    Parameters
    ----------
    u_star : int or float
        Friction velocity
    z0 : int or float
        Surface roughness [m]
    z : int, float or array_like
        The heights of interest

    Returns
    -------
    log_shear : array-like
        Wind speeds at height z

    Excample
    --------
    >>> log_shear(1, 10, [20, 50, 70])
    [ 1.73286795  4.02359478  4.86477537]
    """
    K = 0.4  # von Karmans constant
    if Obukhov_length is None:
        return u_star / K * (np.log(np.array(z) / z0))
    else:
        return u_star / K * (np.log(z / z0) - stability_term(z, z0, Obukhov_length))

def stability_term(z, z0, L):
    """Calculate the stability term for the log shear

    Not validated!!!
    """
    zL = z / L
    phi_us = lambda zL : (1 + 16 * np.abs(zL)) ** (-1 / 4)  #unstable
    phi_s = lambda zL : 1 + 5 * zL  # stable
    phi = np.zeros_like(zL) + np.nan

    for m, f in [(((-2 <= zL) & (zL <= 0)), phi_us), (((0 < zL) & (zL <= 1)), phi_s)]:
        phi[m] = f(zL[m])
    f = L / z * (1 - phi)
    psi = np.cumsum(np.r_[0, (f[1:] + f[:-1]) / 2 * np.diff(z / L)])
    return psi


def fit_log_shear(z_u_lst):
    """Estimate log shear parameter, u_star and z0

    Parameters
    ----------
    z_u_lst : [(z1, u_z1), (z2, u_z2),...]
        - z1: Some height
        - u_z1: Wind speeds or mean wind speed at z1
        - z2: another height
        - u_z2: Wind speeds or mean wind speeds at z2

    Returns
    -------
    u_star : float
        friction velocity
    z0 : float
        Surface roughness [m]

    Excample
    --------
    >>> fit_log_shear([(85, 8.88131), (21, 4.41832)],  87.13333)
    [ 0.49938238  8.99192568]
    """
#    def shear_error(x, z_u_lst):
#        u_star, z0 = x
#        return np.sum([(np.mean(u) - log_shear(u_star, z0, z)) ** 2 for z, u in z_u_lst])
#    return fmin(shear_error, (1, 1), (z_u_lst,), disp=False)
    z, U = _z_u(z_u_lst)
    a, b = np.polyfit(np.log(z), U, 1)
    kappa = 0.4
    return a * kappa, np.exp(-b / a)  #, sum((U - (a * np.log(z) + b)) ** 2)

