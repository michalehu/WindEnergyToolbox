from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from future import standard_library
import wetb.fatigue_tools
from wetb.fatigue_tools.rainflowcounting.rainflowcount_IEA import peak_trough,\
    pair_range_amplitude_mean
from wetb.fatigue_tools.rainflowcounting import rainflowcount_IEA, compile_ext
import sys
import os
standard_library.install_aliases()
import numpy as np
non_compile_warning_shown = False


def check_signal(signal):
    # check input data validity
    if not type(signal).__name__ == 'ndarray':
        raise TypeError('signal must be ndarray, not: ' + type(signal).__name__)

    elif len(signal.shape) not in (1, 2):
        raise TypeError('signal must be 1D or 2D, not: ' + str(len(signal.shape)))

    if len(signal.shape) == 2:
        if signal.shape[1] > 1:
            raise TypeError('signal must have one column only, not: ' + str(signal.shape[1]))
    if np.min(signal) == np.max(signal):
        raise TypeError("Signal contains no variation")


def rainflow_windap(signal, levels=255., thresshold=(255 / 50)):
    global non_compile_warning_shown
    """Windap equivalent rainflow counting


    Calculate the amplitude and mean values of half cycles in signal

    This algorithms used by this routine is implemented directly as described in
    "Recommended Practices for Wind Turbine Testing - 3. Fatigue Loads", 2. edition 1990, Appendix A

    Parameters
    ----------
    Signal : array-like
        The raw signal

    levels : int, optional
        The signal is discretize into this number of levels.
        255 is equivalent to the implementation in Windap

    thresshold : int, optional
        Cycles smaller than this thresshold are ignored
        255/50 is equivalent to the implementation in Windap

    Returns
    -------
    ampl : array-like
        Peak to peak amplitudes of the half cycles

    mean : array-like
        Mean values of the half cycles


    Examples
    --------
    >>> signal = np.array([-2.0, 0.0, 1.0, 0.0, -3.0, 0.0, 5.0, 0.0, -1.0, 0.0, 3.0, 0.0, -4.0, 0.0, 4.0, 0.0, -2.0])
    >>> ampl, mean = rainflow_windap(signal)
    """
    check_signal(signal)
    # type <double> is required by <find_extreme> and <rainflow>
    signal = signal.astype(np.double)
    if np.all(np.isnan(signal)):
        return None
    offset = np.nanmin(signal)
    signal -= offset

    if rainflowcount_IEA.__file__.endswith('.py') and non_compile_warning_shown is False:
        non_compiled_warning()

    if np.nanmax(signal) > 0:
        gain = np.nanmax(signal) / levels
        signal = signal / gain
        signal = np.round(signal).astype(np.int)

        # If possible the module is compiled using cython otherwise the python implementation is used

        # Convert to list of local minima/maxima where difference > thresshold
        sig_ext = peak_trough(signal, thresshold)

        # rainflow count
        ampl_mean = pair_range_amplitude_mean(sig_ext)

        ampl_mean = np.array(ampl_mean)
        ampl_mean = np.round(ampl_mean / thresshold) * gain * thresshold
        ampl_mean[:, 1] += offset
        return ampl_mean.T


def rainflow_astm(signal):
    """Matlab equivalent rainflow counting

    Calculate the amplitude and mean values of half cycles in signal

    This implemementation is based on the c-implementation by Adam Nieslony found at
    the MATLAB Central File Exchange http://www.mathworks.com/matlabcentral/fileexchange/3026

    Parameters
    ----------
    Signal : array-like
        The raw signal

    Returns
    -------
    ampl : array-like
        peak to peak amplitudes of the half cycles (note that the matlab implementation
        uses peak amplitude instead of peak to peak)

    mean : array-like
        Mean values of the half cycles


    Examples
    --------
    >>> signal = np.array([-2.0, 0.0, 1.0, 0.0, -3.0, 0.0, 5.0, 0.0, -1.0, 0.0, 3.0, 0.0, -4.0, 0.0, 4.0, 0.0, -2.0])
    >>> ampl, mean = rainflow_astm(signal)
    """
    check_signal(signal)

    # type <double> is reuqired by <find_extreme> and <rainflow>
    signal = signal.astype(np.double)

    # Import find extremes and rainflow.
    # If possible the module is compiled using cython otherwise the python implementation is used
    from wetb.fatigue_tools.rainflowcounting import rainflowcount_astm
    from wetb.fatigue_tools.rainflowcounting.rainflowcount_astm import find_extremes, rainflowcount
    if rainflowcount_astm.__file__.endswith('.py') and non_compile_warning_shown is False:
        non_compiled_warning()
    # Remove points which is not local minimum/maximum
    sig_ext = find_extremes(signal)

    # rainflow count
    ampl_mean = np.array(rainflowcount(sig_ext))

    return np.array(ampl_mean).T


def non_compiled_warning():
    global non_compile_warning_shown
    compiler = ""
    import platform
    if platform.architecture()[0] == "32bit" and os.name == 'nt' and "mingw" in os.environ['path'].lower():
        compiler = " --compiler=mingw32"
    sys.stderr.write("To speed up rainflowcounting run: '%s %s build_ext --inplace%s'\n" %
                     (sys.executable, compile_ext.__file__, compiler))
    non_compile_warning_shown = True
