"""
Fracture and destruction system
Implements Voronoi-based fracture patterns and rigid body breakage
"""
import numpy as np
from typing import List, Tuple
from scipy.spatial import Voronoi
from ..core.component import PhysicsBody, Transform


class FractureSystem:
    """System for handling object fracture and destruction"""
    
    def __init__(self):
        self.voronoi_points = []
        
    def fracture_object(self, position: np.ndarray, size: np.ndarray, 
                       fracture_points: List[np.ndarray], 
                       material_strength: float = 100.0) -> List:
        """
        Fracture an object using Voronoi tessellation
        
        Args:
            position: World position of the object
            size: Size of the object (for bounding box)
            fracture_points: Points where fracture originates
            material_strength: Material strength parameter
            
        Returns:
            List of fractured pieces (each with position, size, physics properties)
        """
        # Generate fracture pattern using Voronoi tessellation
        pieces = self._generate_voronoi_fracture(position, size, fracture_points)
        
        # Calculate stress distribution and determine which pieces break off
        fractured_pieces = self._calculate_fracture_pieces(pieces, material_strength)
        
        return fractured_pieces
    
    def _generate_voronoi_fracture(self, position: np.ndarray, size: np.ndarray, 
                                  fracture_points: List[np.ndarray]) -> List:
        """Generate fracture pattern using Voronoi tessellation"""
        # Create bounding box for the object
        min_corner = position - size / 2
        max_corner = position + size / 2
        
        # Add the fracture points and some random points for realistic fracture
        all_points = fracture_points.copy()
        
        # Add random points for more natural fracture patterns
        for _ in range(5):  # Add 5 random points
            random_offset = np.random.uniform(-0.3, 0.3, 3) * size
            all_points.append(position + random_offset)
        
        # Generate 3D Voronoi by creating 2D Voronoi on each plane and stacking
        points_2d = np.array([[p[0], p[2]] for p in all_points])  # XZ plane
        vor = Voronoi(points_2d)
        
        # Convert Voronoi regions to 3D pieces
        pieces = []
        for region_idx in vor.regions:
            if len(region_idx) == 0 or -1 in region_idx:
                continue
                
            # Get vertices of the region
            vertices = vor.vertices[region_idx]
            
            # Create a 3D bounding box for this piece
            if len(vertices) > 0:
                min_x, min_z = vertices.min(axis=0)
                max_x, max_z = vertices.max(axis=0)
                
                # Extrude in Y direction (height of original object)
                piece_min = np.array([min_x, min_corner[1], min_z])
                piece_max = np.array([max_x, max_corner[1], max_z])
                
                piece_center = (piece_min + piece_max) / 2
                piece_size = piece_max - piece_min
                
                pieces.append({
                    'position': piece_center,
                    'size': piece_size,
                    'volume': np.prod(piece_size)
                })
        
        return pieces
    
    def _calculate_fracture_pieces(self, pieces: List, material_strength: float) -> List:
        """Calculate which pieces break off based on stress distribution"""
        fractured_pieces = []
        
        for piece in pieces:
            # Calculate if this piece should break off based on size and stress
            volume = piece['volume']
            stress_threshold = material_strength * volume  # Simplified model
            
            # Random factor to make fracture more natural
            random_factor = np.random.uniform(0.5, 1.5)
            
            # If piece is small enough, it breaks off
            if volume < 0.1 or (volume < 0.5 and random_factor < 1.0):
                # Create physics body for this piece
                physics_body = PhysicsBody(
                    mass=volume * 1000,  # Assuming density of 1000 kg/m^3
                    is_static=False
                )
                
                # Add some initial velocity based on fracture force
                physics_body.velocity = np.random.uniform(-2, 2, 3)
                
                fractured_pieces.append({
                    'transform': Transform(position=piece['position']),
                    'physics_body': physics_body,
                    'size': piece['size']
                })
        
        return fractured_pieces


class DestructibleCube:
    """A cube that can be destructed with fracture physics"""
    
    def __init__(self, position: np.ndarray, size: np.ndarray):
        self.position = position
        self.size = size
        self.health = 100.0
        self.intact = True
        self.fracture_system = FractureSystem()
        self.fragments = []
        
    def apply_damage(self, damage: float, impact_position: np.ndarray):
        """Apply damage to the cube"""
        self.health -= damage
        
        if self.health <= 0 and self.intact:
            self._fracture(impact_position)
    
    def _fracture(self, impact_position: np.ndarray):
        """Fracture the cube at the impact position"""
        # Calculate fracture points around the impact
        fracture_points = [impact_position]
        
        # Add some additional fracture points for more realistic breakage
        for _ in range(3):
            offset = np.random.uniform(-0.2, 0.2, 3) * self.size
            fracture_points.append(impact_position + offset)
        
        # Generate fragments
        self.fragments = self.fracture_system.fracture_object(
            self.position,
            self.size,
            fracture_points
        )
        
        self.intact = False
    
    def is_broken(self) -> bool:
        """Check if the cube is broken"""
        return not self.intact
    
    def get_fragments(self) -> List:
        """Get the fragments after breaking"""
        return self.fragments if not self.intact else []