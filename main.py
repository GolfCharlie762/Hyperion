"""
Main entry point for the cross-platform game engine
Implements Qt application with OpenGL widget, SPH particle system,
deferred shading pipeline, and destructible cube demo
"""
import sys
import numpy as np
from PyQt6.QtWidgets import QApplication
from engine.core.application import EngineApplication
from engine.core.scene import Scene, Entity, Camera
from engine.core.component import Transform, Renderable, PhysicsBody
from engine.physics.fracture import DestructibleCube
from engine.physics.sph import SPHSystem


def create_demo_scene():
    """Create a demo scene with fluid simulation and destructible objects"""
    scene = Scene()
    
    # Create camera
    camera = Camera()
    camera.transform.position = np.array([0.0, 2.0, 8.0])
    scene.camera = camera
    
    # Create a destructible cube
    cube_entity = Entity("DestructibleCube")
    cube_entity.transform.position = np.array([0.0, 2.0, 0.0])
    cube_entity.transform.scale = np.array([1.0, 1.0, 1.0])
    
    # Add renderable component (simplified - would have actual mesh)
    cube_renderable = Renderable()
    cube_entity.add_component(cube_renderable)
    
    # Add physics component
    cube_physics = PhysicsBody(mass=10.0, is_static=False)
    cube_entity.add_component(cube_physics)
    
    scene.add_entity(cube_entity)
    
    # Create destructible cube object
    destructible_cube = DestructibleCube(
        position=np.array([0.0, 2.0, 0.0]),
        size=np.array([1.0, 1.0, 1.0])
    )
    cube_entity.destructible = destructible_cube  # Store reference for interaction
    
    # Create fluid particles
    sph_system = SPHSystem(particle_count=2000)
    
    # Add some simple light entities (simplified representation)
    light_entity = Entity("MainLight")
    light_entity.transform.position = np.array([2.0, 4.0, 2.0])
    scene.lights.append(light_entity)
    
    return scene, sph_system


def main():
    """Main entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Initialize engine
    engine_app = EngineApplication()
    engine_app.initialize()
    
    # Create demo scene
    scene, sph_system = create_demo_scene()
    engine_app.scene = scene
    engine_app.physics_system = sph_system  # Override with SPH system
    
    # Add mouse click interaction for destructible cube
    def handle_mouse_click(x, y):
        """Handle mouse clicks to break cubes"""
        # Find destructible cube in scene
        for entity in scene.entities:
            if hasattr(entity, 'destructible') and entity.name == "DestructibleCube":
                # Apply damage at a position near the cube
                impact_pos = entity.transform.position + np.random.uniform(-0.2, 0.2, 3)
                entity.destructible.apply_damage(150.0, impact_pos)  # High damage to ensure breakage
                
                # If cube is broken, replace with fragments
                if entity.destructible.is_broken():
                    fragments = entity.destructible.get_fragments()
                    for frag_data in fragments:
                        frag_entity = Entity("Fragment")
                        frag_entity.transform = frag_data['transform']
                        
                        # Add physics to fragment
                        frag_physics = frag_data['physics_body']
                        frag_entity.add_component(frag_physics)
                        
                        # Add renderable component
                        frag_renderable = Renderable()
                        frag_entity.add_component(frag_renderable)
                        
                        scene.add_entity(frag_entity)
                    
                    # Remove original cube
                    scene.remove_entity(entity)
                break
    
    # Connect mouse click to OpenGL widget (simplified)
    def mousePressEvent(event):
        handle_mouse_click(event.x(), event.y())
    
    # Monkey patch the mouse event (in a real app, this would be done properly)
    original_mouse_event = engine_app.main_window.opengl_widget.mousePressEvent
    def new_mouse_event(self, event):
        mousePressEvent(event)
        if original_mouse_event:
            original_mouse_event(event)
    
    engine_app.main_window.opengl_widget.mousePressEvent = new_mouse_event.__get__(
        engine_app.main_window.opengl_widget, 
        type(engine_app.main_window.opengl_widget)
    )
    
    print("Game Engine Started!")
    print("Click on the cube to break it into fragments")
    print("Close the window to exit")
    
    # Run the application
    return engine_app.run()


if __name__ == "__main__":
    sys.exit(main())