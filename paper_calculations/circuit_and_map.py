"""Edge sensor-node circuit, electrical calculations and geographic map for the paper."""
import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm

warnings.filterwarnings("ignore")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------ electrical calculations
calc = {}
V_BAT_MAX, V_BAT_NOM, V_BAT_MIN = 4.20, 3.70, 3.00     # 18650 Li-ion cell
V_REG, V_DROP = 3.30, 0.178                            # MCP1700 LDO, dropout @ 250 mA
calc["ldo_min_input_V"] = V_REG + V_DROP
calc["ldo_efficiency_nominal_pct"] = 100 * V_REG / V_BAT_NOM

# Status LED (red, Vf = 2.0 V, target 10 mA) from a 3.3 V GPIO
VF, I_LED_TARGET = 2.0, 0.010
R_led_ideal = (V_REG - VF) / I_LED_TARGET
R_LED = 150.0                                          # next E12 value up
calc["led_R_ideal_ohm"] = R_led_ideal
calc["led_R_chosen_ohm"] = R_LED
calc["led_I_mA"] = 1e3 * (V_REG - VF) / R_LED
calc["led_P_resistor_mW"] = 1e3 * ((V_REG - VF) / R_LED) ** 2 * R_LED

# Battery-sense divider into the ESP32 ADC (keep below ~2.45 V at 11 dB attenuation)
R1, R2 = 100e3, 100e3
calc["divider_Vadc_at_4V2"] = V_BAT_MAX * R2 / (R1 + R2)
calc["divider_Vadc_at_3V0"] = V_BAT_MIN * R2 / (R1 + R2)
calc["divider_leak_uA"] = 1e6 * V_BAT_MAX / (R1 + R2)
calc["adc_LSB_mV_battery"] = 1e3 * (2.45 / 4095) * (R1 + R2) / R2

# DHT22 pull-up: 10 kOhm on a 3.3 V line
R_PU = 10e3
calc["dht_pullup_sink_mA"] = 1e3 * V_REG / R_PU

# Duty-cycled power budget: wake every 60 s, sense + MQTT publish for 2 s
I_ACTIVE, T_ACTIVE = 0.120, 2.0                        # ESP32 Wi-Fi TX average (A, s)
I_SLEEP = 10e-6 + calc["divider_leak_uA"] * 1e-6 + 1.6e-6   # deep sleep + divider + LDO Iq
I_SENSOR = 1.5e-3                                      # DHT22 during measurement
T_PERIOD = 60.0
I_avg = ((I_ACTIVE + I_SENSOR) * T_ACTIVE + I_SLEEP * (T_PERIOD - T_ACTIVE)) / T_PERIOD
CAP_mAh, DERATE = 2600.0, 0.80
calc["avg_current_mA"] = I_avg * 1e3
calc["battery_life_hours"] = CAP_mAh * DERATE / (I_avg * 1e3)
calc["battery_life_days"] = calc["battery_life_hours"] / 24
calc["energy_per_report_mJ"] = 1e3 * V_BAT_NOM * (I_ACTIVE + I_SENSOR) * T_ACTIVE
# 5-minute reporting variant
T5 = 300.0
I_avg5 = ((I_ACTIVE + I_SENSOR) * T_ACTIVE + I_SLEEP * (T5 - T_ACTIVE)) / T5
calc["avg_current_mA_5min"] = I_avg5 * 1e3
calc["battery_life_days_5min"] = CAP_mAh * DERATE / (I_avg5 * 1e3) / 24

# MQTT traffic seen by the gateway IDS
PAYLOAD, OVERHEAD = 64, 2 + 20 + 20 + 14           # MQTT fixed hdr+topic, TCP, IPv4, Ethernet-ish
calc["bytes_per_report"] = PAYLOAD + OVERHEAD
NODES = 50
calc["gateway_reports_per_s_50nodes"] = NODES / T_PERIOD
calc["gateway_bitrate_bps_50nodes"] = 8 * calc["bytes_per_report"] * NODES / T_PERIOD

# Raspberry Pi 4 gateway running DriftGuard inference
P_PI = 3.4                                            # W, typical under light CPU load
calc["gateway_daily_energy_Wh"] = P_PI * 24
(OUT / "electrical_calcs.json").write_text(json.dumps(calc, indent=2))

