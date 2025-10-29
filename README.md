# xsec_lora_workshop

Del Aire al Análisis: Emulación y Decodificación de LoRa con GNU Radio

## Descripcion

Explora paso a paso el proceso de comunicación LoRa sin necesidad de hardware físico. En este taller aprenderás a emular señales LoRa con GNU Radio, crear bloques para su demodulación, y exportar la salida por TCP para su posterior análisis en Python.
El objetivo es comprender cómo se estructura la telemetría en sistemas que utilizan el estándar CCSDS SPP, y cómo un flujo digital puede transformarse en datos interpretables. Todos los materiales serán proporcionados para que puedas seguir la práctica en tiempo real.


# Herramientas


## Instalacion de GNU Radio en Linux

Repos:
- [gnuradio](https://wiki.gnuradio.org/index.php/InstallingGR#Quick_Start)
- [gr-lora_sdr](https://github.com/tapparelj/gr-lora_sdr)

```bash
# GNU Radio
sudo apt install gnuradio

# LoRa lib
git clone https://github.com/tapparelj/gr-lora_sdr
cd gr-lora_sdr
mkdir build
cd build
cmake ..
sudo make install
sudo ldconfig 
```

> Para mas informacion sobre como instalar las librerias revisar cada repositorio.

## Uso de del script
Para utilizar el script y comunicarse correctamente con GNU Radio, la instalacion de librerias se debe realizar directamente en el entorno global.

### Instalacion de librerias requeridas
```bash
pip install zmq spacepackets
```

Si te da error con los paquetes globales del sistema agrega la bandera `--break-system-packages`.


