# Copyright 2017 C. Arguelles, S. Palomares-Ruiz, A. Schneider, L. Wille, and T. Yuan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# For more information please email:
#
# C. Arguelles (caad@mit.edu)
# S. Palomres-Ruiz (sergio.palomares.ruiz@ific.uv.es)
# A. Schneider (aschneider@icecube.wisc.edu)
# L. Wille (lwille@icecube.wisc.edu)
# T. Yuan (tyuan@icecube.wisc.edu)
#
# Please cite:
# arXiv:XXXX.XXXX

import numpy as np
import scipy as sp
import scipy.stats as stats
import math
import scipy.interpolate as interpolate
import scipy.integrate as integrate
from MCEq.core import MCEqRun
from MCEq.data import HadAirCrossSections
import CRFluxModels as pm
import utils
from mceq_config import config, mceq_config_without

class Units(object):
    # units
    km = 5.0677309374099995 # km to GeV^-1 value from SQuIDS
    cm = km*1.e-5
    m = km*1.e-3
    gr = 5.62e+23 # gr to GeV value from SQuIDS
    sec = 1523000.0 #$ sec to GeV^-1 from SQuIDS
    GeV = 1
    TeV = 1.e3*GeV
    PeV = 1.e3*TeV

class SelfVetoProbabilityCalculator(object):
    class ParticleProperties(object):
        r_dict ={}; mass_dict = {}; lifetime_dict = {}; pdg_id = {};
        r_dict["kaon"]=0.046
        r_dict["pion"]=0.573

        mass_dict["kaon"]=0.493677*Units.GeV # GeV
        mass_dict["pion"]=0.139570*Units.GeV # GeV

        lifetime_dict["kaon"]=1.2389e-8*Units.sec # s converted to GeV^-1
        lifetime_dict["pion"]=2.6033e-8*Units.sec # s converted to GeV^-1

        pdg_id["kaon"] = 321 # k+
        pdg_id["pion"] = 211 # pi+

    class MaterialProperties(object):
        a = {}; b = {}; density = {};
        a["ice"]=0.249*Units.GeV/Units.m # GeV/mwe
        a["rock"]=0.221*Units.GeV/Units.m # GeV/mwe
        b["ice"]=0.422e-3/Units.m # 1/mwe
        b["rock"]=0.531e-3/Units.m # 1/mwe
        density["ice"] = 0.9167*Units.gr/Units.cm**3 # g/cm^3

    def  __init__(self,hadronic_model = 'SIBYLL-2.3c', primary_cr_model=(pm.HillasGaisser2012, 'H3a')):
        self.hadronic_model = hadronic_model
        self.primary_cr_model = primary_cr_model

