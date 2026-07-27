from datetime import datetime

def parsear_fecha_hora(fecha_texto, hora_texto):
    anio_actual = datetime.now().year
    texto_completo = f"{fecha_texto}/{anio_actual} {hora_texto}"

    fecha_hora = datetime.strptime(texto_completo, "%d/%m/%Y %H:%M")
    return fecha_hora

if __name__ == "__main__":
    resultado = parsear_fecha_hora("28/07", "18:00")
    print(resultado)
    print(type(resultado))