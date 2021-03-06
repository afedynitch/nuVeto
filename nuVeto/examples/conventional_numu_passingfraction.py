import pickle
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.interpolate import interpolate as interpolate
import CRFluxModels.CRFluxModels as pm
import nuVeto.nuveto as nv
import numpy as np

from nuVeto.external import helper
from nuVeto.external import selfveto as jvssv

def PlotNuMuConventionalPassingFraction(cos_theta, pmodel=(pm.HillasGaisser2012, 'H3a'), hadr='SIBYLL2.3c', prpl='ice_allm97_step_1'):
    """ plot passing fraction for the conventional component
    """
    enu_grid = np.logspace(3, 10, 20)
    enu_grid_fine = np.logspace(3, 10, 1000)
    pnm = [nv.passing(enu, cos_theta, kind = 'conv_numu') for enu in enu_grid]
    pnmfn = interpolate.interp1d(enu_grid, pnm, kind='cubic',
                                 assume_sorted=True, fill_value=(1,np.nan))
    plt.semilogx(enu_grid_fine, pnmfn(enu_grid_fine), label='interpolated')
    plt.xlabel(r'$E_\nu$')
    plt.ylabel(r'Conventional Muon Neutrino Passing Fraction')
    plt.legend()
    plt.savefig("ConventionalNuMuPassingFraction.eps",dpi=300)

if __name__ == "__main__":
    PlotNuMuConventionalPassingFraction(0.1)
    #plt.savefig("ConventionalNuMuPassingFraction.eps",dpi=300)

