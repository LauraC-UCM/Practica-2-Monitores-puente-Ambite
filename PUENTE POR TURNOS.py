"""
        PRACTICA 2 (PRPA)

Laura Cano Gómez 

Solution to the one-way tunnel
 
Se añaden variables compartidas para limitar el paso seguido de vehiculos y personas, y turnos entre ellos.

Con justicia, sin inanicion y sin deadblock.
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value
from multiprocessing import Manager

NORTH = 0
SOUTH = 1

NCARS = 5
NPED = 3     

# Constantes para limitar cuantos pueden pasar seguidos de cada tipo
MAX_SEGUIDOS_CN = 3     # Coches del norte
MAX_SEGUIDOS_CS = 3     # Coches del sur
MAX_SEGUIDOS_P = 2      # Peatones

TIME_CARS_NORTH = 0.5   # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5   # a new car enters each 0.5s
TIME_PED = 4            # a new pedestrian enters each 4s

TIME_IN_BRIDGE_CARS = (1, 0.5)          # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10)    # normal 30s, 10s


class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i',0)

        self.cNortePasando= Value('i', 0)         # Numero de coches del norte dentro del puente
        self.cSurPasando= Value('i', 0)           # Numero de coches del sur dentro del puente
        self.peatonesPasando= Value('i', 0)       # Numero de peatones dentro del puente

        self.permisoCoches= Condition(self.mutex)       # Variable condicion
        self.permisoPeatones= Condition(self.mutex)     # Variable condicion

        self.turno= Value('i',0)    # Turno de quién puede pasar: 0 -> coches norte ; 1 -> coches sur ; 2 -> peatones

        self.cNorteSeguidos= Value('i', 0)        # Numero de coches del norte cruzando seguidos
        self.cSurSeguidos= Value('i', 0)          # Numero de coches del sur cruzando seguidos
        self.peatonesSeguidos= Value('i', 0)      # Numero de peatones cruzando seguidos
        
        self.cNorteEsperando= Value('i', 0)       # Numero de coches del norte esperando para pasar
        self.cSurEsperando= Value('i', 0)         # Numero de coches del sur esperando para pasar
        self.peatonesEsperando= Value('i', 0)     # Numero de peatones esperando para pasar



    '''
    INVARIANTE:
        0 <= cNortePasando   <= NCARS
        0 <= cSurPasando     <= NCARS
        0 <= peatonesPasando <= NPED

        0 <= cNorteSeguidos   <= MAX_SEGUIDOS_CN
        0 <= cSurSeguidos     <= MAX_SEGUIDOS_CS
        0 <= peatonesSeguidos <= MAX_SEGUIDOS_P

        0 <= cNorteEsperando   <= NCARS
        0 <= cSurEsperando     <= NCARS
        0 <= peatonesEsperando <= NPED
        
        0 <= turno <= 2

        cNortePasando   > 0 => cSurPasando == 0   /\ peatonesPasando == 0 /\ turno == 0
        cSurPasando     > 0 => cNortePasando == 0 /\ peatonesPasando == 0 /\ turno == 1
        peatonesPasando > 0 => cNortePasando == 0 /\ cSurPasando == 0     /\ turno == 2

    '''


    # Permiso para coches que vienen del norte
    def puedenPasarCN(self):    
        '''{I}'''
        # Pueden pasar si no hay coches en sentido contrario ni peatones pasando, o si hay coches en su mismo sentido 
        noHayOtrosPasando= self.cSurPasando.value == 0 and self.peatonesPasando.value == 0
        '''{I /\ cSurPasando= 0 /\ peatonesPasando= 0} = {I}'''

        # Y cuando no hay nadie esperando a entrar
        noHayOtrosEsperando= self.cSurEsperando.value == 0 and self.peatonesEsperando.value == 0
        '''{I /\ cSurEsperando= 0 /\ peatonesEsperando= 0} = {I}'''
        if noHayOtrosEsperando:
            self.turno.value=0
            '''{I /\ turno= 0} = {I}'''

        '''{I}'''
        return  noHayOtrosPasando and self.turno.value == 0
        


    # Permiso para coches que vienen del sur
    def puedenPasarCS(self):   
        '''{I}'''
        noHayOtrosPasando= self.cNortePasando.value == 0 and self.peatonesPasando.value == 0
        '''{I /\ cNortePasando= 0 /\ peatonesPasando= 0} = {I}'''

        noHayOtrosEsperando= self.cNorteEsperando.value == 0 and self.peatonesEsperando.value == 0
        '''{I /\ cNorteEsperando= 0 /\ peatonesEsperando= 0} = {I}'''
        if noHayOtrosEsperando:
            self.turno.value= 1
            '''{I /\ turno= 1} = {I}'''
        
        '''{I}'''
        return  noHayOtrosPasando and self.turno.value == 1

    # Permiso para peatones
    def puedenPasarPeatones(self):   
        '''{I}'''   
        noHayOtrosPasando= self.cNortePasando.value == 0 and self.cSurPasando.value == 0
        '''{I /\ cNortePasando= 0 /\ cSurPasando= 0} = {I}'''

        noHayOtrosEsperando= self.cNorteEsperando.value == 0 and self.cSurEsperando.value == 0
        '''{I /\ cNorteEsperando= 0 /\ cSurEsperando= 0} = {I}'''
        if noHayOtrosEsperando:
            self.turno.value= 2
            '''{I /\ turno= 2 = {I}'''
        
        '''{I}'''
        return noHayOtrosPasando and self.turno.value == 2 


    def wants_enter_car(self, direction: int) -> None:
        '''{I}'''
        self.mutex.acquire()
        self.patata.value += 1
        #### código

        if direction == NORTH:
            # Espera a tener permiso
            self.cNorteEsperando.value += 1
            '''{I /\ 0 < cNorteEsperando <= NCARS = {I}'''
            self.permisoCoches.wait_for(self.puedenPasarCN)
            '''{I /\ cSurPasando= 0 /\ peatonesPasando= 0 /\ turno = 0} = {I}'''           

            # Entra al puente
            self.cNorteEsperando.value -= 1
            self.cNortePasando.value += 1
            self.cNorteSeguidos.value += 1
            '''{I /\ 0 <= cNorteEsperando <= NCARS /\ 0 < cNortePasando <= NCARS /\ 0 <= cNorteSeguidos <= MAX_SEGUIDOS_CN} = {I}'''

            # Cambia el turno si ha pasado su maximo o si no hay ninguno de su tipo esperando
            if self.cNorteSeguidos.value == MAX_SEGUIDOS_CN or self.cNorteEsperando.value == 0:
                if self.cSurEsperando.value > 0:
                    self.turno.value= 1
                    '''{I /\ (cNorteSeguidos= MAX_SEGUIDOS_CN \/ cNorteEsperando= 0) /\ 0 < cSurEsperando <= NCARS /\ turno= 1} = {I}'''                
                elif self.peatonesEsperando.value > 0:
                    self.turno.value= 2
                    '''{I /\ (cNorteSeguidos= MAX_SEGUIDOS_CN \/ cNorteEsperando= 0) /\ 0 < peatonesEsperando <= NPED /\ turno= 2} = {I}''' 

                self.cNorteSeguidos.value = 0
                '''{I /\ cNorteSeguidos= 0} = {I}'''           

        else:
            # Espera a tener permiso
            self.cSurEsperando.value += 1
            '''{I /\ 0 < cSurEsperando <= NCARS = {I}'''
            self.permisoCoches.wait_for(self.puedenPasarCS)
            '''{I /\ cNortePasando= 0 /\ peatonesPasando= 0 /\ turno = 1} = {I}'''   

            # Entra al puente
            self.cSurEsperando.value -= 1
            self.cSurPasando.value += 1
            self.cSurSeguidos.value += 1
            '''{I /\ 0 <= cSurEsperando <= NCARS /\ 0 < cSurPasando <= NCARS /\ 0 < cSurSeguidos <= MAX_SEGUIDOS_CS} = {I}'''   

            # Cambia el turno si ha pasado su maximo o si no hay ninguno de su tipo esperando
            if self.cSurSeguidos.value == MAX_SEGUIDOS_CS or self.cSurEsperando.value == 0:
                if self.peatonesEsperando.value > 0:
                    self.turno.value= 2
                    '''{I /\ (cSurSeguidos= MAX_SEGUIDOS_CS \/ cSurEsperando= 0) /\ 0 < peatonesEsperando <= NPED /\ turno= 2} = {I}'''                

                elif self.cNorteEsperando.value > 0:
                    self.turno.value= 0
                    '''{I /\ (cSurSeguidos= MAX_SEGUIDOS_CS \/ cSurEsperando= 0) /\ 0 < cNorteEsperando <= NCARS /\ turno= 0} = {I}'''  
                
                self.cSurSeguidos.value = 0           
                '''{I /\ cSurSeguidos= 0} = {I}''' 

        # Sale y abre el mutex
        self.mutex.release()
        '''{I}'''

    def leaves_car(self, direction: int) -> None:
        '''{I}'''
        self.mutex.acquire() 
        self.patata.value += 1
        #### código
        
        # Sale del puente
        if direction == NORTH:
            self.cNortePasando.value -= 1
            '''{I /\ 0 <= cNortePasando <= NCARS} = {I}'''

        else:
            self.cSurPasando.value -= 1
            '''{I /\ 0 <= cSurPasando <= NCARS} = {I}'''

        # Avisa a todos los demas coches y peatones de que ha salido, para que comprueben si pueden pasar
        self.permisoCoches.notify_all()
        self.permisoPeatones.notify_all()

        self.mutex.release()
        '''{I}'''

    def wants_enter_pedestrian(self) -> None:
        '''{I}'''
        self.mutex.acquire()
        self.patata.value += 1
        #### código

        # Espera a tener permiso
        self.peatonesEsperando.value += 1
        '''{I /\ 0 < peatonesEsperando <= NPED} = {I}'''
        self.permisoPeatones.wait_for(self.puedenPasarPeatones)
        '''{I /\ cNortePasando= 0 /\ cSurPasando= 0 /\ turno = 2} = {I}'''   

        # Entra al puente
        self.peatonesEsperando.value -= 1
        self.peatonesPasando.value += 1
        self.peatonesSeguidos.value += 1
        '''{I /\ 0 <= peatonesEsperando <= NPED /\ 0 < peatonesPasando <= NPED /\ 0 < peatonesSeguidos <= MAX_SEGUIDOS_CP} = {I}'''   


        # Cambia el turno si ha pasado su maximo o si no hay ningun peaton esperando
        if self.peatonesSeguidos.value == MAX_SEGUIDOS_P or self.peatonesEsperando.value == 0:
            if self.cNorteEsperando.value > 0:
                self.turno.value= 0
                '''{I /\ (peatonesSeguidos= MAX_SEGUIDOS_CS \/ peatonesEsperando= 0) /\ 0 < cNorteEsperando <= NCARS /\ turno= 0} = {I}'''                

            elif self.cSurEsperando.value > 0:
                self.turno.value= 1
                '''{I /\ (peatonesSeguidos= MAX_SEGUIDOS_CS \/ peatonesEsperando= 0) /\ 0 < cSurEsperando <= NCARS /\ turno= 1} = {I}''' 

            self.peatonesSeguidos.value = 0
            '''{I /\ peatonesSeguidos= 0} = {I}'''

        self.mutex.release()
        '''{I}'''


    def leaves_pedestrian(self) -> None:
        '''{I}'''
        self.mutex.acquire()
        self.patata.value += 1
        #### código

        # Sale del puente
        self.peatonesPasando.value -= 1
        '''{I /\ 0 <= peatonesPasando <= NPED} = {I}'''


        # Avisa a todos los demas coches y peatones de que ha salido, para que comprueben si pueden pasar
        self.permisoCoches.notify_all()
        self.permisoPeatones.notify_all()

        self.mutex.release()
        '''{I}'''


    def __repr__(self) -> str:
        '''{I}'''
        #return f'Monitor: {self.patata.value}'
        return f'\nMonitor: ( Turno: {self.turno.value} )\n  Pasando   -> Coches Norte: {self.cNortePasando.value}, Coches Sur: {self.cSurPasando.value}, Peatones: {self.peatonesPasando.value}.\n  Esperando -> Coches Norte: {self.cNorteEsperando.value}, Coches Sur: {self.cSurEsperando.value}, Peatones: {self.peatonesEsperando.value}. \n\n'



# Funciones para simular el tiempo del paso por el puente
# Con normales 
'''
def delay_car_north() -> None:
    time.sleep(random.normalvariate(1,0.5))

def delay_car_south() -> None:
    time.sleep(random.normalvariate(1,0.5))

def delay_pedestrian() -> None:
    time.sleep(random.normalvariate(30,10)) 
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
