import numpy as np

from eark.state import StateComponent
from eark.utilities import plot


class Solution:
    __slots__ = ('_array', '_t')

    def __init__(self, array: np.ndarray, t: np.ndarray):
        self._array = array
        self._t = t

    @property
    def array(self):
        return self._array

    @property
    def t(self):
        return self._t

    @property
    def neutron_population(self):
        return self._array[:, StateComponent.NeutronPopulation]

    @property
    def precursor_densities(self):
        return self._array[:, StateComponent.PrecursorDensity1:StateComponent.TMod]

    def precursor_density(self, i: int):
        """Get a time series of precursor densities of the ith kind

        Args:
            i:
                index of the vector component. These are 1-indexed, to match the mathematical notation.

        Returns:
            ndarray
        """
        return self.precursor_densities[:, i - 1]

    @property
    def temp_mod(self):
        return self._array[:, StateComponent.TMod]

    @property
    def temp_fuel(self):
        return self._array[:, StateComponent.TFuel]

    @property
    def rho_fuel_temp(self):
        return self._array[:, StateComponent.RhoFuelTemp]

    @property
    def rho_mod_temp(self):
        return self._array[:, StateComponent.RhoModTemp]

    @property
    def drum_angle(self):
        return self._array[:, StateComponent.DrumAngle]

    @property
    def rho_con_drum(self):
        return self._array[:, StateComponent.RhoConDrum]

    def plot_power(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=self.neutron_population, label='$P(t)$', y_label='Power',
                                title='Power v. Time', output_file=output_file)

    def plot_densities(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=[self.precursor_density(i) for i in range(1, 7)], label=lambda i: '$c_{:d}$'.format(i),
                                color=plot.DENSITY_COLORS,
                                title="Concentration of Neutron Precursors vs. Time",
                                y_label=r"Concentration of Neutron Precursors, $c_i [\#/dr^3]$", output_file=output_file)

    def plot_temp_fuel(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=self.temp_fuel, y_label="Fuel  Temperature [K]",
                                label=r'$T_{fuel}$', title='Fuel Temperature vs. Time', output_file=output_file)

    def plot_temp_mod(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=self.temp_mod, y_label="Moderator Temperature [K]",
                                label=r'$T_{mod}$', title='Moderator Temperature vs. Time', output_file=output_file)

    def plot_rho_fuel_temp(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=self.rho_fuel_temp, y_label=r"Fuel Temperature Reactivity [$\Delta k$]",
                                label=r'$\rho_{fuel temp}$', title='Fuel Temperature Reactivity vs. Time', output_file=output_file)

    def plot_rho_mod_temp(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=self.rho_mod_temp, y_label=r"Moderator Temperature Reactivity [$\Delta k$]",
                                label=r'$\rho_{mod temp}$', title='Moderator Temperature Reactivity vs. Time', output_file=output_file)

    def plot_rho_con_drum(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.t, y=self.rho_con_drum, y_label=r"Control Drum Reactivity [$\Delta k$]",
                                label=r'$\rho_{CD}$', title='Control Drum Reactivity vs. Time', output_file=output_file)

    def plot_rho_con_drum_angle(self, output_file: str = None):
        plot.plot_soln_quantity(t=self.drum_angle, y=self.rho_con_drum, y_label=r"Control Drum Reactivity [$\Delta k$]",
                                x_label=r'Drum Angle [$\theta_{CD}$]',label=r'$\rho_{CD}$', title='Control Drum Reactivity vs. Drum Angle', output_file=output_file)
