import numpy as np

from ...tests.instance import gaussian_instance
from ..lasso import lasso, selected_targets
from ..approx_reference import approximate_grid_inference

def test_summary(n=500,
                 p=100,
                 signal_fac=1.,
                 s=5,
                 sigma=2.,
                 rho=0.4,
                 randomizer_scale=1.):

    inst, const = gaussian_instance, lasso.gaussian
    signal = np.sqrt(signal_fac * 2 * np.log(p))

    X, Y, beta = inst(n=n,
                      p=p,
                      signal=signal,
                      s=s,
                      equicorrelated=False,
                      rho=rho,
                      sigma=sigma,
                      random_signs=True)[:3]

    n, p = X.shape

    sigma_ = np.std(Y)
    dispersion = np.linalg.norm(Y - X.dot(np.linalg.pinv(X).dot(Y))) ** 2 / (n - p)

    W = 1 * np.ones(X.shape[1]) * np.sqrt(2 * np.log(p)) * sigma_

    conv = const(X,
                 Y,
                 W,
                 randomizer_scale=randomizer_scale * dispersion)

    signs = conv.fit()
    nonzero = signs != 0

    if nonzero.sum()>0:
        beta_target = np.linalg.pinv(X[:, nonzero]).dot(X.dot(beta))

        (observed_target,
         cov_target,
         cov_target_score,
         alternatives) = selected_targets(conv.loglike,
                                          conv._W,
                                          nonzero,
                                          dispersion=dispersion)

        inverse_info = conv.selective_MLE(observed_target,
                                          cov_target,
                                          cov_target_score)[1]
        
        S = conv.approximate_grid_inference(observed_target,
                                            cov_target,
                                            cov_target_score,
                                            alternatives=alternatives)

def test_approx_pivot(n=500,
                      p=100,
                      signal_fac=1.,
                      s=5,
                      sigma=2.,
                      rho=0.4,
                      randomizer_scale=1.):

    inst, const = gaussian_instance, lasso.gaussian
    signal = np.sqrt(signal_fac * 2 * np.log(p))

    X, Y, beta = inst(n=n,
                      p=p,
                      signal=signal,
                      s=s,
                      equicorrelated=False,
                      rho=rho,
                      sigma=sigma,
                      random_signs=True)[:3]

    n, p = X.shape

    sigma_ = np.std(Y)
    dispersion = np.linalg.norm(Y - X.dot(np.linalg.pinv(X).dot(Y))) ** 2 / (n - p)

    W = 1 * np.ones(X.shape[1]) * np.sqrt(2 * np.log(p)) * sigma_

    conv = const(X,
                 Y,
                 W,
                 randomizer_scale=randomizer_scale * dispersion)

    signs = conv.fit()
    nonzero = signs != 0

    if nonzero.sum()>0:
        beta_target = np.linalg.pinv(X[:, nonzero]).dot(X.dot(beta))

        (observed_target,
         cov_target,
         cov_target_score,
         alternatives) = selected_targets(conv.loglike,
                                          conv._W,
                                          nonzero,
                                          dispersion=dispersion)

        inverse_info = conv.selective_MLE(observed_target,
                                          cov_target,
                                          cov_target_score)[1]

        approximate_grid_inf = approximate_grid_inference(observed_target,
                                                          cov_target,
                                                          cov_target_score,
                                                          inverse_info,
                                                          conv.observed_opt_state,
                                                          conv.sampler.affine_con.mean,
                                                          conv.sampler.affine_con.covariance,
                                                          conv.sampler.logdens_transform[0],
                                                          conv.sampler.affine_con.linear_part,
                                                          conv.sampler.affine_con.offset)

        pivot = approximate_grid_inf._approx_pivots(beta_target)

        return pivot


def test_approx_ci(n=500,
                   p=100,
                   signal_fac=1.,
                   s=5,
                   sigma=2.,
                   rho=0.4,
                   randomizer_scale=1.,
                   level=0.9):

    inst, const = gaussian_instance, lasso.gaussian
    signal = np.sqrt(signal_fac * 2 * np.log(p))

    X, Y, beta = inst(n=n,
                      p=p,
                      signal=signal,
                      s=s,
                      equicorrelated=False,
                      rho=rho,
                      sigma=sigma,
                      random_signs=True)[:3]

    n, p = X.shape

    sigma_ = np.std(Y)
    dispersion = np.linalg.norm(Y - X.dot(np.linalg.pinv(X).dot(Y))) ** 2 / (n - p)

    W = 1 * np.ones(X.shape[1]) * np.sqrt(2 * np.log(p)) * sigma_

    conv = const(X,
                 Y,
                 W,
                 randomizer_scale=randomizer_scale * dispersion)

    signs = conv.fit()
    nonzero = signs != 0

    if nonzero.sum()>0:

        (observed_target,
         cov_target,
         cov_target_score,
         alternatives) = selected_targets(conv.loglike,
                                          conv._W,
                                          nonzero,
                                          dispersion=dispersion)

        ntarget = observed_target.shape[0]
        result, inverse_info = conv.selective_MLE(observed_target,
                                                  cov_target,
                                                  cov_target_score)[:2]

        _scale = 4 * np.sqrt(np.diag(inverse_info))
        scale_ = np.max(_scale)
        ngrid = int(2 * scale_/0.1)

        approximate_grid_inf = approximate_grid_inference(observed_target,
                                                          cov_target,
                                                          cov_target_score,
                                                          inverse_info,
                                                          conv.observed_opt_state,
                                                          conv.sampler.affine_con.mean,
                                                          conv.sampler.affine_con.covariance,
                                                          conv.sampler.logdens_transform[0],
                                                          conv.sampler.affine_con.linear_part,
                                                          conv.sampler.affine_con.offset)

        lci, uci = approximate_grid_inf._approx_intervals(level)

        S = conv.approximate_grid_inference(observed_target,
                                            cov_target,
                                            cov_target_score)

    beta_target = np.linalg.pinv(X[:, nonzero]).dot(X.dot(beta))
    coverage = (lci < beta_target) * (uci > beta_target)
    length = uci - lci

    return np.mean(coverage), np.mean(length)



def main(nsim=300, CI = False):

    import matplotlib.pyplot as plt
    from statsmodels.distributions.empirical_distribution import ECDF
    if CI is False:
        _pivot = []
        for i in range(nsim):
            _pivot.extend(test_approx_pivot(n=200,
                                            p=100,
                                            signal_fac=1.,
                                            s=5,
                                            sigma=3.,
                                            rho=0.20,
                                            randomizer_scale=1.))

            print("iteration completed ", i)

        plt.clf()
        ecdf_MLE = ECDF(np.asarray(_pivot))
        grid = np.linspace(0, 1, 101)
        plt.plot(grid, ecdf_MLE(grid), c='blue', marker='^')
        plt.plot(grid, grid, 'k--')
        plt.show()

    if CI is True:
        coverage_ = 0.
        length_ = 0.
        for n in range(nsim):
            cov, len = test_approx_ci(n=500,
                                      p=100,
                                      signal_fac=1.,
                                      s=5,
                                      sigma=2.,
                                      rho=0.4,
                                      randomizer_scale=1.)

            coverage_ += cov
            length_ += len
            print("coverage so far ", coverage_ / (n + 1.))
            print("lengths so far ", length_ / (n + 1.))
            print("iteration completed ", n + 1)

if __name__ == "__main__":
    main(nsim=20, CI = True)
