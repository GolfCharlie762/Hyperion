"""
SPH (Smoothed Particle Hydrodynamics) fluid simulation system
Uses Numba for JIT compilation to accelerate physics calculations
"""
import numpy as np
import numba
from numba import jit, prange
from typing import Tuple


class SPHSystem:
    """Main SPH system class"""
    def __init__(self, 
                 particle_count: int = 5000,
                 smoothing_radius: float = 0.1,
                 rest_density: float = 1000.0,
                 viscosity: float = 0.1,
                 pressure_stiffness: float = 3.0,
                 gravity: np.ndarray = None):
        
        self.particle_count = particle_count
        self.smoothing_radius = smoothing_radius
        self.rest_density = rest_density
        self.viscosity = viscosity
        self.pressure_stiffness = pressure_stiffness
        self.gravity = np.array(gravity or [0.0, -9.81, 0.0], dtype=np.float32)
        
        # Initialize particle data using Structure of Arrays (SoA) for performance
        self.positions = np.random.uniform(-1.0, 1.0, (particle_count, 3)).astype(np.float32)
        self.velocities = np.zeros((particle_count, 3), dtype=np.float32)
        self.densities = np.full(particle_count, rest_density, dtype=np.float32)
        self.pressures = np.zeros(particle_count, dtype=np.float32)
        self.forces = np.zeros((particle_count, 3), dtype=np.float32)
        
        # Boundary parameters
        self.boundary_min = np.array([-3.0, -1.0, -3.0], dtype=np.float32)
        self.boundary_max = np.array([3.0, 5.0, 3.0], dtype=np.float32)
        self.boundary_damping = -0.5
        
        # Precompute constants
        self.kernel_constant = 8.0 / (np.pi * smoothing_radius**4)
        self.pressure_constant = pressure_stiffness * rest_density
        
    def update(self, dt: float):
        """Update the SPH simulation"""
        # Calculate densities and pressures
        calculate_densities_and_pressures(
            self.positions, 
            self.densities, 
            self.pressures,
            self.smoothing_radius,
            self.rest_density,
            self.pressure_constant,
            self.particle_count
        )
        
        # Calculate forces
        calculate_forces(
            self.positions,
            self.velocities, 
            self.densities,
            self.pressures,
            self.forces,
            self.smoothing_radius,
            self.viscosity,
            self.kernel_constant,
            self.gravity,
            self.particle_count
        )
        
        # Integrate motion
        integrate_motion(
            self.positions,
            self.velocities,
            self.forces,
            dt,
            self.boundary_min,
            self.boundary_max,
            self.boundary_damping,
            self.particle_count
        )
        
        # Clear forces for next frame
        self.forces.fill(0.0)


@jit(nopython=True, parallel=True)
def calculate_densities_and_pressures(positions, densities, pressures, smoothing_radius, 
                                   rest_density, pressure_constant, particle_count):
    """Calculate density and pressure for each particle using SPH kernel"""
    h = smoothing_radius
    h_sq = h * h
    
    for i in prange(particle_count):
        density = 0.0
        
        for j in range(particle_count):
            if i == j:
                continue
                
            # Calculate distance between particles
            dx = positions[i, 0] - positions[j, 0]
            dy = positions[i, 1] - positions[j, 1] 
            dz = positions[i, 2] - positions[j, 2]
            dist_sq = dx*dx + dy*dy + dz*dz
            
            if dist_sq < h_sq:
                r = np.sqrt(dist_sq)
                # Cubic spline kernel
                q = r / h
                if q <= 1.0:
                    if q <= 0.5:
                        kernel_value = 8.0 / (np.pi * h**4) * (1 - 6*q*q + 6*q*q*q)
                    else:
                        kernel_value = 8.0 / (np.pi * h**4) * 2 * (1 - q)**3
                    density += kernel_value
        
        densities[i] = max(density, rest_density * 0.1)  # Prevent division by zero
        pressures[i] = pressure_constant * (densities[i] / rest_density - 1.0)


@jit(nopython=True, parallel=True)
def calculate_forces(positions, velocities, densities, pressures, forces, 
                    smoothing_radius, viscosity, kernel_constant, gravity, particle_count):
    """Calculate forces on each particle (pressure, viscosity, external forces)"""
    h = smoothing_radius
    h_sq = h * h
    
    for i in prange(particle_count):
        # Add gravity force
        forces[i, 1] += gravity[1]  # Only Y component for now
        
        pressure_force = np.array([0.0, 0.0, 0.0], dtype=numba.float32)
        viscosity_force = np.array([0.0, 0.0, 0.0], dtype=numba.float32)
        
        for j in range(particle_count):
            if i == j:
                continue
                
            # Calculate distance between particles
            dx = positions[i, 0] - positions[j, 0]
            dy = positions[i, 1] - positions[j, 1]
            dz = positions[i, 2] - positions[j, 2]
            dist_sq = dx*dx + dy*dy + dz*dz
            
            if dist_sq < h_sq:
                r = np.sqrt(dist_sq)
                
                # Compute gradient of kernel
                if r > 1e-8:  # Prevent division by zero
                    grad_kernel = compute_kernel_gradient(dx, dy, dz, r, h)
                    
                    # Pressure force
                    pressure_term = (pressures[i] + pressures[j]) / (2.0 * densities[j])
                    pressure_force -= grad_kernel * pressure_term
                    
                    # Viscosity force
                    vel_diff = velocities[j] - velocities[i]
                    viscosity_force += viscosity * vel_diff * (grad_kernel / densities[j])
        
        # Apply forces
        forces[i] += pressure_force
        forces[i] += viscosity_force


@jit(nopython=True)
def compute_kernel_gradient(dx, dy, dz, r, h):
    """Compute gradient of cubic spline kernel"""
    q = r / h
    h_inv = 1.0 / h
    
    if q <= 0.5:
        grad_mag = 24.0 / (np.pi * h**5) * q * (3.0 * q - 2.0)
    else:
        grad_mag = 24.0 / (np.pi * h**5) * (1.0 - q)**2
        grad_mag = -grad_mag if q > 1e-8 else 0.0
    
    # Normalize and scale by gradient magnitude
    if r > 1e-8:
        return np.array([dx/r * grad_mag, dy/r * grad_mag, dz/r * grad_mag], dtype=numba.float32)
    else:
        return np.array([0.0, 0.0, 0.0], dtype=numba.float32)


@jit(nopython=True)
def integrate_motion(positions, velocities, forces, dt, boundary_min, boundary_max, boundary_damping, particle_count):
    """Integrate particle motion using Verlet integration"""
    for i in range(particle_count):
        # Apply forces to acceleration
        acceleration = forces[i]  # Forces already include gravity
        
        # Update velocity
        velocities[i] += acceleration * dt
        
        # Update position
        positions[i] += velocities[i] * dt
        
        # Boundary collision handling
        for j in range(3):  # X, Y, Z axes
            if positions[i, j] < boundary_min[j]:
                positions[i, j] = boundary_min[j]
                velocities[i, j] *= boundary_damping
            elif positions[i, j] > boundary_max[j]:
                positions[i, j] = boundary_max[j]
                velocities[i, j] *= boundary_damping