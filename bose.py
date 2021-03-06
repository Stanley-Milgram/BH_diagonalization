import os
import profile
import numpy as np
from scipy.sparse import csc_matrix
import time
from mpi4py import MPI

import cProfile

import hamiltonian        as ham
import hamiltonian_parity as ham_par
import function           as ff
import observables        as ob
import time_evolution	  as t_ev
import Hamiltonian_MPI	  as ham_MPI

np.set_printoptions(precision=12,suppress=True)

COMM = MPI.COMM_WORLD


#  n 	 Uc
# 2.0	4.0	 0.0
# 3.0	1.83 0.05
# 4.0 	1.15 0.05
# 5.0 	0.82 0.05
# 6.0 	0.63 0.05
# 7.0 	0.48 0.08
# 8.0 	0.45 0.08
# 9.0 	0.40 0.08
# 10.0 	0.32 0.08


for nn_inp in [3]:
		
	bar_inp = 0.0

	
	if nn_inp == 2: ll_inp = 28
	if nn_inp == 3: ll_inp = 32
	if nn_inp == 4: ll_inp = 12
	#if nn_inp == 5: ll_inp = 10
	
	if nn_inp == 2:	U_in = 0.76
	if nn_inp == 3:	U_in = 0.46
	if nn_inp == 4:	U_in = 0.80	
	if nn_inp == 5:	U_in = 0.72
	
	U_inp   = -1.0*U_in


	'''
		if nn_inp == 1:	bar_inp = 0.007
		if nn_inp == 2:	bar_inp = 0.0085
		if nn_inp == 3:	bar_inp = 0.003
		if nn_inp == 4:	bar_inp = 0.0025	
		if nn_inp == 5:	bar_inp = 0.001	
		if nn_inp == 6:	bar_inp = 0.0007			
	'''

	#for ll_inp in np.arange(8,38,4):

	BC_inp 			= 0			# 0 is periodic

	#mat_type_inp     = 'Dense' 	#'Sparse' #.... default Dense
	mat_type_inp     = 'Sparse' 	#.... default Dense
	parity_inp       = 'False'		#.... default False
	n_diag_state_inp = 1
	cores_num_inp    = 2
	t_inp  			 = -1


	t_start  = 0
	dt 		 = 10
	step_num = 500	#100
	Dstep = 1

	#t max 4000

	if mat_type_inp == None:
		mat_type_inp = 'Sparse'

	######............PREPARATION OF DICTIONARSS

	zero = 0.0

	Global_dictionary = {
		"ll" 		: ll_inp, 
		"nn" 		: nn_inp,
		"BC" 		: BC_inp, 
		"t"  		: t_inp ,
		"U"  		: U_inp ,
		"bar"		: zero,
		"n_diag_state"  : n_diag_state_inp,
		"cores_num" : cores_num_inp,
		"mat_type" 	: mat_type_inp,
		"LOCAL" 	: os.path.abspath('.'),
		"parity"   	: parity_inp,
		"dt"      	: dt,
		"step_num"	: step_num,
		"t_start"	: t_start
		}

	n_diag_state 	= Global_dictionary.get("n_diag_state")

	Global_dictionary["tab_fact"]     = ff.fact_creation(ll_inp,nn_inp) #**Global_dictionary)

	DIM_H 			= ff.hilb_dim(nn_inp, ll_inp, Global_dictionary.get("tab_fact"))

	Global_dictionary["DIM_H"]        = DIM_H 
	Global_dictionary["hilb_dim_tab"] = ff.hilb_dim_tab(**Global_dictionary)

	#if COMM.rank == 0:
	print('Hilbert space Dimension:', Global_dictionary.get("DIM_H"))
	print('ll', ll_inp, 'nn', nn_inp)

	COMM.Barrier()

	if COMM.rank == 0:

		BASE_bin, BASE_bose, CONF_tab = ff.Base_prep(**Global_dictionary)

		Global_dictionary["BASE_bin"]    = BASE_bin		#.......11100000, str
		Global_dictionary["BASE_bose"]   = BASE_bose	#.......[3 0 0 0 0 0], numpy.ndarray
		Global_dictionary["CONF_tab"]    = CONF_tab		#.......224, int

	else:

		BASE_bin 		= None
		BASE_bose 		= None
		CONF_tab		= None

	COMM.Barrier()
	BASE_bin 		= COMM.bcast(BASE_bin,	root=0)
	BASE_bose 		= COMM.bcast(BASE_bose,	root=0)
	CONF_tab		= COMM.bcast(CONF_tab,	root=0)

	Global_dictionary["BASE_bin"]    = BASE_bin		#.......11100000, str
	Global_dictionary["BASE_bose"]   = BASE_bose	#.......[3 0 0 0 0 0], numpy.ndarray
	Global_dictionary["CONF_tab"]    = CONF_tab		#.......224, int

	HOP_list     = ff.Hop_prep(**Global_dictionary)
	Global_dictionary["HOP_list"]  = HOP_list

	N 		 	= ob.N_creation(**Global_dictionary)	
	CDC 		= ob.CdiCj_creation(**Global_dictionary)	

	Global_dictionary["CDC_matrix"]   = CDC
	Global_dictionary["N_matrix"]     = N

	
	################################################################################################
	################################################################################################
	############ HAMILTONIAN CAT 0

	Hint   		= ob.int_op     (		**Global_dictionary)
	Hkin_0 		= ob.kinetik_op (0,  	**Global_dictionary)
	Hkin_1 		= ob.kinetik_op (1,  	**Global_dictionary)
	Hkin_05 	= ob.kinetik_op (0.5, 	**Global_dictionary)
	Hba_0   	= ob.bar_0		(0,		**Global_dictionary)



	'''

	directory = os.sep+'dati'+os.sep+'N_'+str(nn_inp)


	for U_inp in np.arange(-0.8,-0.2,0.05):

		xoxo = []

		HH   = U_inp/2*Hint + Hkin_0
		E,V  = ham.diagonalization(HH, **Global_dictionary)

		V   = V.T[0]
		V_c = np.conjugate(V)					

		for i in range(int(ll_inp/2)):

			op_0 = N[0].dot(N[i])
			op = csc_matrix(op_0, shape = (DIM_H,DIM_H), dtype=np.float)
			cc = np.real(V_c.dot(op.dot(V)))

			xoxo.append([ll_inp, i, cc])

		xoxo = np.array(xoxo)

		
		#fit,cov = np.polyfit( xoxo[:,1]/ll_inp, np.log(xoxo[:,2]), 1, cov=True)
		#print(ll_inp, U_inp, fit[0], np.sqrt(cov[0,0]), fit[1], np.sqrt(cov[1,1]))

		l0 = "{:.0f}".format(ll_inp)
		u0 = "{:.2f}".format(U_inp)

		print(l0,u0)

		ob.Export_Observable(xoxo, directory, 'corr-L_'+l0+'-U_'+u0+'.dat', **Global_dictionary)

	#quit()

	'''

