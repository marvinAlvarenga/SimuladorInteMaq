# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 19:34:56 2020

@author: Marvin Alvarenga - AH13019

Simulación de Interrupción de Máquinas
"""

MC = 0 #Master Clock
TIEMPO_PARA_NUEVA_FALLA_DESPUES_DE_REPARADA = 10
NUMERO_DE_PASOS = 11

# La cola de clientes, inicialmente está vacia
COLA_CLIENTES = []

# CONSTANTES PARA EL CONTROL DEL FLUJO DEL PROGRAMA
NADIE = 0
PENDIENTE_DE_PROCESAR = -1
PROCESANDO = -2

# INICIO CLASE PADRE
class Clock(object):
    def __init__(self, identificador, proximo_evento):
        self.identificador = identificador
        self.proximo_evento = proximo_evento

class Cliente(Clock):
    def __init__(self, identificador, proximo_evento, atendido_por):
        Clock.__init__(self, identificador, proximo_evento)
        self.atendido_por = atendido_por
    
    def programar_nueva_falla(self):
        self.atendido_por = NADIE # Ya no está siendo atendido por un servidor
        self.proximo_evento = MC + TIEMPO_PARA_NUEVA_FALLA_DESPUES_DE_REPARADA
# FIN CLASE PADRE
        
# INICIO CLASE SERVIDOR
class Servidor(Clock):
    def __init__(self, identificador, proximo_evento, libre, atendiendo_a, tiempo_que_le_toma):
        Clock.__init__(self,identificador, proximo_evento)
        self.libre = libre
        self.atendiendo_a = atendiendo_a
        self.tiempo_que_le_toma = tiempo_que_le_toma
    
    # Cuando el servidor ha terminado de procesar un cliente debe ponerse en estado de
    # disponible para seguir procesando y programar la proxima falla del cliente
    # que acaba de terminar de ser procesado
    def liberar(self):
        self.proximo_evento = 0
        self.libre = True
        eliminar_cliente_de_cola_por_id(self.atendiendo_a)
        get_cliente_por_id(self.atendiendo_a).programar_nueva_falla()
        self.atendiendo_a = NADIE
    
    # Programar la salida del cliente que se iniciará a procesar según el tiempo
    # que le toma al servidor procesar clientes, bloquear el servidor para que no
    # sea molestado, poner en estado de PROCESANDO al cliente
    def atender_cliente(self, cliente):
        self.proximo_evento = MC + self.tiempo_que_le_toma
        self.libre = False
        self.atendiendo_a = cliente.identificador
        cliente.atendido_por = self.identificador
        cliente.proximo_evento = PROCESANDO
# FIN CLASE SERVIDOR

#CONFIGURE A CONTINUACIÓN EL NUEMERO DE CLIENTES Y SERVIDORES        

# CREACION DE OBJETOS CLIENTES
# @identificador: es un id que hará único al cliente
# @proximo_evento: el tiempo en el que ocurrirá la primera falla
# @atendido_por: inicialmente establecer siempre con el valor de NADIE
cliente1 = Cliente(identificador=1, proximo_evento=1, atendido_por=NADIE)
cliente2 = Cliente(identificador=2, proximo_evento=4, atendido_por=NADIE)
cliente3 = Cliente(identificador=3, proximo_evento=9, atendido_por=NADIE)

# Agregar a la lista tantos objetos clientes haya creado
clientes = [cliente1, cliente2, cliente3]


# CREACION DE OBJETOS SERVIDORES
# @identificador: es un id que hará único al servidor
# @proximo_evento: inicialmente los servidores deben ponerse en 0 porque no están atendiendo a nadie
# @libre: inicialmente en TRUE ya que no hay clientes al comienzo y el servidor está listo para recibirlos
# @tiempo_que_le_toma: son las unidades de tiempo que le toma al servidor procesar un cliente
servidor1 = Servidor(identificador=1, proximo_evento=0, libre=True, atendiendo_a=NADIE, tiempo_que_le_toma=5)
servidor2 = Servidor(identificador=2, proximo_evento=0, libre=True, atendiendo_a=NADIE, tiempo_que_le_toma=5)

# Agregar a la lista tantos objetos servidores haya creado
servidores = [servidor1, servidor2]

#----------------FUNCIONES GENERALES ----------------------------------------

# Generar las columnas a mostrar en pantalla
def desplegar_encabezado():
    linea = "PASO\tMC\t"
    for i in range(len(clientes)):
        linea += "CL" + str(i+1) + "\t"
        
    for i in range(len(servidores)):
        linea += "SV" + str(i+1) + "\t"
    
    linea += "n\t"
    for i in range(len(servidores)):
        linea += "R" + str(i+1) + "\t"
        
    print(linea)

# Devuelve el clock minimo
def get_clock_minimo():
    minimo = 100000 #valor muy grande
    
    for cli in clientes:
        minimo = cli.proximo_evento if cli.proximo_evento > 0 and cli.proximo_evento < minimo else minimo
    
    for serv in servidores:
        minimo = serv.proximo_evento if serv.proximo_evento > 0 and serv.proximo_evento < minimo else minimo
    
    return minimo

# Retorna una instancia de Cliente del identificador pasado como parámetro
def get_cliente_por_id(identifi):
    for cli in clientes:
        if cli.identificador == identifi:
            return cli

# Elimina a un cliente de la cola de servicio en base a su identificador
# esta operación es invocada una vez el cliente ha sido servido y el servidor
# que lo atendió está listo para procesar un cliente diferente
def eliminar_cliente_de_cola_por_id(identif):
    global index
    index = -1
    for i in range(len(COLA_CLIENTES)):
        if identif == COLA_CLIENTES[i].identificador:
            index = i
    if index != -1:
        COLA_CLIENTES.pop(index)

# Inicia el proceso de liberación de los servidores, que contempla las siguientes operaciones:
# 1. Poner en estado de disponible el servidor para que reciba nuevos clientes
# 2. Sacar de la cola de servicio al cliente que acaba de ser procesado
# 3. Poner en funcionamiento nuevamente al cliente reparado, calculando su tiempo donde fallara otra vez
def liberar_servidores():
    for servi in servidores:
        if servi.proximo_evento == MC: #liberar el servidor
            servi.liberar()

# Inicia el proceso de atender clientes, esto ocurre cuando hay servidores libres
# y la cola de servicio tiene clientes que aún no estan siendo atendidos
def cargar_servidores_desde_cola():
    for serv in servidores:
        if serv.libre == True and len(COLA_CLIENTES) > 0:
            for cli in COLA_CLIENTES:
                if cli.atendido_por == NADIE:
                    serv.atender_cliente(cli)

# Un cliente se dañó y necesita ser reparado. Se necesita anexarlo a la cola de servicio
def cargar_clientes_a_cola():
    for cli in clientes:
        n_evento = cli.proximo_evento
        if n_evento == MC and n_evento != PROCESANDO and n_evento != PENDIENTE_DE_PROCESAR:
            cli.proximo_evento = PENDIENTE_DE_PROCESAR
            COLA_CLIENTES.append(cli)
                    

#------------------------INICIO DEL PROCESO DE LA SIMULACIÓN----------------

desplegar_encabezado()

for paso in range(NUMERO_DE_PASOS + 1):
    if paso > 0:
        MC = get_clock_minimo()
        liberar_servidores()
        cargar_servidores_desde_cola()
        cargar_clientes_a_cola()
        cargar_servidores_desde_cola()
  
    # Imprimir en pantalla los pasos de la simulación calculados
    linea = ""
    linea += str(paso) + "\t"
    linea += str(MC) + "\t"
    for i in clientes:
        linea += str(i.proximo_evento) + "\t" if i.proximo_evento > 0 else "pros\t" if i.proximo_evento == PROCESANDO else "pen\t"
    for i in servidores:
        linea += str(i.proximo_evento) + "\t"
    linea += str(len(COLA_CLIENTES)) + "\t"
    for i in servidores:
        linea += str(int(not i.libre)) + "\t"
    print(linea)
    