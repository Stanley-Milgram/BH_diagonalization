import os
import profile
import numpy as np
import scipy as sp
from scipy.sparse import csc_matrix
from scipy.sparse import linalg
from numpy import linalg as LA
import time

import spectral

import hamiltonian        as ham
import hamiltonian_parity as ham_par
import function           as ff
import observables        as ob


np.set_printoptions(precision=3)

ll_inp = 20
nn_inp = 3
BC_inp = 0				# 0 is periodic
t_inp  = -1
U_inp  = -1
mat_type_inp = 'Sparse' #'Sparse' #.... deafault Dense
parity_inp   = 'True'	#.... deafault False
n_diag_state_inp = 1
cores_num_inp = 1


######............PREPARATION OF DICTIONARSS

Constants_dictionary = {}
Global_dictionary    = {}

Constants_dictionary = {
	"ll" : ll_inp, 
	"nn" : nn_inp,
	"BC" : BC_inp, 
	"t"  : t_inp ,
	"U"  : U_inp ,
	"n_diag_state"  : n_diag_state_inp,
	"cores_num" : cores_num_inp,
	"mat_type" : mat_type_inp,
	"PATH_now" : os.path.abspath('.'),
	"parity"   : parity_inp,
	}

n_diag_state 	= Constants_dictionary.get("n_diag_state")

Constants_dictionary["tab_fact"]     = ff.fact_creation(**Constants_dictionary)

DIM_H 			= ff.hilb_dim(nn_inp, ll_inp, Constants_dictionary.get("tab_fact"))
Constants_dictionary["DIM_H"]        = DIM_H 
Constants_dictionary["hilb_dim_tab"] = ff.hilb_dim_tab(**Constants_dictionary)

print('Hilbert space Dimension:', Constants_dictionary.get("DIM_H"))

Global_dictionary.update(Constants_dictionary)

BASE_bin, BASE_bose, CONF_tab = ff.Base_prep(**Constants_dictionary)

Global_dictionary["BASE_bin"]    = BASE_bin		#.......11100000, str
Global_dictionary["BASE_bose"]   = BASE_bose	#.......[3 0 0 0 0 0], numpy.ndarray
Global_dictionary["CONF_tab"]    = CONF_tab		#.......224, int

HOP_list     = ff.Hop_prep(**Constants_dictionary)

Global_dictionary["HOP_list"]  = HOP_list

if Constants_dictionary.get("parity") == 'True':

	Global_dictionary["parity_index"], Constants_dictionary["sim_sec_len"] = ham_par.base_parity(**Global_dictionary)
	Global_dictionary.update(Constants_dictionary)

	print('I do parity!! ')

	Hamiltonian = ham_par.bose_Hamiltonian_parity_fast(**Global_dictionary)


else:

	Hamiltonian = ham.bose_Hamiltonian(**Global_dictionary)

E,V   = ham.diagonalization(Hamiltonian, **Global_dictionary)


'''
for i in range(3):
	dens   = ob.density( V[:,i],       **Global_dictionary)

	print(dens)
'''



part_ind = [3,3,3]#,3,3]
state    = np.zeros(ll_inp, dtype=np.int)

b_p_inp	 = Global_dictionary.get("parity_index")
b_p      = np.asarray(b_p_inp)	
DX       = Global_dictionary.get("sim_sec_len")	

for x in range(nn_inp):
	state[part_ind[x]] += int(1)

print(state)

state_con      = ff.FROM_bose_TO_bin (state,     **Global_dictionary)
state_ind      = ff.get_index        (state_con, **Global_dictionary)

state_rev_ind  = ham_par.parity      (state_con, **Global_dictionary)[1]

ind      = min(state_ind,state_rev_ind)
par_ind  = b_p[ind]

i_s = par_ind[0]
i_a = par_ind[3]+DX

B    = np.zeros(DIM_H, dtype=np.double)

if   state_ind == state_rev_ind:

	B[i_s] = 1

elif state_ind <  state_rev_ind:

	B[i_s] = +np.sqrt(2)/2
	B[i_a] = +np.sqrt(2)/2

else:

	B[i_s] = +np.sqrt(2)/2
	B[i_a] = -np.sqrt(2)/2


dt       = 0.1
step_num = 50

t_i 	 = 0
t_f 	 = dt*step_num

A        = -1.0J*Hamiltonian

psit  = linalg.expm_multiply(A, B, start=t_i, stop=t_f, num=step_num+1, endpoint=True)

prova = ham_par.vectors_parity_symmetrize( psit.T, **Global_dictionary)


for i in range(len(psit)):

	dens   = ob.density( prova[:,i],       **Global_dictionary)
	print(dens)