############ HAMILTONIAN CAT omega = 0 no barrier

	HH_1   = U_inp/2*Hint + Hkin_0

	E1,V_cat_0  = ham.diagonalization(HH_1, **Global_dictionary)

############ HAMILTONIAN CAT omega = 1 no barrier

	HH_2   = U_inp/2*Hint + Hkin_1

	E2,V_cat_1  = ham.diagonalization(HH_2, **Global_dictionary)


	for bar_inp in np.arange(0,0.06,0.001):

############ HAMILTONIAN t=0 omega = 0, YES barrier

		HH_3   = U_inp/2*Hint + Hkin_0 + bar_inp*Hba_0
		E3,V3  = ham.diagonalization(HH_3, **Global_dictionary)

		n0 = "{:.0f}".format(nn_inp)
		l0 = "{:.0f}".format(ll_inp)
		u0 = "{:.2f}".format(U_inp)
		b0 = "{:.5f}".format(bar_inp)

		directory = os.sep+'dati'+os.sep+'L_'+l0+os.sep+'N_'+n0+os.sep+'U_'+u0+os.sep+'bb_'+b0

############ HAMILTONIAN t evolution omega = 1/2, YES barrier

		HH_ev = U_inp/2*Hint + Hkin_05 + bar_inp*Hba_0
		HH_ev  = HH_ev.todense()
        
############ time_evolution

		psi_0 = V3
		psit = t_ev.time_evolution(psi_0, HH_ev, **Global_dictionary)

####################	OBSERVABLES -->> 			
		ll = ll_inp

		cu_op 		= ob.corrente_op(0,    **Global_dictionary)
		fl_op   	= ob.fluct_op   (cu_op,**Global_dictionary)

		t_vec          = range(0,step_num,Dstep)
		corrente_array = np.real(np.array([[t*dt+t_start, np.conjugate(psit[t]).dot(cu_op.dot(psit[t]))] for t in t_vec]))
		fisherin_array = np.real(np.array([[t*dt+t_start, np.conjugate(psit[t]).dot(cu_op.dot(psit[t])), np.conjugate(psit[t]).dot(fl_op.dot(psit[t]))] for t in t_vec]))			

		ob.Export_Observable(fisherin_array,   	directory, 'fish_t.dat',     **Global_dictionary)
		ob.Export_Observable(corrente_array, 	directory, 'corrente.dat', **Global_dictionary)										

		ob.Export_Fidelity_CAT_s(psit, V_cat_0, V_cat_1, directory, 'fidelity_cat_s.dat',**Global_dictionary)
		ob.Export_Fidelity_CAT_a(psit, V_cat_0, V_cat_1, directory, 'fidelity_cat_a.dat',**Global_dictionary)			
		ob.Export_Fidelity(psit, V_cat_0,   directory, 'fidelity_0.dat',**Global_dictionary)
		ob.Export_Fidelity(psit, V_cat_1,   directory, 'fidelity_1.dat',**Global_dictionary)
		ob.Export_Fidelity(psit, psi_0,     directory, 'fidelity_psi0.dat',**Global_dictionary)






