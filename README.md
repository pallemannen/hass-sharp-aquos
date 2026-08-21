
# hass-sharp-aquos

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&repository=hass-sharp-aquos&owner=pallemannen)

Home Assistant integration for Sharp Aquos TVs.

## Compatibility

This integration should work with network-enabled Sharp Aquos LCD/LED televisions released between roughly 2011 and 2016. This includes:
- LE Series (High-End & Mid-Range): Models starting with LC- and ending with LE or U (e.g., LC-60LE650U, LC-70LE732U, LC-52LE835U).
- UD / EQ / SQ Series (Early 4K/Premium): Flagship models like the LC-UD27U, LC-EQ10U, and LC-SQ15U.

## How to check and enable

- You need a network enabled TV - either with an ethernet RJ-45 jack or a WiFi module.
- Look for "IP Control", "Remote Control Settings" or "AQUOS Remote Control" in the settings, and turn it on.

## Workaround for older TV's

- Some older Aquos models have a 9-pin RS-232 serial port that accepts the same commands. You could use a ESP32 with a MAX3232 TTL-to-RS232 device (or any other similar products), point this integration to the ESP32 and let then relay the commands to the serial connection.

Example ESP configuration:
```YAML
esphome:
  name: aquos-network-bridge

esp8266:
  board: d1_mini

# 1. Setup the physical serial port connected to your MAX3232 transceiver
uart:
  id: tv_uart
  tx_pin: GPIO1
  rx_pin: GPIO3
  baud_rate: 9600
  stop_bits: 1
  data_bits: 8
  parity: NONE

# 2. Open up port 10002 on the network and link it directly to the UART
stream_server:
  uart_id: tv_uart
  port: 10002
```
TV models from 2004 to 2012 that might have such an RS-232 port:
- D-Series (the early flat-panels): Models like the LC-42D64U, LC-52D64U, LC-65D64U, and LC-32D4U.
- LE/UN Series (first backlit LEDs): Models ending in LE700UN or LE810UN (such as LC-46LE700UN or LC-52LE700UN).

As TVs grew larger and thinner, Sharp replaced the bulky DB9 housing with an RS-232C 3.5mm headphone-jack style port labeled "Service" or "Control" to save physical space on the chassis. A 3.5mm-to-DB9 adapter cable or a 3.5mm stereo jack breakout wired to the MAX3232 chip is required for this setup. Models include:
- LE600/700/800 Series: High-performance large screens such as the LC-60LE657U, LC-70LE657U, LC-80LE657U, and the massive LC-90LE657U.
- Early Smart Central Arrays: Sub-series lines including the LE830U, LE835U, and early LE650U sets.

For commercial digital signage displays or interactive conference boards (like the PN-L703B series), Sharp exposes serial controls under a small screw-down service plate on the back cover housing.

## Installation

1. Add this repository to HACS as a custom repository (category "Integration"), then install "Sharp Aquos TV".
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for "Sharp Aquos TV", and fill in:
   - **TV IP address**
   - **Username** (Only if you set it on the TV, otherwise blank.)
   - **Password** (Only if you set it on the TV, otherwise blank.)
   - **Power on enabled** If you turn this off, Home Assistant will not be able to turn the TV on.
  
   Note: Even with Power on enable turned on, you will have to turn it on manually at least once for HA to be able to turn it on going forward. On some models, the TV may display a Sharp Aquos logo on the screen when it is "turned off".

No YAML editing or manually edited config files needed - everything is set up through the UI.

## What you get

**Commands**
- Power on/off
- Mute on/off
- Volume control
- Input control (4 HDMI, 1 COMP, 1 tuner)
- Channel select/up/down

**Sensors**
In addition to the current state of the above controls:
- Model info
- Aspect ratio
- AV mode
- Brightness
- Signal strength

All of these are created automatically when you set up the integration - nothing extra to configure.

## HACS

More info about HACS can be found at https://www.hacs.xyz/

## Credits

Based on the official Sharp Aquos TV integration: https://www.home-assistant.io/integrations/aquostv

## License

MIT - see [LICENSE](LICENSE).
