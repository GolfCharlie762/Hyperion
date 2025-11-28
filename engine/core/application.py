"""
Main application class for the game engine
Handles initialization, main loop, and resource management
"""
import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtOpenGL import QOpenGLWidget
import OpenGL.GL as gl
import moderngl
import numpy as np


class EngineApplication:
    def __init__(self):
        self.app = None
        self.main_window = None
        self.opengl_context = None
        self.renderer = None
        self.physics_system = None
        self.scene = None
        self.running = False
        
    def initialize(self):
        """Initialize the engine application"""
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Initialize core systems
        self._init_rendering()
        self._init_physics()
        self._init_scene()
        
        # Setup main loop timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        self.running = True
    
    def _init_rendering(self):
        """Initialize rendering system"""
        from engine.rendering.renderer import DeferredRenderer
        self.renderer = DeferredRenderer(self.main_window.opengl_widget)
    
    def _init_physics(self):
        """Initialize physics system"""
        from engine.physics.sph import SPHSystem
        self.physics_system = SPHSystem()
    
    def _init_scene(self):
        """Initialize initial scene"""
        from engine.core.scene import Scene
        self.scene = Scene()
        
    def update(self):
        """Main update loop"""
        if self.running:
            # Update physics
            self.physics_system.update(1.0/60.0)  # 60 FPS delta time
            
            # Update scene
            self.scene.update(1.0/60.0)
            
            # Render
            self.renderer.render(self.scene)
            
            # Update OpenGL widget
            self.main_window.opengl_widget.update()
    
    def run(self):
        """Run the application"""
        return self.app.exec()
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        if self.renderer:
            self.renderer.cleanup()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Engine Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with OpenGL
        self.opengl_widget = OpenGLViewport(self)
        self.setCentralWidget(self.opengl_widget)
        
        # Create menu
        self._create_menu()
    
    def _create_menu(self):
        """Create application menu"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu('View')
        debug_action = view_menu.addAction('Debug View')
        debug_action.setCheckable(True)


class OpenGLViewport(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ctx = None
        self.fbo = None
        
    def initializeGL(self):
        """Initialize OpenGL context"""
        # Initialize moderngl context
        self.ctx = moderngl.create_context(require=330)
        
        # Enable depth testing and other OpenGL settings
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        
    def resizeGL(self, width, height):
        """Handle resize events"""
        self.ctx.viewport = (0, 0, width, height)
        
    def paintGL(self):
        """Render the scene"""
        # Clear the screen
        self.ctx.clear(0.1, 0.1, 0.1, 1.0)  # Dark gray background