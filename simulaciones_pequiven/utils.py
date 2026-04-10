def generate_nonexistent_tag(model, tag):
    """
    Resumen:
        Genera un tag derivado de otro que no exista en la base de datos para el equipo del modelo.
    
    Parámetros:
        model: Model -> El modelo usado para la verificación.
        tag: str -> Tag a derivar.
    
    Devuelve: str
        Etiqueta derivada no existente en el modelo original.
    """

    n = 1
    new_tag = tag
    while model.objects.filter(tag=new_tag).exists():
        new_tag = tag + f'-C{n}'
        n += 1
    
    return new_tag