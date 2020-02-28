# Copyright (c) 2016-2018, The University of Texas at Austin 
# & University of California, Merced.
# Copyright (c) 2019-2020, The University of Texas at Austin 
# University of California--Merced, Washington University in St. Louis.
#
# All Rights reserved.
# See file COPYRIGHT for details.
#
# This file is part of the hIPPYlib library. For more information and source code
# availability see https://hippylib.github.io.
#
# hIPPYlib is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License (as published by the Free
# Software Foundation) version 2.0 dated June 1991.

import dolfin as dl
import numpy as np
from numpy.testing import assert_allclose
from mpi4py import MPI

def splitCommunicators(comm_world, n_subdomain, n_instances):
    mpi_rank = comm_world.rank
    world_size = comm_world.size
    assert world_size == n_subdomain*n_instances
    # This interprets the communication structure as a grid where rows correspond
    # to instances and columns correspond to mesh subdomain collectives accross 
    # different samples. Color corresponds to row index, and key corresponds to 
    # column index as is customary. 
    color = np.floor(mpi_rank/n_instances)
    key = np.remainder(mpi_rank,n_instances) 
    mesh_constructor_comm = comm_world.Split(color = color,key = key)
    collective_comm = comm_world.Split(color = key,key = color)
    return mesh_constructor_comm, collective_comm


def checkFunctionSpaceConsistentPartitioning(Vh, collective):
    v = dl.interpolate(dl.Constant(float(collective.rank)),Vh)
    if collective.rank == 0:
        root_v = dl.interpolate(dl.Constant(float(mesh.comm.rank)),Vh)
    else:
        root_v = dl.interpolate(dl.Constant(0.),Vh)
    collective.bcast(root_v.vector(),root = 0)
    diff = v - root_v
    tests_passed_here = diff.norm("l2") < 1e-10
    tests_passed_everywhere = False
    dl.MPI.comm_world.allReduce([tests_passed_here, MPI.BOOL], [tests_passed_everywhere,MPI.BOOL] , op = MPI.LAND)
    return tests_passed_everywhere

def checkMeshConsistentPartitioning(mesh, collective):
    t1 = checkFunctionSpaceConsistentPartitioning(dl.FunctionSpace(mesh,"DG", 0), collective)
    t2 = checkFunctionSpaceConsistentPartitioning(dl.FunctionSpace(mesh,"CG", 1), collective)
    return t1 and t2