# ------------------------------------------------------------ schematic
with schemdraw.Drawing(file=str(OUT / "fig_circuit.png"), dpi=200, show=False) as d:
    d.config(fontsize=10, unit=2.0)
    # battery and rail
    d.add(elm.Ground().at((0, 0)))
    d.add(elm.BatteryCell().endpoints((0, 0), (0, 2.6)).label(""))
    d.add(elm.Label().at((-1.3, 1.3)).label("18650\nLi-ion\n3.0–4.2 V", fontsize=9.5))
    d.add(elm.Line().endpoints((0, 2.6), (0, 4)))
    d.add(elm.Line().endpoints((0, 4), (2, 4)))
    d.add(elm.Dot().at((2, 4)))
    # battery-sense divider
    d.add(elm.Resistor().endpoints((2, 4), (2, 2)).label("R1\n100 kΩ", loc="bottom"))
    d.add(elm.Dot().at((2, 2)))
    d.add(elm.Resistor().endpoints((2, 2), (2, 0)).label("R2\n100 kΩ", loc="bottom"))
    d.add(elm.Ground().at((2, 0)))
    # LDO
    d.add(elm.Line().endpoints((2, 4), (3.6, 4)))
    ldo = d.add(elm.Ic(pins=[elm.IcPin("IN", side="left"), elm.IcPin("GND", side="bottom"),
                              elm.IcPin("OUT", side="right")], size=(2.2, 1.6), pinlblsize=8,
                       plblofst=0.08).anchor("IN").at((3.6, 4)))
    d.add(elm.Label().at((ldo.center[0], ldo.center[1] + 1.3)).label("MCP1700 LDO\n3.3 V", fontsize=9.5))
    d.add(elm.Ground().at(ldo.GND))
    ox = ldo.OUT[0]
    d.add(elm.Line().endpoints(ldo.OUT, (ox + 1.0, 4)))
    d.add(elm.Dot().at((ox + 1.0, 4)).label("3V3", loc="top"))
    d.add(elm.Capacitor().endpoints((ox + 1.0, 4), (ox + 1.0, 2.9)).label("C1 10 µF", loc="bottom"))
    d.add(elm.Ground().at((ox + 1.0, 2.9)))
    vx = ox + 2.6                       # DHT22 VCC tap on the rail
    ex = vx + 3.4                       # ESP32 left edge pins
    d.add(elm.Line().endpoints((ox + 1.0, 4), (ex, 4)))
    d.add(elm.Dot().at((vx, 4)))
    # ESP32 (left pins bottom->top: ADC, 3V3, GPIO4)
    mcu = d.add(elm.Ic(
        pins=[elm.IcPin("GPIO34 (ADC)", side="left", slot="1/3"), elm.IcPin("3V3", side="left", slot="2/3"),
              elm.IcPin("GPIO4", side="left", slot="3/3"), elm.IcPin("GPIO2", side="right", slot="1/2"),
              elm.IcPin("ANT", side="right", slot="2/2"), elm.IcPin(name="", anchorname="GND", side="bottom")],
        size=(6.0, 3.6), pinlblsize=9, label="").anchor("3V3").at((ex, 4)))
    d.add(elm.Ground().at(mcu.GND))
    d.add(elm.Label().at((mcu.center[0], mcu.center[1] + 0.25)).label("ESP32-WROOM\nsensor node", fontsize=11.5))
    d.add(elm.Line().endpoints(mcu.ANT, (mcu.ANT[0] + 0.8, mcu.ANT[1])))
    d.add(elm.Antenna().at((mcu.ANT[0] + 0.8, mcu.ANT[1])).label("Wi-Fi: MQTT/TCP to\nDriftGuard gateway", loc="right", ofst=0.2))
    # ADC route from divider midpoint
    ay = mcu["GPIO34 (ADC)"][1]
    d.add(elm.Line().endpoints((2, 2), (ex - 0.6, 2)).color("#1f5fa8"))
    d.add(elm.Line().endpoints((ex - 0.6, 2), (ex - 0.6, ay)).color("#1f5fa8"))
    d.add(elm.Line().endpoints((ex - 0.6, ay), mcu["GPIO34 (ADC)"]).color("#1f5fa8"))
    # DHT22 above the rail
    gy = mcu.GPIO4[1]
    dx_data = vx + 1.8
    top_y = gy + 2.6
    d.add(elm.Line().endpoints((vx, 4), (vx, top_y)))
    d.add(elm.Line().endpoints((dx_data, gy), (dx_data, top_y)).color("#b03a2e"))
    d.add(elm.Line().endpoints((dx_data, gy), mcu.GPIO4).color("#b03a2e"))
    d.add(elm.Resistor().endpoints((vx, gy + 1.2), (dx_data, gy + 1.2)).label("10 kΩ pull-up", loc="top", fontsize=9))
    d.add(elm.Dot().at((vx, gy + 1.2)))
    d.add(elm.Dot().at((dx_data, gy + 1.2)))
    # DHT22 box drawn as rectangle with three bottom pins
    bx0, bx1 = vx - 0.6, dx_data + 1.8
    d.add(elm.Line().endpoints((bx0, top_y), (bx1, top_y)))
    d.add(elm.Line().endpoints((bx1, top_y), (bx1, top_y + 1.1)))
    d.add(elm.Line().endpoints((bx1, top_y + 1.1), (bx0, top_y + 1.1)))
    d.add(elm.Line().endpoints((bx0, top_y + 1.1), (bx0, top_y)))
    d.add(elm.Label().at(((bx0 + bx1) / 2, top_y + 0.75)).label("DHT22 temp./humidity sensor", fontsize=9.5))
    d.add(elm.Label().at((vx, top_y + 0.25)).label("VCC", fontsize=8))
    d.add(elm.Label().at((dx_data, top_y + 0.25)).label("DATA", fontsize=8))
    d.add(elm.Label().at((dx_data + 1.2, top_y + 0.25)).label("GND", fontsize=8))
    d.add(elm.Line().endpoints((dx_data + 1.2, top_y), (dx_data + 1.2, top_y - 0.5)))
    d.add(elm.Ground().at((dx_data + 1.2, top_y - 0.5)))
    # status LED
    lx = mcu.GPIO2[0]
    d.add(elm.Line().endpoints(mcu.GPIO2, (lx + 0.5, mcu.GPIO2[1])))
    d.add(elm.Resistor().right().at((lx + 0.5, mcu.GPIO2[1])).label("R_LED 150 Ω", loc="top"))
    d.add(elm.LED().down().label("red LED\n8.7 mA", loc="bottom"))
    d.add(elm.Ground())

