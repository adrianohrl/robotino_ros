#!/usr/bin/env python

import roslib; roslib.load_manifest('smach_tutorials')
import rospy
import smach
import smach_ros
from enum import *
from enum import areaOrganizada
from pegando_objeto import *
from deixando_objeto import *
from indo_para_area import *
from ligando_leds import *
from lendo_postes import *
global buffer_empty
global success
global objeto
global terminou
global cores
global prox_area_aux
global prox_area
global area_verifica
global areas_ogz
global num_prateleiras_arrumadas
global parar_arrumar
parar_arrumar = False
prox_area_aux = []
prox_area = []
area_verifica = AreasOrganizadas.A1
num_prateleiras_arrumadas = 0

areas_ogz = [AreasOrganizadas.A1, AreasOrganizadas.A2, AreasOrganizadas.A3, AreasOrganizadas.A4, AreasOrganizadas.B1, AreasOrganizadas.B2, AreasOrganizadas.B3, AreasOrganizadas.B4]
areas = [Areas.A1, Areas.A2, Areas.A3, Areas.A4, Areas.B1, Areas.B2, Areas.B3, Areas.B4, Areas.CASA]

cores = [1, 2, 3, 4]

buffer_empty = True
success = False
terminou = False
objeto = Objetos.NONE

seq = 0

# define state IndoParaArea
class IndoParaArea(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['chegou'],
				input_keys=['area'])

    def execute(self, userdata):
	global seq
	global cores
	global terminou
	seq += 1
	rospy.logwarn('Area: %s', userdata.area[0])
	
	if userdata.area[0] == Areas.CASA:
		ligandoLeds(cores, True)
		indoParaArea(userdata.area, seq)
		return 'chegou'
	indoParaArea(userdata.area, seq)
	rospy.logwarn('Cheguei')
	return 'chegou'

# define state EstouNaArea
class EstouNaArea(smach.State):   
    def __init__(self):
        smach.State.__init__(self, outcomes=['pegar_obj', 'deixar_obj', 'fim_org', 'comeca_org'],
				input_keys=['area_atual', 'area_des', 'area_aux'],
				output_keys=['prox_area', 'area_parc'])

    def execute(self, userdata):
	global objeto
	global terminou
	global areas
	global prox_area_aux
	global prox_area
	rospy.logwarn("Area Atual: %s, Area Desejada: %s, Area Auxiliar: %s", userdata.area_atual, userdata.area_des, userdata.area_aux)
	if userdata.area_atual[0] == Areas.CASA[0]:
		desligandoLeds()
		terminou = True
		return 'fim_org'
	if userdata.area_atual[0] == userdata.area_des[0]:
		rospy.logwarn('Estou na Area Desejada com o objeto %s, buffer %s', userdata.area_atual[4], buffer_empty)
		if not areaOrganizada(userdata.area_atual, objeto) and not areaComObjDesejado(userdata.area_des, userdata.area_aux):
			success = True
			terminou = True
			userdata.prox_area = Areas.CASA
			return 'comeca_org'
		if areaOrganizada(userdata.area_atual, objeto) and buffer_empty:			
			rospy.logwarn('Estou na Prateleira Desejada com Objeto DESEJADO na primeira passada')
			success = True
			terminou = True			
			userdata.prox_area = Areas.CASA
			return 'comeca_org'
		if not areaOrganizada(userdata.area_atual, objeto) and buffer_empty:
			rospy.logwarn('Estou na Prateleira Desejada com Objeto AUXILIAR')
			if len(userdata.area_atual[4]) == 0:
				userdata.prox_area = Areas.CASA
				success = True
				terminou = True
				return 'comeca_org'
			if userdata.area_aux == Areas.CASA:
				userdata.prox_area = Areas.CASA
				success = True
				terminou = True
				return 'comeca_org'
			userdata.area_parc = userdata.area_atual			
			userdata.prox_area = Areas.BUFFER
			return 'pegar_obj'
		if areaOrganizada(userdata.area_atual, objeto) and not buffer_empty:	
			rospy.logwarn('Estou na Prateleira Desejada com Objeto DESEJADO')
			userdata.area_parc = userdata.area_atual			
			userdata.prox_area = Areas.BUFFER
			return 'deixar_obj'
	elif userdata.area_atual[0] == Areas.BUFFER[0]:
		rospy.logwarn('Estou no Buffer')
		if buffer_empty == True:
			rospy.logwarn('Estou no Buffer e vou deixar o Objeto AUXILIAR')
			userdata.area_parc = userdata.area_atual			
			userdata.prox_area = userdata.area_aux
			return 'deixar_obj'
		if buffer_empty == False:
			rospy.logwarn('Estou no Buffer e vou pegar o Objeto AUXILIAR')
			userdata.area_parc = userdata.area_atual			
			userdata.prox_area = userdata.area_aux
			return 'pegar_obj'
	elif userdata.area_atual[0] == userdata.area_aux[0]:
		rospy.logwarn('Estou na Prateleira Auxiliar, Buffer: %s', buffer_empty)
		if areaComObjDesejado(userdata.area_des, userdata.area_atual) and not buffer_empty:
			rospy.logwarn('Estou na Prateleira Auxiliar e vou pegar o Objeto DESEJADO')
			rospy.logwarn('%s', userdata.area_atual)	
			userdata.area_parc = userdata.area_atual			
			userdata.prox_area = userdata.area_des			
			return 'pegar_obj'
		if not areaComObjDesejado(userdata.area_des, userdata.area_atual) and buffer_empty:
			rospy.logwarn('Estou na Prateleira Auxiliar e vou deixar o Objeto AUXILIAR e ir pra casa')
			success = True			
			terminou = True			
			userdata.area_parc = userdata.area_atual			
			userdata.prox_area = Areas.CASA
			return 'deixar_obj'
	rospy.logerr('Deu algum erro, vou deixar o Objeto e ir pra casa')
	success = False
	terminou = True
	userdata.prox_area = Areas.CASA
	return 'deixar_obj'

