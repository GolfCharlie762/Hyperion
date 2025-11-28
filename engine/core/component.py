"""
Base component classes for the entity-component system
"""
import numpy as np


class Component:
    """Base component class"""
    def __init__(self):
        self.entity = None
        self.active = True
    
    def update(self, dt: float):
        """Update component logic"""
        pass


class Transform:
    """Transform component holding position, rotation, scale"""
    def __init__(self, position=None, rotation=None, scale=None):
        self.position = np.array(position or [0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array(rotation or [0.0, 0.0, 0.0], dtype=np.float32)  # Euler angles
        self.scale = np.array(scale or [1.0, 1.0, 1.0], dtype=np.float32)
    
    def get_matrix(self):
        """Get transformation matrix"""
        # Create translation matrix
        translation = np.eye(4, dtype=np.float32)
        translation[0:3, 3] = self.position
        
        # Create rotation matrix (simplified - only Y rotation for now)
        ry = self.rotation[1]
        rotation_y = np.array([
            [np.cos(ry), 0, np.sin(ry), 0],
            [0, 1, 0, 0],
            [-np.sin(ry), 0, np.cos(ry), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Create scale matrix
        scale = np.eye(4, dtype=np.float32)
        scale[0, 0] = self.scale[0]
        scale[1, 1] = self.scale[1]
        scale[2, 2] = self.scale[2]
        
        # Combine transformations
        return translation @ rotation_y @ scale


class Renderable:
    """Component for renderable objects"""
    def __init__(self, mesh=None, material=None):
        self.mesh = mesh
        self.material = material
        self.visible = True


class PhysicsBody:
    """Component for physics simulation"""
    def __init__(self, mass=1.0, is_static=False):
        self.mass = mass
        self.is_static = is_static
        self.velocity = np.zeros(3, dtype=np.float32)
        self.acceleration = np.zeros(3, dtype=np.float32)
        self.forces = np.zeros(3, dtype=np.float32)
    
    def add_force(self, force):
        """Add a force to the body"""
        self.forces += force
    
    def clear_forces(self):
        """Clear accumulated forces"""
        self.forces.fill(0.0)