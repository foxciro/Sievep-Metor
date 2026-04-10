from auxiliares.models import Fluido
from thermo.chemical import search_chemical

def conseguir_largo(tupla : tuple, valor : str) -> str:
    '''
    Resumen:
        Función para conseguir los valores de las opciones en tuplas como se ve en algunos modelos.
    
    Parámetros:
        tupla : tuple -> Tupla con valores de la forma: (('A','B'),('C','D'))
        valor: str -> Llave a conseguir en los valores.

    Devuelve:
        str: Valor encontrado, o None si no se encuentra

    Ejemplo:
        conseguir_largo((('A','B'),('C','D')), 'A') -> 'B'
    '''
    for x in tupla:
        if(x[0] == valor):
            return x[1]
    
    return '-'

def fluido_existe(cas: str):
    '''
    Resumen:
        Función para comprobar si un fluido existe mediante su código CAS.
    
    Parámetros:
        cas : str -> Código CAS del fluido

    Devuelve:
        dict -> Devuelve el nombre del fluido y el estado (1 = no existe en la BDD pero sí en Thermo, 2 = Ya existe en la BDD, 3 = No encontrado ni en BDD ni en Thermo)
    '''

    if(Fluido.objects.filter(cas = cas).exists()):
        estado = 2 # Encontrado en la BDD
        fluido = Fluido.objects.get(cas = cas).nombre
    else:
        estado = 1 # No encontrado en la BDD pero sí en la librería

    if(estado != 2):
        try:
            quimico = search_chemical(cas, cache=True)
            fluido = quimico.common_name
        except Exception as e:
            print(str(e))
            estado = 3 # No encontrado ni en la librería ni en la BDD
            fluido = None

    return {
        "estado": estado,
        "nombre": fluido
    }

def registrar_fluido(cas: str, nombre: str):
    '''
    Resumen:
        Función para registrar un fluido por código CAS.
    
    Parámetros:
        cas : str -> Código CAS del fluido
        nombre: str -> Nombre con el que registrar el fluido.

    Devuelve:
        dict -> Diccionario con la llave 'id', que contiene la primary key del fluido
    '''
    fluido = Fluido.objects.get_or_create(cas = cas, nombre = nombre.upper())[0]

    return {
        "id": fluido.pk
    }