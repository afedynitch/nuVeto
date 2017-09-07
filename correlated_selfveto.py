import numpy as np
from MCEq.core import MCEqRun
import CRFluxModels as pm
from mceq_config import config, mceq_config_without

r_dict["kaon"]=0.046
r_dict["pion"]=0.573

def GetRunMCLayeredMode(theta,hadronic_model='SIBYLL-2.3c',primary_model=(pm.HillasGaisser2012, 'H3a')):
    cfg = dict(config)
    mceq_run = MCEqRun(
                    hadronic_model,
                    primary_model=primary_model,
                    theta_deg=theta,
                    **cfg
                )
    Xvec = np.arange(1, mceq_run.density_model.max_X, 5)
    mceq_run.solve(int_grid=Xvec, grid_var="X")
    return mceq_run

def GetRelativeContributions(mceq_run):
    total_numu = mceq_run.get_solution('total_numu', 0, grid_idx=0)
    pion_prob = mceq_run.get_solution('pi_numu', 0, grid_idx=0)/total
    kaon_prob = mceq_run.get_solution('kaon_numu', 0, grid_idx=0)/total

def MinimumMuonBrotherEnergy(neutrino_energy,meson):
    """
    Returns the minimum muon energy of the brother muon.
    Eq. (5) from 0812.4308
    """
    if not(meson in r_dict):
        raise Exception("Meson not found in mass dictionary.")
    r = r_dict[meson]
    return neutrino_energy*r/(1.-r)

def MinimumMesonParentEnergy(neutrino_energy,meson):
    """
    Returns the minimum parent meson energy.
    Eq. (5) from 0812.4308
    """
    if not(meson in r_dict):
        raise Exception("Meson not found in mass dictionary.")
    r = r_dict[meson]
    return neutrino_energy/(1.-r)

def CorrelatedProbability(neutrino_energy,costh):

if __name__ == "__main__":
    mierda = GetRunMCLayeredMode(30.)
    print "hola"