# define state PegandoObjeto
class PegandoObjeto(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['pegou'],
				input_keys=['area_atual'])

    def execute(self, userdata):
	global buffer_empty
	global objeto
	rospy.logwarn('Peguei e vou para a proxima area')
	objeto = userdata.area_atual[4]
	rospy.logwarn('Objeto: %s', objeto)
	pegandoObjeto(userdata.area_atual, objeto[1])
	rospy.logwarn("%s", userdata.area_atual)
	if userdata.area_atual[0] == Areas.BUFFER[0]:
		buffer_empty = True
	return 'pegou'

# define state DeixandoObjeto
class DeixandoObjeto(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['deixou'],
				input_keys=['area_atual', 'area_aux'])

    def execute(self, userdata):
	global buffer_empty
	global objeto
	deixandoObjeto(userdata.area_atual, objeto)
	rospy.logwarn('Area Atual :%s na Area Auxiliar: %s', userdata.area_atual, userdata.area_aux)
	rospy.logwarn('Deixei :%s na Area:%s', objeto, userdata.area_atual)
	objeto = Objetos.NONE
	if userdata.area_atual[0] == userdata.area_aux[0]:
		rospy.logwarn('Deixei e vou voltar para casa')
		return 'deixou'
	buffer_empty = False
	rospy.logwarn('Deixei e vou para a proxima area')
	return 'deixou'

# define state LendoPostes
class LendoPostes(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['leitura_realizada', 'finaliza_prova'],
				input_keys=['area_atual'],
				output_keys=['prox_area', 'nova_area_des', 'nova_area_aux'])

    def execute(self, userdata):
	global terminou
	global prox_area
	global areas
	global num_prateleiras_arrumadas
	if userdata.area_atual[0] == Areas.CASA[0] and not terminou:
		desligandoLeds()
		rospy.logwarn('Estou em casa e vou comecar a ler os postes')
		prox_area = lendoPostes()
		while prox_area == Areas.CASA:
			rospy.logwarn('Lendo os postes....')
			prox_area = lendoPostes()
		ondeIr()	
		if parar_arrumar == True:
			rospy.logwarn('Como ficaram Areas A: %s, %s, %s, %s', Areas.A1, Areas.A2, Areas.A3, Areas.A4)
			rospy.logwarn('Como ficaram Areas B: %s, %s, %s, %s', Areas.B1, Areas.B2, Areas.B3, Areas.B4)
			rospy.logwarn('Num prat arrumadas : %s', num_prateleiras_arrumadas)
			return 'finaliza_prova'	
		else:		
			userdata.prox_area = prox_area
			userdata.nova_area_des = prox_area
			novaAreaAux(prox_area)
			userdata.nova_area_aux = prox_area_aux
			rospy.logwarn('Prox_area_des: %s, prox_area_aux: %s', prox_area, prox_area_aux)
			return 'leitura_realizada'
	if userdata.area_atual[0] == Areas.CASA[0] and terminou:
		'''
		if prox_area[0] == Areas.CASA[0]:
			rospy.logwarn('Finalizei a organizacao')
			rospy.logwarn('Como ficaram Areas A: %s, %s, %s, %s', Areas.A1, Areas.A2, Areas.A3, Areas.A4)
			rospy.logwarn('Como ficaram Areas B: %s, %s, %s, %s', Areas.B1, Areas.B2, Areas.B3, Areas.B4)
			return 'finaliza_prova'
		'''
		prox_area = lendoPostes()
		if prox_area == Areas.CASA:
			rospy.logwarn('Como ficaram Areas A: %s, %s, %s, %s', Areas.A1, Areas.A2, Areas.A3, Areas.A4)
			rospy.logwarn('Como ficaram Areas B: %s, %s, %s, %s', Areas.B1, Areas.B2, Areas.B3, Areas.B4)
			rospy.logwarn('Num prat arrumadas : %s', num_prateleiras_arrumadas)
		while prox_area == Areas.CASA:
			rospy.logwarn('Lendo os postes....')
			prox_area = lendoPostes()
		ondeIr()
		if parar_arrumar == True:
			rospy.logwarn('Como ficaram Areas A: %s, %s, %s, %s', Areas.A1, Areas.A2, Areas.A3, Areas.A4)
			rospy.logwarn('Como ficaram Areas B: %s, %s, %s, %s', Areas.B1, Areas.B2, Areas.B3, Areas.B4)
			rospy.logwarn('Num prat arrumadas : %s', num_prateleiras_arrumadas)
			return 'finaliza_prova'
		else:
			userdata.prox_area = prox_area
			userdata.nova_area_des = prox_area
			rospy.logwarn('Acabei de organizar mais um e vou ler o prox pedido, %s', prox_area)
			novaAreaAux(prox_area)
			userdata.nova_area_aux = prox_area_aux
			terminou = False
			rospy.logwarn('Prox_area_des: %s, prox_area_aux: %s', prox_area, prox_area_aux)
			return 'leitura_realizada'

