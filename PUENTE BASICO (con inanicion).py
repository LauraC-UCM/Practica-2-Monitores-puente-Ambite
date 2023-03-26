"""
        PRACTICA 2 (PRPA)

Laura Cano Gómez 

Solution to the one-way tunnel

"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value
from multiprocessing import Manager

NORTH = 0
SOUTH = 1

NCARS = 5
NPED = 3     # Como los peatones si pueden pasar en ambos sentidos, no hace falta distinguir SU SENTIDO

TIME_CARS_NORTH = 0.5   # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5   # a new car enters each 0.5s
TIME_PED = 5            # a new pedestrian enters each 5s

TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s


class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i',0)

        self.cNortePasando= Value('i', 0)       # Numero de coches seguidos hacia el norte
        self.cSurPasando= Value('i', 0)         # Numero de coches seguidos hacia el sur
        self.peatonesPasando= Value('i', 0)     # Numero de peatones seguidos hacia el sur

        self.permisoCoches= Condition(self.mutex)       # Variable condicion
        self.permisoPeatones= Condition(self.mutex)     # Variable condicion


    '''
    INVARIANTE: (demo en Desarrollo monitor.pdf)
        cNortePasando >= 0
        cSurPasando >= 0
        peatonesPasando >= 0
        cNortePasando > 0 => cSurPasando == 0 /\ peatonesPasando == 0
        cSurPasando > 0 => cNortePasando == 0 /\ peatonesPasando == 0
        peatonesPasando > 0 => cNortePasando == 0 /\ cSurPasando == 0

        Hay inanicion porque podrian estar pasando continuamente  2 de ellos sin que el otro pueda entrar. Ademas, si no paran de llegar de un tipo, hasta que no acaben de salir los otros 2 se quedan bloqueados. Hay que poner alguna limitacion de paso -> turnos (PUENTE POR TURNOS.py)
    '''

    def puenteEstaVacio(self):
        return self.cNortePasando.value == 0 and self.cSurPasando == 0 and self.peatonesPasando == 0


    # Permiso para coches que vienen del norte
    def puedenPasarCN(self):    
        # Pueden pasar si no hay coches en sentido contrario ni peatones pasando, o si hay coches en su mismo sentido 
        puedenPasar= (self.cSurPasando.value == 0 and self.peatonesPasando.value == 0) or (self.cNortePasando.value>0)

        return  puedenPasar or self.puenteEstaVacio()
    

    # Permiso para coches que vienen del sur
    def puedenPasarCS(self):    
        puedenPasar= (self.cNortePasando.value == 0 and self.peatonesPasando.value == 0) or (self.cSurPasando.value>0)

        return  puedenPasar or self.puenteEstaVacio()

    # Permiso para peatones
    def puedenPasarPeatones(self):      
        puedePasar= (self.cNortePasando.value == 0 and self.cSurPasando.value == 0) or (self.peatonesPasando.value>0)
        return puedePasar or self.puenteEstaVacio()



    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código

        # Espera a tener permiso
        if direction==NORTH:
            self.permisoCoches.wait_for(self.puedenPasarCN)

        else:
            self.permisoCoches.wait_for(self.puedenPasarCS)

        # Entra al puente
        if direction == NORTH:
            self.cNortePasando.value += 1
        else:
            self.cSurPasando.value += 1

        # Sale y abre el mutex
        self.mutex.release()


    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        #### código
        
        # Sale del puente
        if direction == NORTH:
            self.cNortePasando.value -= 1
        else:
            self.cSurPasando.value -= 1

        # Avisa a todos los demas coches y peatones de que ha salido, para que comprueben si pueden pasar
        self.permisoCoches.notify_all()
        self.permisoPeatones.notify_all()

        self.mutex.release()


    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código

        # Espera a tener permiso y entra
        self.permisoPeatones.wait_for(self.puedenPasarPeatones)
        self.peatonesPasando.value += 1

        self.mutex.release()


    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código

        # Sale del puente
        self.peatonesPasando.value -= 1

        # Avisa a todos los demas coches y peatones de que ha salido, para que comprueben si pueden pasar
        self.permisoCoches.notify_all()
        self.permisoPeatones.notify_all()

        self.mutex.release()


    def __repr__(self) -> str:
        #return f'Monitor: {self.patata.value}'
        return f'\n   Monitor-> Coches Norte: {self.cNortePasando.value}, Coches Sur: {self.cSurPasando.value}, Peatones :  {self.peatonesPasando.value}.\n\n'



# Funciones para simular el tiempo del paso por el puente
# Con normales 
'''
def delay_car_north() -> None:
    time.sleep(random.normalvariate(1,0.5))

def delay_car_south() -> None:
    time.sleep(random.normalvariate(1,0.5))

def delay_pedestrian() -> None:
    time.sleep(random.normalvariate(1,0.5)) 
'''
# Sin normales
def delay_car_north(factor = 3) -> None:
    time.sleep(random.randint(1,4)/factor)

def delay_car_south(factor = 3) -> None:
    time.sleep(random.randint(1,4)/factor)

def delay_pedestrian(factor = 2) -> None:
    time.sleep(random.randint(3,6)/factor)


# Creación de peatones y coches
def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"Coche {cid} rumbo {direction} quiere entrar. {monitor}")

    monitor.wants_enter_car(direction)
    print(f"Coche {cid} rumbo {direction} entrando... {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    #print(f"Coche {cid} rumbo {direction} abandonando el puente. {monitor}")
    
    monitor.leaves_car(direction)
    print(f"El coche {cid} rumbo {direction} ha salido. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"Peatón {pid} quiere entrar. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"Peatón {pid} entrando... {monitor}")
    delay_pedestrian()

    #print(f"Peatón {pid} abandonando el puente. {monitor}")
    monitor.leaves_pedestrian()
    print(f"El peatón {pid} ha salido. {monitor}")


def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    
    gcars_north.start()
    gcars_south.start()
    gped.start()

    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()
