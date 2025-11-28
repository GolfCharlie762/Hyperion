"""
Scene management system
Handles entities, components, and scene graph
"""
import numpy as np
from typing import List, Dict, Optional
from .component import Component, Transform


class Entity:
    """Basic entity in the scene"""
    def __init__(self, name: str = ""):
        self.name = name
        self.id = id(self)
        self.components: Dict[str, Component] = {}
        self.active = True
        self.transform = Transform()
        
    def add_component(self, component: Component):
        """Add a component to the entity"""
        component_type = type(component).__name__
        self.components[component_type] = component
        component.entity = self
        
    def get_component(self, component_type: str) -> Optional[Component]:
        """Get a component by type"""
        return self.components.get(component_type)
    
    def remove_component(self, component_type: str):
        """Remove a component by type"""
        if component_type in self.components:
            del self.components[component_type]


class Scene:
    """Scene container holding all entities"""
    def __init__(self):
        self.entities: List[Entity] = []
        self.entity_map: Dict[int, Entity] = {}
        self.camera = None
        self.lights = []
        
    def add_entity(self, entity: Entity) -> Entity:
        """Add an entity to the scene"""
        self.entities.append(entity)
        self.entity_map[entity.id] = entity
        return entity
    
    def remove_entity(self, entity: Entity):
        """Remove an entity from the scene"""
        if entity in self.entities:
            self.entities.remove(entity)
            if entity.id in self.entity_map:
                del self.entity_map[entity.id]
    
    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """Find an entity by name"""
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None
    
    def update(self, dt: float):
        """Update all entities in the scene"""
        for entity in self.entities[:]:  # Copy list to allow removal during iteration
            if entity.active:
                for component in entity.components.values():
                    if hasattr(component, 'update'):
                        component.update(dt)


class Camera:
    """Camera component for rendering"""
    def __init__(self):
        self.fov = 60.0
        self.near = 0.1
        self.far = 1000.0
        self.aspect_ratio = 16.0 / 9.0
        self.transform = Transform()
        
    def get_view_matrix(self):
        """Get the view matrix for this camera"""
        # Placeholder - would implement actual view matrix calculation
        return np.eye(4, dtype=np.float32)
    
    def get_projection_matrix(self):
        """Get the projection matrix for this camera"""
        # Placeholder - would implement actual projection matrix calculation
        return np.eye(4, dtype=np.float32)