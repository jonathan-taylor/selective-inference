
from rpy2.robjects.packages import importr
from rpy2 import robjects

SLOPE = importr('SLOPE')

import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

import numpy as np
import sys

from regreg.atoms.slope import slope

import regreg.api as rr


def test_slope_R(X, Y, W = None, normalize = True, choice_weights = "gaussian"):
    robjects.r('''
    slope = function(X, Y, W=NA, normalize, choice_weights, fdr = NA, sigma = 1){

      if(is.na(sigma)){
      sigma = NULL}

      if(is.na(fdr)){
      fdr = 0.1 }

      if(normalize=="TRUE"){
       normalize = TRUE} else{
       normalize = FALSE}

      if(is.na(W))
      {
        if(choice_weights == "gaussian"){
        lambda = "gaussian"} else{
        lambda = "bhq"}
        result = SLOPE(X, Y, fdr = fdr, lambda = lambda, sigma = sigma, normalize = normalize)
       } else{
        result = SLOPE(X, Y, fdr = fdr, lambda = W, sigma = sigma, normalize = normalize)
      }

      return(list(beta = result$beta, E = result$selected, lambda_seq = result$lambda, sigma = result$sigma))
    }''')

    r_slope = robjects.globalenv['slope']

    n, p = X.shape
    r_X = robjects.r.matrix(X, nrow=n, ncol=p)
    r_Y = robjects.r.matrix(Y, nrow=n, ncol=1)

    if normalize is True:
        r_normalize = robjects.StrVector('True')
    else:
        r_normalize = robjects.StrVector('False')

    if W is None:
        r_W = robjects.NA_Logical
        if choice_weights is "gaussian":
            r_choice_weights  = robjects.StrVector('gaussian')
        elif choice_weights is "bhq":
            r_choice_weights = robjects.StrVector('bhq')

    else:
        r_W = robjects.r.matrix(W, nrow=p, ncol=1)

    result = r_slope(r_X, r_Y, r_W, r_normalize, r_choice_weights)

    return result[0], result[1], result[2], result[3]

def compare_outputs_prechosen_weights():

    n, p = 500, 50

    X = np.random.standard_normal((n, p))
    Y = np.random.standard_normal(n)
    W = np.linspace(3, 3.5, p)[::-1]

    output_R = test_slope_R(X, Y, W)
    r_beta = output_R[0]
    print("output of est coefs R", r_beta)

    pen = slope(W, lagrange=1.)
    loss = rr.squared_error(X, Y)
    problem = rr.simple_problem(loss, pen)
    soln = problem.solve()
    print("output of est coefs python", soln)

    print("difference in solns", soln-r_beta)

#compare_outputs_prechosen_weights()

def compare_outputs_SLOPE_weights():

    n, p = 500, 50

    X = np.random.standard_normal((n, p))
    #Y = np.random.standard_normal(n)
    X /= (X.std(0)[None, :] * np.sqrt(n))
    beta = np.zeros(p)
    beta[:5] = 5.

    Y = X.dot(beta) + np.random.standard_normal(n)

    output_R = test_slope_R(X, Y, W = None, normalize = True, choice_weights = "bhq")
    r_beta = output_R[0]
    r_lambda_seq = output_R[2]
    print("output of est coefs R", r_beta)

    W = r_lambda_seq
    pen = slope(W, lagrange=1.)

    loss = rr.squared_error(X, Y)
    problem = rr.simple_problem(loss, pen)
    soln = problem.solve()
    print("output of est coefs python", soln)

    print("difference in solns", soln-r_beta)

compare_outputs_SLOPE_weights()
