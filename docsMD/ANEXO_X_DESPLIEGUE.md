# ANEXO X: DESPLIEGUE DEL SISTEMA WatermelonD 

**Proyecto:** WatermelonD (Language Copilot for Group and Administration Environments) 
**Versión del Documento:** 1
**Fecha:** 11/01/2026


---
## 1. PREPARACION 
Para llevar acabo la instalacion del sistema WatermelonD necesitaremos una distribucion Linux, el sistema soporta de manera oficial Debian y Ubuntu 

1. Nos desplazamos a la pagina de Debian, y pulsaremos en *Descargar*, debemos verificar que se descarga el archivo `debian-13.3.0-amd64-netinst.iso` (Se recomienda usar debian 12/13).
![1768155741024](image/ANEXO_X_DESPLIEGUE/1768155741024.png)






<Aqui va una instalacion de debian siguiendo los pasos del documento despliegue_desde0.md>

## DESPLIEGUE AUTOMATIZADO (install.sh)
Antes de comenzar la instalacion automatizada debemos comprobar que nuestro sistema tiene instalado el paquete `git` y `wget`, en caso contrario instalarlo usando nuestro instalador de paquetes 
![1768155996639](image/ANEXO_X_DESPLIEGUE/1768155996639.png)
![1768156548600](image/ANEXO_X_DESPLIEGUE/1768156548600.png)

En el repositorio de Github encontraremos un comando que descargara el script de instalacion del servicio, se esta dando por hecho que tenemos una conexion ssh con el equipo en el que se va a desplegar el servicio, por lo que solo debemos copiar el comando y pegarlo en la terminal remota que tengamos en uso 
![1768156481776](image/ANEXO_X_DESPLIEGUE/1768156481776.png)

Pegaremos el comando de instalacion en la terminal y pulsaremos enter, el script es interactivo, preguntara varias cosas al usuario segun la instalacion que se vaya a hacer y pedira la clave de sudo cuando sea necesario (esta instalacion requiere conexion a internet y puede llevar hasta 1 hora)
![1768156562584](image/ANEXO_X_DESPLIEGUE/1768156562584.png)

En las siguientes imagenes podemos ver algunas de las opciones que da el instalador asi como su funcionamiento

![1768156660479](image/ANEXO_X_DESPLIEGUE/1768156660479.png)
![1768156683906](image/ANEXO_X_DESPLIEGUE/1768156683906.png)
El script incluye una serie de optimizaciones para sistemas debian para hacerlos mas ligeros en cuanto al consumo de recursos
![1768156700930](image/ANEXO_X_DESPLIEGUE/1768156700930.png)
Instala todas las dependecias y paquetes de manera automatica 
![1768156867549](image/ANEXO_X_DESPLIEGUE/1768156867549.png)
![1768156890145](image/ANEXO_X_DESPLIEGUE/1768156890145.png)
![1768156898443](image/ANEXO_X_DESPLIEGUE/1768156898443.png)
La parte mas lenta es la descarga de librerias de python 
![1768157159495](image/ANEXO_X_DESPLIEGUE/1768157159495.png)
![1768160159165](image/ANEXO_X_DESPLIEGUE/1768160159165.png)
![1768160330015](image/ANEXO_X_DESPLIEGUE/1768160330015.png)
![1768160496426](image/ANEXO_X_DESPLIEGUE/1768160496426.png)

