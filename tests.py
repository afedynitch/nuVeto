from mceqveto import *
from matplotlib import pyplot as plt


def test_pr(cos_theta=1., kind='numu', pmods=(), **kwargs):
    ens = np.logspace(2,9, 100)
    prs = plt.plot(ens, [passing_rate(en, cos_theta, kind=kind, accuracy=20, pmods=pmods) for en in ens], **kwargs)
    plt.xlim(10**3, 10**7)
    plt.ylim(0, 1)
    plt.xscale('log')
    return prs[0]


def test_barr_brackets(cos_theta=1., kind='numu', params='g h1 h2 i w6 y1 y2 z ch_a ch_b ch_e'):
    params = params.split(' ')
    uppers = [BARR[param].error for param in params]
    lowers = [-BARR[param].error for param in params]
    all_pmods = [tuple(zip(params, uppers)), tuple(zip(params, lowers))]
    pr = test_pr(cos_theta, kind, label='{}, cth={}'.format(kind, cos_theta))
    for pmods in all_pmods:
        test_pr(cos_theta, kind, pmods, color=pr.get_color(), alpha=1-abs(pmods[0][-1]))


def test_barr_samples(cos_theta=1, kind='numu', nsamples=10, params='g h1 h2 i w6 y1 y2 z ch_a ch_b ch_e'):
    params = params.split(' ')
    pr = test_pr(cos_theta, kind, label='{}, cth={}'.format(kind, cos_theta))
    for i in xrange(nsamples):
        errors = [np.random.normal(scale=BARR[param].error) for param in params]
        pmods = tuple(zip(params, errors))
        test_pr(cos_theta, kind, pmods, color=pr.get_color(), alpha=1-abs(min(np.mean(errors), 0.1)))