# ------------------------------------------------------------ geographic map
import geopandas as gpd

world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
sites = [
    ("TON_IoT\nUNSW Canberra, AU", 149.13, -35.28, "#c0392b"),
    ("WUSTL-IIoT-2021\nWashington Univ., St. Louis, US", -90.31, 38.65, "#d68910"),
    ("Edge-IIoTset\nUniv. of Guelma, DZ", 7.43, 36.46, "#7d3c98"),
    ("Edge-IIoTset co-authors\nDe Montfort Univ., UK", -1.14, 52.63, "#7d3c98"),
    ("This study\nFAU, Boca Raton, US", -80.10, 26.37, "#1e8449"),
]
fig, ax = plt.subplots(figsize=(11, 5.6), dpi=200)
world[world.continent != "Antarctica"].plot(ax=ax, color="#e8ecef", edgecolor="#9aa5ad", linewidth=0.4)
fx, fy = -80.10, 26.37
for name, x, y, c in sites:
    if "FAU" not in name:
        ax.annotate("", xy=(fx, fy), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color=c, lw=1.1, alpha=0.55,
                                    connectionstyle="arc3,rad=0.18"))
    ax.scatter(x, y, s=70 if "FAU" in name else 45, color=c, edgecolor="black", zorder=5,
               marker="*" if "FAU" in name else "o")
offsets = {"TON_IoT": (-90, -32), "WUSTL": (-200, 15), "Edge-IIoTset\nUniv": (12, -28),
           "Edge-IIoTset co": (10, 14), "This study": (12, -26)}
for name, x, y, c in sites:
    key = next(k for k in offsets if name.startswith(k))
    ax.annotate(name, (x, y), xytext=offsets[key], textcoords="offset points", fontsize=8.5,
                color=c, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=c, lw=0.6, alpha=0.9))
ax.set_xlim(-170, 180); ax.set_ylim(-58, 80)
ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
ax.set_title("Origin of the three IoT/IIoT benchmark datasets and the study site", fontsize=12)
ax.grid(alpha=0.25, lw=0.4)
fig.tight_layout(); fig.savefig(OUT / "fig_map.png"); plt.close(fig)

# great-circle distances to FAU (haversine)
import math
def hav(a, b, c, d):
    r = 6371.0; p1, p2 = math.radians(b), math.radians(d)
    dp, dl = p2 - p1, math.radians(c - a)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))
dist = {n.split("\n")[0]: round(hav(x, y, fx, fy)) for n, x, y, _ in sites if "FAU" not in n}
(OUT / "map_distances_km.json").write_text(json.dumps(dist, indent=2))
print(json.dumps(calc, indent=2)); print(dist)
