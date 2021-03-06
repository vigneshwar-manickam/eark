"""Module for numerical integrator utilities and interfaces. We define a "solve" function with EARK specific
arguments that relate to the state of the reactor and the initial conditions of the underlying dynamics.
"""

import functools

import numpy as np
from scipy.integrate import odeint

from eark import dynamics
from eark.control import ControlRule
from eark.solution import Solution
from eark.state import State


def state_deriv_array(state_array: np.ndarray, t: float, beta_vector: np.ndarray, precursor_constants: np.ndarray,
                      total_beta: float, period: float, heat_coeff: float, mass_mod: float, heat_cap_mod: float, mass_flow: float,
                      mass_fuel: float, heat_cap_fuel: float, temp_in: float, drum_control_rule: ControlRule) -> np.ndarray:
    """Function to compute the time derivative of the reactor state

    Returns:
        ndarray, the time derivative of the reactor state at time "t"
    """
    state = State.from_array(state_array)

    dndt = dynamics.total_neutron_deriv(beta=total_beta, period=period, power=state.neutron_population,
                                        precursor_constants=precursor_constants, precursor_density=state.precursor_densities,
                                        rho_fuel_temp=state.rho_fuel_temp, rho_mod_temp=state.rho_mod_temp,
                                        rho_con_drum=state.rho_con_drum)

    dcdt = dynamics.delay_neutron_deriv(beta_vector=beta_vector, period=period, power=state.neutron_population,
                                        precursor_constants=precursor_constants, precursor_density=state.precursor_densities)

    dT_moddt = dynamics.mod_temp_deriv(heat_coeff=heat_coeff, mass_mod=mass_mod, heat_cap_mod=heat_cap_mod, mass_flow=mass_flow,
                                       temp_fuel=state.t_fuel, temp_mod=state.t_mod, temp_in=temp_in)

    dT_fueldt = dynamics.fuel_temp_deriv(power=state.neutron_population, mass_fuel=mass_fuel, heat_cap_fuel=heat_cap_fuel,
                                         heat_coeff=heat_coeff, temp_fuel=state.t_fuel, temp_mod=state.t_mod)

    drho_fuel_temp_dt = dynamics.temp_fuel_reactivity_deriv(power=state.neutron_population, beta=total_beta, mass_fuel=mass_fuel,
                                                            heat_cap_fuel=heat_cap_fuel, heat_coeff=heat_coeff, temp_fuel=state.t_fuel,
                                                            temp_mod=state.t_mod)

    drho_mod_temp_dt = dynamics.temp_mod_reactivity_deriv(beta=total_beta, heat_coeff=heat_coeff, mass_mod=mass_mod, heat_cap_mod=heat_cap_mod,
                                                    mass_flow=mass_flow, temp_fuel=state.t_fuel, temp_mod=state.t_mod, temp_in=temp_in)

    ddrum_angle_dt = drum_control_rule.drum_speed(t=t, state=state)

    drho_con_drum_dt = dynamics.con_drum_reactivity_deriv(beta=total_beta, drum_speed=ddrum_angle_dt, drum_angle=state.drum_angle)

    state_deriv = State(dndt, dcdt, dT_moddt, dT_fueldt, drho_fuel_temp_dt, drho_mod_temp_dt, ddrum_angle_dt, drho_con_drum_dt)
    return state_deriv.to_array()


def solve(power_initial: float, precursor_density_initial: np.ndarray, beta_vector: np.ndarray,
          precursor_constants: np.ndarray, total_beta: float, period: float, heat_coeff: float,
          mass_mod: float, heat_cap_mod: float, mass_flow: float, mass_fuel: float, heat_cap_fuel: float,
          temp_in: float, temp_mod_initial: float, temp_fuel_initial: float, drum_control_rule: ControlRule,
          drum_angle_initial: float, t_max: float, t_start: float = 0, num_iters: int = 100) -> Solution:

    """Solving differential equations to calculate parameters of reactor at a certain state

    Args:
        power_initial:
            float, initial reactor power                                [W]
        precursor_density_initial:
            ndarray, 1x6 vector of initial precursor densities          []
        beta_vector:
            ndarray, 1x6 vector of beta_i                               []
        precursor_constants:
            ndarray, 1x6 vector of lambda_i                             []
        total_beta:
            float, delayed neutron fraction                             []
        period:
            float, effective generation time                            [sec]
        heat_coeff:
            float, heat transfer coefficient of fuel and moderator      [J/K/sec]
        mass_mod:
            float, mass of moderator                                    [kg]
        heat_cap_mod:
            float, specific Heat capacity of moderator                  [J/kg/K]
        mass_flow:
            float, total moderator/coolant mass flow rate               [kg/sec]
        mass_fuel:
            float, mass of fuel                                         [kg]
        heat_cap_fuel:
            float, specific heat capacity of fuel                       [J/kg/K]
        T_fuel:
            float, temperature of fuel                                  [K]
        T_mod:
            float, temperature of moderator                             [K]
        temp_in:
            float, temperature of inlet coolant                         [K]
        rho_fuel_temp
            float, reactivity due to fuel temperature                   [dk/K]
        rho_mod_temp
            float, reactivity due to moderator temperature              [dk/K]
        drum_speed:
            float, rotation rate of control drums                       [degrees/sec]
        drum_angle:
            float, angle of control drunk rotation                      [degrees]
        rho_con_drum:
            float, reactivity due to control drum rotation              [dK/theta]
        t_max:
            float, ending time of simulation                            [sec]
        t_start:
            float, default 0, starting time of simulation               [sec]
        num_iters:
            int, default 100, number of iterations                      []

    Returns:
        ndarray, state vector evolution 7xnum_iters

    References:
        [1] https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.odeint.html
    """
    # Build the initial state
    rho_fuel_temp_initial = dynamics.temp_fuel_reactivity(beta=total_beta, temp_fuel=temp_fuel_initial)
    rho_mod_temp_initial = dynamics.temp_mod_reactivity(beta=total_beta, temp_mod=temp_mod_initial)
    rho_con_drum_initial = dynamics.con_drum_reactivity(beta=total_beta, drum_angle=drum_angle_initial)

    initial_state = State(power_initial, precursor_density_initial, temp_mod_initial, temp_fuel_initial, rho_fuel_temp_initial, rho_mod_temp_initial,
                          drum_angle_initial, rho_con_drum_initial)

    # Compute time intervals for odeint integrator
    t = np.linspace(t_start, t_max, num_iters)

    # Partialize the state derivative function for signature compatibility with scipy.odeint, see [1] for "func" signature details
    deriv_func = functools.partial(state_deriv_array,
                                   beta_vector=beta_vector,
                                   precursor_constants=precursor_constants,
                                   total_beta=total_beta,
                                   period=period,
                                   heat_coeff=heat_coeff,
                                   mass_mod=mass_mod,
                                   heat_cap_mod=heat_cap_mod,
                                   mass_flow=mass_flow,
                                   mass_fuel=mass_fuel,
                                   heat_cap_fuel=heat_cap_fuel,
                                   temp_in=temp_in,
                                   drum_control_rule=drum_control_rule)

    # Compute result using odeint integrator, see [1] for numerical details
    res = odeint(deriv_func, initial_state.to_array(), t)

    # Create solution object
    return Solution(array=res, t=np.arange(t_start, t_max, (t_max - t_start) / num_iters))
