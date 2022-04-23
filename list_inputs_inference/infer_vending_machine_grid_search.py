import copy
from pathlib import Path

from list_inputs_inference.base_estimator import BaseEstimator
from sklearn.model_selection import GridSearchCV

import operator
import math
import numbers
import sys

import pandas as pd

from custom_operators import protectedDivision, safe_binary_operation
from traces.trace_parser import TraceParser

class Estimator(BaseEstimator):
  def __init__(self, mu=None, lmbda=None, cxpb=None, mutpb=None, gcount=None, popsize=None, mut_tool=None, cx_tool=None, selection=None, tree_output_dir=None, tournsize=None, tournparssize=None):
    self.set_params(mu, lmbda, cxpb, mutpb, gcount, popsize, mut_tool, cx_tool, selection, tree_output_dir, tournsize, tournparssize)

  def set_params(self, mu, lmbda, cxpb, mutpb, gcount, popsize, mut_tool, cx_tool, selection, tree_output_dir, tournsize=None, tournparssize=None):
    self.tree_output_dir = tree_output_dir
    self.mu = mu
    self.lmbda = lmbda
    self.cxpb = cxpb
    self.mutpb = mutpb
    self.gcount = gcount
    self.popsize = popsize
    self.mut_tool = mut_tool
    self.cx_tool = cx_tool
    self.selection = selection
    self.tournsize = tournsize
    self.tournparssize = tournparssize

    self.setup = {
      'population_size': popsize,
      'hall_of_fame_size': 2,
      'input_list_length': 1, # hardcoding it to only accept a single argument # event_args_length,
      'output_type': float,
      'generations_count': gcount,
      'primitives': [
        # [safe_binary_operation(operator.add, 0), [float, float], float, 'add'],
        # [safe_binary_operation(operator.sub, 0), [float, float], float, 'sub'],
        # [safe_binary_operation(operator.mul, 0), [float, float], float, 'mul'],
        # [protectedDivision, [float, float], float, 'div']
        [operator.add, [float, float], float, 'add'],
        [operator.sub, [float, float], float, 'sub'],
        [operator.mul, [numbers.Complex, numbers.Complex], float, 'mul'],
        [operator.truediv, [numbers.Complex, numbers.Complex], float, 'div'],
      ],
      'terminals':[
        [1, float],
        [0, float]
      ],
      'individual_fitness_eval_func': self.eval_mean_squared_error,
      'mut_tool': mut_tool,
      'cx_tool': cx_tool,
      'selection': selection,
      'tournsize': tournsize,
      'tournparssize': tournparssize
    }

    self.estimator = None
    self.gpa = None

    return self

  def eval_mean_squared_error(self, individual, test_x_y_list=None, y_only_list=None):
        # Transform the tree expression in a callable function
        tree_expression = self.gpa.toolbox.compile(expr=individual)
        # Evaluate the mean squared error between the expression
        # and the real function : x**4 + x**3 + x**2 + x

        squared_errors = []
        for x_y in (test_x_y_list or self.gpa.target_list):
          try:
            # EDIT THIS
            # THIS IS JUST TEST IMPLEMENTATION OF RUNNING A FUNCTION MULTIPLE TIMES WITH A SINGLE PARAMETER

            # this is the coin event in the vending machine
            # the params for the coin event are from indexes 1 until the end of the array
            # FIX THIS PART
            params = x_y[0][1:]

            registers = [0, 0, 0, 0, 0]
            tree_expression_result = None

            # lets try to call the tree multiple times with a single parameter each time
            for param in params:
              # pass the param in a list, so that we don't have to change the pick_array_element implementation
              # we will hardcode it to only work for the 0th index of the input, and also for 5 more indexes for 
              # custom registers.
              param_and_registers = [param] + registers # + [output_condition_elements, output_elements]

              tree_expression_result = tree_expression(param_and_registers)
              registers = param_and_registers[-5:]

            # only use the last tree expression result from above
            squared_error = (tree_expression_result - x_y[1]) ** 2
            squared_errors.append(squared_error)

          except Exception as e: # if the tree is just: x , then we have array - integer
            # import traceback
            # print(e)
            # print(traceback.format_exc())
            return math.inf,

        return math.fsum(squared_errors) / len(squared_errors) if len(squared_errors) else 20000,

# tp = TraceParser('./traces/vending_machine/traces_3855')
# tp = TraceParser('./traces/vending_machine/traces_9309')
tp = TraceParser('./traces/vending_machine/traces_1703')

event_args_length, events = tp.parse()

x_y_list = events['coin']
y_list = list(map(lambda s: s[-1], x_y_list))