def novaAreaAux(area_des):
	global prox_area_aux
	global areas_ogz
	global area_verifica
	area_verifica = AreasOrganizadas.A1
	atualizaAreasOgz()
	rospy.logwarn('VOU PROCURAR A AREA AUX DA AREA %s', area_des[0])
	for i in range (0, 8):
		rospy.logwarn('ENTROU AQUI, area_verifica: %s, i: %s', area_verifica[0], i)
		if area_des[0] == area_verifica[0]:
			rospy.logwarn('Procurando area aux da area: %s', area_verifica[0])
			rospy.logwarn('Objeto procurado: %s', area_verifica[1])
			if area_verifica[1] == Areas.A1[4]:
				if Areas.A1[4] != AreasOrganizadas.A1[1]:
					prox_area_aux = Areas.A1
					return
			if area_verifica[1] == Areas.A2[4]:
				if Areas.A2[4] != AreasOrganizadas.A2[1]:
					prox_area_aux = Areas.A2		
					return	
			if area_verifica[1] == Areas.A3[4]:
				if Areas.A3[4] != AreasOrganizadas.A3[1]:
					prox_area_aux = Areas.A3		
					return	
			if area_verifica[1] == Areas.A4[4]:
				if Areas.A4[4] != AreasOrganizadas.A4[1]:
					prox_area_aux = Areas.A4		
					return	
			if area_verifica[1] == Areas.B1[4]:
				if Areas.B1[4] != AreasOrganizadas.B1[1]:
					prox_area_aux = Areas.B1		
					return	
			if area_verifica[1] == Areas.B2[4]:
				if Areas.B2[4] != AreasOrganizadas.B2[1]:
					prox_area_aux = Areas.B2		
					return	
			if area_verifica[1] == Areas.B3[4]:
				if Areas.B3[4] != AreasOrganizadas.B3[1]:
					prox_area_aux = Areas.B3		
					return	
			if area_verifica[1] == Areas.B4[4]:
				if Areas.B4[4] != AreasOrganizadas.B4[1]:
					prox_area_aux = Areas.B4		
					return
			else:
				prox_area_aux = Areas.CASA
				prox_area_aux[4] = Objetos.NONE
				return
		area_verifica = areas_ogz.pop(0)
		i += 1

def atualizaAreasOgz():
	global areas_ogz
	areas_ogz = [AreasOrganizadas.A2, AreasOrganizadas.A3, AreasOrganizadas.A4, AreasOrganizadas.B1, AreasOrganizadas.B2, AreasOrganizadas.B3, AreasOrganizadas.B4]

def ondeIr():
	global prox_area
	global terminou
	global num_prateleiras_arrumadas
	global parar_arrumar
	for  i in range (0, 6):
		i += 1
		if num_prateleiras_arrumadas == 7:
			parar_arrumar = True
			return
		else:
			if prox_area == Areas.CASA:
				rospy.logwarn('Como ficaram Areas A: %s, %s, %s, %s', Areas.A1, Areas.A2, Areas.A3, Areas.A4)
				rospy.logwarn('Como ficaram Areas B: %s, %s, %s, %s', Areas.B1, Areas.B2, Areas.B3, Areas.B4)
			while prox_area == Areas.CASA:
				rospy.logwarn('Lendo os postes....')
				prox_area = lendoPostes()
			if areaOrganizada(prox_area, Objetos.NONE):
				num_prateleiras_arrumadas += 1
				ligandoLeds(sinalizaLeitura(prox_area), False)
				ligandoLeds2(cores, True, 5)
				rospy.logwarn('Area ja organizada, bora pra Proxima')		
				prox_area = lendoPostes()
			else:
				num_prateleiras_arrumadas += 1
				ligandoLeds(sinalizaLeitura(prox_area), False)
				return prox_area
