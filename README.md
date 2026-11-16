# Mars Lander Simulator

A 2D rigid-body model of a Mars landing module with spring-damper landing legs, a parachute
deployment sequence and PID autopilot, plus a procedural lunar terrain generator kept in the same
repository.

The lander is simulated as a planar rigid body under Martian gravity with thrust and torque control,
and rendered live in a Pygame window with a HUD showing altitude, vertical/horizontal speed, pitch
angle, leg compression and contact state.

University coursework project, cleaned up for publication. Code comments are in Russian (original),
README in English.

## Lander model (`lander/`)

**State vector:** `[x, y, φ, Vx, Vy, ω]` — planar position, attitude, linear and angular velocity.
Moment of inertia of the body: `I = m·(w² + L²)/12`.

| Parameter | Value |
|---|---|
| Body | 6.0 × 4.0 m, 1000 kg |
| Gravity (Mars) | 3.71 m/s² |
| Atmosphere | `ρ = 0.05·exp(−h/11000)`, aeroshell `Cd·A = 1.2 · 20 m²` |
| Main engine | up to 15 kN thrust, up to 800 N·m torque |
| Landing legs | rest length 1.2 m, `k = 50 kN/m`, `c = 10 kN·s/m`, stroke 0.5 m, deploy below 15 m |
| Parachute | `Cd·A = 1.2 · 50 m²`, opens below 800 m while slower than 100 m/s |
| Integration | explicit, `dt = 0.01 s` |

**Landing legs** are modelled individually (`landing_leg.py`): spring force `k·δ` plus damping `c·δ̇`,
clamped at maximum compression, with contact detection and a bounce fix — a leg that is compressed
beyond its stroke is treated as a hard stop rather than an oscillator.

**Control.** Two modes: `MANUAL` (keyboard thrust and torque, with rotation damping and torque decay)
and `AUTO`, where three independent PID loops hold vertical speed, pitch angle and height:

```
KP/KI/KD  =  30/0.5/5  (vertical speed)
             200/5/50  (pitch)
             10/2/5    (height)
```

The autopilot switches to terminal descent below 20 m and targets a touchdown at 0.5 m/s.

**Success criteria** are checked at contact: `|Vy| ≤ 5 m/s`, `|Vx| ≤ 1 m/s`, `|φ| ≤ 15°`,
`|ω| ≤ 10 °/s`. Telemetry is logged at 10 Hz and up to 10 000 samples are retained for post-flight plots.

## Procedural lunar terrain (`lunar_terrain/`)

`terrain_final.py` builds a synthetic cratered surface from four stacked layers:

1. **Base relief** — OpenSimplex noise (fixed seed, amplitude 0.02) for gentle undulation;
2. **Crater field** — crater diameters drawn from a power-law distribution
   (`min 2 m`, `max 70 m`, `power −2.8`) placed at random centres;
3. **Gaussian crater profiles** — each crater added as a smooth Gaussian depression or rim;
4. **Shading** — Gaussian blur for regolith smoothing, then a Matplotlib `LightSource` hillshade.

The intermediate versions (`terrain_v1` … `v3`) are kept to show the progression from noise-only
terrain to the final layered model. Rendered result: `docs/lunar_surface_final.png`.

## Layout

```
mars-lander-sim/
├─ lander/
│  ├─ config.py                # all physical constants and PID gains
│  ├─ rocket_mars.py           # rigid-body dynamics, engine, parachute, autopilot
│  ├─ landing_leg.py           # spring-damper leg model with hard stop
│  ├─ simple_visualization.py  # Pygame renderer + HUD
│  └─ main.py                  # entry point (autopilot landing from 200 m)
├─ lunar_terrain/
│  ├─ terrain_final.py         # layered crater generator
│  ├─ terrain_v1.py … v3.py    # earlier iterations
│  ├─ gaussian_crater.py       # single-crater Gaussian profile
│  └─ noise_playground.py      # OpenSimplex experiments
└─ docs/lunar_surface_final.png
```

## Quick start

```bash
pip install -r requirements.txt

cd lander
python main.py            # autopilot descent from 200 m
```

Terrain generation:

```bash
cd lunar_terrain
python terrain_final.py   # writes lunar_surface_final.png
```

## Notes and limitations

* Planar (2D) dynamics: roll, yaw and lateral tilt are not modelled.
* The atmosphere is exponential and monotonic — no wind gusts, dust or density fluctuations.
* Engine is treated as an ideal thruster with instant response; no propellant consumption, so mass and
  centre of mass stay constant.
* Coursework scope: the goal was to demonstrate guidance and contact dynamics, not flight-qualified
  fidelity.

## Stack

Python 3.10+ · NumPy · SciPy · Matplotlib · Pygame · OpenSimplex
