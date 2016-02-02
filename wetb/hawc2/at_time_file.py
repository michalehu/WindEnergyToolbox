'''
Created on 24/04/2014

@author: MMPE
'''
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import range
from future import standard_library
standard_library.install_aliases()

import numpy as np
class AtTimeFile(object):
    """Loads an at time file generated by HAWC2

    >>> atfile = AtTimeFile("at_time.dat") # load file
    >>> atfile.attribute_names # Attribute names
    ['radius_s', 'twist', 'chord']
    >>> atfile[:3,1]) # first 3 twist rows
    [ 0.       -0.775186 -2.91652 ]
    >>> atfile.twist()[:3]) # first 3 twist rows
    [ 0.       -0.775186 -2.91652 ]
    >>> atfile.twist(10) # Twist at radius = 10 (interpolated)
    -5.34743208242399
    """
    def __init__(self, filename):
        with open(filename) as fid:
            lines = fid.readlines()
        self.attribute_names = lines[2].lower().replace("#", "").split()
        data = np.array([[float(l) for l in lines[i].split() ] for i in range(3, len(lines))])
        self.data = data
        def func_factory(column):
            def values(radius=None):
                if radius is None:
                    return self.data[:, column]
                else:
                    return np.interp(radius, self.data[:, 0], self.data[:, column])
            return values
        for column, att_name in enumerate(self.attribute_names):
            setattr(self, att_name, func_factory(column))

    def radius(self, radius=None):
        """Radius of calculation point(s)

        Parameters
        ----------
        radius : int or float, optional
            - if None (default): Radius of calculation points\n
            - if int or float: Radius of calculation point nearest radius

        Returns
        -------
        radius : float or array_like
            Radius of calculation points or radius of calculation point nearest radius
        """
        if radius is None:
            return self.radius_s(radius)
        else:
            return self.radius_s()[np.argmin(np.abs(self.radius_s() - radius))]

    def value(self, radius, column):
        return np.interp(radius, self.data[:, 0], self.data[:, column])

    def __getitem__(self, subset):
        return self.data[subset]


if __name__ == "__main__":
    at = AtTimeFile(r"tests/test_files/at_time.dat")
    print (at.attribute_names)
    print (at.twist(36))
    print (at.chord(36))

