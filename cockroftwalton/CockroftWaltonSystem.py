import numpy as np
import schemdraw
import schemdraw.elements as elm
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

class CockroftWaltonSystem:
    def __init__(self, n_stages=3, v_peak=10@u_V, freq=1@u_kHz, cap=100@u_uF, r_load=1@u_GOhm):
        self.n_stages = n_stages
        self.v_peak = v_peak
        self.freq = freq
        self.cap = cap
        self.r_load = r_load
        self.circuit = None
        self.drawing = None
        self.analysis = None

    def create_circuit(self, draw=True):
        """Generates both PySpice Netlist and SchemDraw Drawing."""
        self.circuit = Circuit(f'{self.n_stages}-Stage CW Multiplier')
        self.circuit.model('Dmodel', 'D', Is=1e-20, N=1, Rs=0.1)
        self.circuit.SinusoidalVoltageSource('Vs', 'vin', self.circuit.gnd, 
                                            amplitude=self.v_peak, frequency=self.freq)

        d = schemdraw.Drawing()
        d.config(unit=2.5, fontsize=12)
        
        # Grid settings
        top_y, bot_y, x_inc = 3.5, 0, 2.5
        v_src = d.add(elm.SourceSin().label(f'Vs={self.v_peak}').at((0, bot_y)).to((0, top_y)))
        d.add(elm.Ground().at(v_src.start))
        
        prev_t_node, prev_b_node = 'vin', '0'
        prev_t_pos, prev_b_pos = v_src.end, v_src.start

        for i in range(1, self.n_stages + 1):
            t_node, b_node = f'top_{i}', f'bot_{i}'
            pk_x, vl_x = (2*i-1)*x_inc, (2*i)*x_inc
            
            # Components & Netlist
            self.circuit.C(f't{i}', prev_t_node, t_node, self.cap)
            ct = d.add(elm.Capacitor().at(prev_t_pos).to((pk_x, top_y)).label(f'C{2*i-1}', loc='top'))
            
            self.circuit.D(f'v{i}', prev_b_node, t_node, model='Dmodel')
            d.add(elm.Diode().at(prev_b_pos).to(ct.end).label(f'D{2*i-1}', loc='bot'))
            
            self.circuit.D(f'f{i}', t_node, b_node, model='Dmodel')
            df = d.add(elm.Diode().at(ct.end).to((vl_x, bot_y)).label(f'D{2*i}', loc='bot'))
            
            self.circuit.C(f'b{i}', prev_b_node, b_node, self.cap)
            d.add(elm.Capacitor().at(prev_b_pos).to(df.end).label(f'C{2*i}', loc='bottom'))

            prev_t_node, prev_b_node, prev_t_pos, prev_b_pos = t_node, b_node, ct.end, df.end

        self.circuit.R('load', prev_b_node, self.circuit.gnd, self.r_load)
        d.add(elm.Line().right().at(prev_b_pos).length(1))
        d.add(elm.Resistor().down().label('RL'))
        d.add(elm.Ground())
        
        self.drawing = d
        return self.circuit, self.drawing

    def run_simulation(self, end_time=100@u_ms, step_time=10@u_us):
        """Executes transient analysis."""
        simulator = self.circuit.simulator(temperature=25)
        self.analysis = simulator.transient(step_time=step_time, end_time=end_time)
        return self.analysis

    def plot(self):
        """Static Matplotlib analysis (optional)."""
        if self.analysis is None:
            return
        import matplotlib.pyplot as plt
        time = np.array(self.analysis.time) * 1000
        plt.figure(figsize=(10, 5))
        plt.plot(time, self.analysis["vin"], label="Input", color="gray", alpha=0.5)
        for i in range(1, self.n_stages + 1):
            plt.plot(time, self.analysis[f"bot_{i}"], label=f"Stage {i}")
        plt.title(f"CW Multiplier - {self.n_stages} Stages")
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage (V)")
        plt.legend()
        plt.grid(True)
        plt.show()
        
    def export_svg(self, path="cw.svg"):
        if self.drawing is None:
            raise RuntimeError("Call create_circuit(draw=True) first.")
        # Depending on schemdraw version, d.save("file.svg") is supported.
        self.drawing.save(path)
        return path

    def export_npz(self, path="cw_sim.npz", nodes=None):
        if self.analysis is None:
            raise RuntimeError("Run simulation first.")
        if nodes is None:
            # By default, save vin and all bot_i/top_i.
            nodes = ["vin"]
            for i in range(1, self.n_stages + 1):
                nodes += [f"top_{i}", f"bot_{i}"]

        t = np.array(self.analysis.time)  # seconds (PySpice usually uses seconds)
        out = {"t": t}

        for n in nodes:
            out[n] = np.array(self.analysis[n])

        np.savez(path, **out)
        return path    