class CorrelatedSelfVetoProbabilityCalculator(SelfVetoProbabilityCalculator):
    meson_list = ["kaon","pion"]
    def  __init__(self,hadronic_model = 'SIBYLL-2.3c', primary_cr_model=(pm.HillasGaisser2012, 'H3a'), life_dangerously = True):
        super(CorrelatedSelfVetoProbabilityCalculator, self).__init__(hadronic_model,primary_cr_model)

        self.x_max = 100*Units.km
        self.x_min = 0*Units.km

        self.detector_depth = 1950.*Units.m
        self.cfg = dict(config)
        if life_dangerously:
            self.cfg["debug_level"] = 0

        self.cs_db = HadAirCrossSections(hadronic_model)
        self.air_xs_inter = {};
        self.air_xs_inter["kaon"] = interpolate.interp1d(self.cs_db.egrid,self.cs_db.get_cs(self.ParticleProperties.pdg_id['kaon'])) # input GeV return cm^2
        self.air_xs_inter["pion"] = interpolate.interp1d(self.cs_db.egrid,self.cs_db.get_cs(self.ParticleProperties.pdg_id['pion'])) # input GeV return cm^2

    def RunMCLayeredMode(self, costh,number_of_layers=100):
        self.mceq_run = MCEqRun(
                        self.hadronic_model,
                        primary_model=self.primary_cr_model,
                        theta_deg=np.degrees(np.arccos(costh)),
                        **self.cfg
                    )

        self.Xvec = np.arange(1, self.mceq_run.density_model.max_X, self.mceq_run.density_model.max_X/number_of_layers)
        self.mceq_run.solve(int_grid=self.Xvec, grid_var="X")

    def UpdateRelativeContributions(self, height):
        idx=self.FindNearest(self.Xvec,self.mceq_run.density_model.s_h2X(height))
        total_numu = self.mceq_run.get_solution('total_numu', 0, grid_idx=0)
        self.pion_prob = self.mceq_run.get_solution('pi_numu', 0, grid_idx=idx)/total_numu
        self.kaon_prob = self.mceq_run.get_solution('k_numu', 0, grid_idx=idx)/total_numu

    def FindNearest(self, array,value):
        return np.searchsorted(array, value, side="left")

    def MinimumMuonBrotherEnergy(self, neutrino_energy,meson):
        """
        Returns the minimum muon energy of the brother muon.
        Eq. (5) from 0812.4308
        """
        if not(meson in self.ParticleProperties.r_dict):
            raise Exception("Meson not found in mass dictionary.")
        r = self.ParticleProperties.r_dict[meson]
        return neutrino_energy*r/(1.-r)

    def MinimumMesonParentEnergy(self, neutrino_energy,meson):
        """
        Returns the minimum parent meson energy.
        Eq. (5) from 0812.4308
        """
        if not (meson in r_dict):
            raise Exception("Meson not found in mass dictionary.")
        r = self.ParticleProperties.r_dict[meson]
        return neutrino_energy/(1.-r)

    def DecayProbability(self, primary_energy, distance, meson):
        if not (meson in self.ParticleProperties.r_dict):
            raise Exception("Meson not found lifetime dictionary.")
        boost_factor=primary_energy/self.ParticleProperties.mass_dict[meson]
        return np.exp(-distance/(boost_factor*self.ParticleProperties.lifetime_dict[meson]))

    def NoInteractionProbability(self, primary_energy, column_density, meson):
        if not (meson in self.ParticleProperties.r_dict):
            raise Exception("Meson not found cross section dictionary.")
        return np.exp(-column_density/(self.air_xs_inter[meson](primary_energy)*Units.cm**2)/self.ParticleProperties.mass_dict[meson])

    def MeanMuonDistance(self, muon_energy, medium = "ice", min_muon_energy=Units.TeV):
        if (muon_energy<min_muon_energy): return 0.
        if not (medium in self.MaterialProperties.a) or not (medium in self.MaterialProperties.b):
            raise Exception("Medium energy losses for muons not found.")
        a_ = self.MaterialProperties.a[medium]
        b_ = self.MaterialProperties.b[medium]

        return np.log((a_ + muon_energy*b_)/(a_ + min_muon_energy*b_))/b_

    def GetAirColumnDensity(self, height, distance):
        return (self.mceq_run.density_model.s_h2X(height) - self.mceq_run.density_model.s_h2X(height+distance))*Units.gr/Units.cm**2

    def GetIceColumnDensity(self, costh, depth = 1950.*Units.m):
        return (utils.overburden(costh, depth/Units.m, elevation=2400)*Units.m)*self.MaterialProperties.density["ice"]

    def MuonReachProbability(self, muon_energy, height, ice_column_density):
        # simplifying assumption that the muon reach distribution is a gaussian
        # the probability that it does not reach is given by the cumnulative distribution function
        # on the other hand the reaching probability is given by the survival distribution function
        # the former is associated with the passing rate.
        return stats.norm.cdf(ice_column_density/self.MaterialProperties.density["ice"],
                loc=self.MeanMuonDistance(muon_energy),scale=np.sqrt(self.MeanMuonDistance(muon_energy)))

    def NeutrinoFromParentProbability(self,neutrino_energy,costh,h,meson):
        self.UpdateRelativeContributions(h)
        ie = self.FindNearest(self.mceq_run.cs.egrid,neutrino_energy/Units.GeV)
        if meson == "pion":
            return self.pion_prob[ie]
        elif meson == "kaon":
            return self.kaon_prob[ie]
        else:
            raise Exception("Invalid meson parent")

    def ParentProductionProbability(self,primary_energy,costh,h,meson):
        ie = self.FindNearest(self.mceq_run.cs.egrid,primary_energy/Units.GeV)
        if meson == "pion":
            return self.mceq_run.get_solution('pi-', 0, grid_idx=0)[ie]
        elif meson == "kaon":
            return self.mceq_run.get_solution('K-', 0, grid_idx=0)[ie]
        else:
            raise Exception("Invalid meson. ")

    def CorrelatedProbability(self,Enu,costh):
        #if self.mceq_run == None:
        self.RunMCLayeredMode(costh)
        # calculate ice column density
        ice_column_density=self.GetIceColumnDensity(costh,self.detector_depth)
        # here we implement the master formulae
        cprob = 0;
        for meson in self.meson_list:
            kernel = lambda x,Emu,h: self.DecayProbability(Emu+Enu,x+h,meson)
            #kernel = lambda x,Emu,h: self.NeutrinoFromParentProbability(Enu,costh,h,meson)*\
            #                         self.DecayProbability(Emu+Enu,x+h,meson)*\
            #                         self.NoInteractionProbability(Emu+Enu,self.GetAirColumnDensity(h,x),meson)*\
            #                         self.ParentProductionProbability(Emu+Enu,costh,h+x,meson)*\
            #                         self.MuonReachProbability(Emu,h,ice_column_density)

            r = self.ParticleProperties.r_dict[meson]
            h_min = 0; h_max = 40*Units.km;
            x_min = 0; x_max = 40*Units.km;
            Emu_min = Enu*r/(1.-r)
            Emu_max = 1.e10*Units.GeV
            cprob += np.array(integrate.tplquad(kernel,
                                        h_min,h_max,
                                        lambda h: Emu_min, lambda h: Emu_max,
                                        lambda h,Emu: x_min, lambda h, Emu: x_max))
        return cprob

if __name__ == "__main__":
    caca = CorrelatedSelfVetoProbabilityCalculator()
    print caca.CorrelatedProbability(1.*Units.TeV,1.)
