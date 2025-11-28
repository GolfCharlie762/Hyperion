"""
Deferred rendering system
Implements deferred shading pipeline with G-buffer and lighting pass
"""
import moderngl
import numpy as np
from typing import Optional
from ..core.scene import Scene
from ..core.component import Transform, Renderable


class DeferredRenderer:
    """Deferred rendering pipeline implementation"""
    
    def __init__(self, opengl_widget):
        self.opengl_widget = opengl_widget
        self.ctx = None
        self.geometry_fbo = None
        self.lighting_fbo = None
        self.screen_quad_vao = None
        self.geometry_program = None
        self.lighting_program = None
        self.screen_program = None
        
        # G-buffer textures
        self.position_texture = None
        self.normal_texture = None
        self.albedo_texture = None
        self.depth_texture = None
        
        # Initialize renderer
        self._init_renderer()
    
    def _init_renderer(self):
        """Initialize the deferred rendering pipeline"""
        self.ctx = self.opengl_widget.ctx
        
        # Create G-buffer textures
        self._create_gbuffer()
        
        # Create shader programs
        self._create_shaders()
        
        # Create fullscreen quad for lighting pass
        self._create_screen_quad()
    
    def _create_gbuffer(self):
        """Create G-buffer textures for deferred rendering"""
        # Get viewport dimensions
        width, height = self.ctx.fbo.size
        
        # Create textures for G-buffer
        self.position_texture = self.ctx.texture(
            (width, height), 
            components=3, 
            dtype='f4'
        )
        self.position_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self.normal_texture = self.ctx.texture(
            (width, height), 
            components=3, 
            dtype='f4'
        )
        self.normal_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self.albedo_texture = self.ctx.texture(
            (width, height), 
            components=4, 
            dtype='f4'
        )
        self.albedo_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self.depth_texture = self.ctx.depth_texture((width, height))
        
        # Create geometry framebuffer
        self.geometry_fbo = self.ctx.framebuffer(
            color_attachments=[
                self.position_texture,
                self.normal_texture, 
                self.albedo_texture
            ],
            depth_attachment=self.depth_texture
        )
    
    def _create_shaders(self):
        """Create shader programs for deferred rendering"""
        # Geometry pass shader
        self.geometry_program = self.ctx.program(
            vertex_shader='''
                #version 330 core
                in vec3 in_position;
                in vec3 in_normal;
                in vec3 in_color;
                
                uniform mat4 model;
                uniform mat4 view;
                uniform mat4 projection;
                
                out vec3 frag_position;
                out vec3 frag_normal;
                out vec3 frag_color;
                
                void main() {
                    vec4 world_pos = model * vec4(in_position, 1.0);
                    gl_Position = projection * view * world_pos;
                    
                    frag_position = world_pos.xyz;
                    frag_normal = mat3(transpose(inverse(model))) * in_normal;
                    frag_color = in_color;
                }
            ''',
            fragment_shader='''
                #version 330 core
                in vec3 frag_position;
                in vec3 frag_normal;
                in vec3 frag_color;
                
                out vec3 out_position;
                out vec3 out_normal;
                out vec4 out_albedo;
                
                void main() {
                    out_position = frag_position;
                    out_normal = normalize(frag_normal);
                    out_albedo = vec4(frag_color, 1.0);
                }
            '''
        )
        
        # Lighting pass shader
        self.lighting_program = self.ctx.program(
            vertex_shader='''
                #version 330 core
                in vec2 in_texcoord;
                out vec2 texcoord;
                
                void main() {
                    gl_Position = vec4(in_texcoord * 2.0 - 1.0, 0.0, 1.0);
                    texcoord = in_texcoord;
                }
            ''',
            fragment_shader='''
                #version 330 core
                in vec2 texcoord;
                out vec4 out_color;
                
                uniform sampler2D g_position;
                uniform sampler2D g_normal;
                uniform sampler2D g_albedo;
                uniform vec3 light_pos = vec3(2.0, 4.0, 2.0);
                uniform vec3 light_color = vec3(1.0, 1.0, 1.0);
                uniform vec3 camera_pos;
                
                void main() {
                    vec3 frag_pos = texture(g_position, texcoord).rgb;
                    vec3 normal = texture(g_normal, texcoord).rgb;
                    vec4 albedo_spec = texture(g_albedo, texcoord);
                    vec3 albedo = albedo_spec.rgb;
                    
                    // Simple point light calculation
                    vec3 light_dir = normalize(light_pos - frag_pos);
                    vec3 view_dir = normalize(camera_pos - frag_pos);
                    vec3 reflect_dir = reflect(-light_dir, normal);
                    
                    float diff = max(dot(light_dir, normal), 0.0);
                    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32.0);
                    
                    vec3 ambient = 0.1 * albedo;
                    vec3 diffuse = diff * light_color * albedo;
                    vec3 specular = spec * light_color * albedo_spec.a;
                    
                    out_color = vec4(ambient + diffuse + specular, 1.0);
                }
            '''
        )
        
        # Simple screen quad shader for debugging
        self.screen_program = self.ctx.program(
            vertex_shader='''
                #version 330 core
                in vec2 in_texcoord;
                out vec2 texcoord;
                
                void main() {
                    gl_Position = vec4(in_texcoord * 2.0 - 1.0, 0.0, 1.0);
                    texcoord = in_texcoord;
                }
            ''',
            fragment_shader='''
                #version 330 core
                in vec2 texcoord;
                out vec4 out_color;
                
                uniform sampler2D screen_texture;
                
                void main() {
                    out_color = texture(screen_texture, texcoord);
                }
            '''
        )
    
    def _create_screen_quad(self):
        """Create a fullscreen quad for post-processing"""
        quad_vertices = np.array([
            -1.0,  1.0,  0.0, 1.0,  # top-left
             1.0,  1.0,  1.0, 1.0,  # top-right
            -1.0, -1.0,  0.0, 0.0,  # bottom-left
             1.0, -1.0,  1.0, 0.0   # bottom-right
        ], dtype=np.float32)
        
        vbo = self.ctx.buffer(quad_vertices)
        self.screen_quad_vao = self.ctx.vertex_array(
            self.screen_program,
            [(vbo, '2f 2f', 'in_position', 'in_texcoord')],
        )
    
    def render(self, scene: Scene):
        """Render the scene using deferred rendering"""
        # Clear buffers
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        # Geometry pass: render scene to G-buffer
        self._geometry_pass(scene)
        
        # Lighting pass: apply lighting using G-buffer
        self._lighting_pass(scene)
    
    def _geometry_pass(self, scene: Scene):
        """Render geometry to G-buffer"""
        self.geometry_fbo.use()
        self.geometry_fbo.clear(0.0, 0.0, 0.0, 0.0)
        
        # Set up matrices (simplified)
        view = np.eye(4, dtype=np.float32)
        projection = np.eye(4, dtype=np.float32)
        
        # Set up perspective projection
        fovy = np.radians(60.0)
        aspect = self.ctx.fbo.size[0] / self.ctx.fbo.size[1]
        near = 0.1
        far = 100.0
        
        projection[0, 0] = 1.0 / (aspect * np.tan(fovy / 2.0))
        projection[1, 1] = 1.0 / np.tan(fovy / 2.0)
        projection[2, 2] = -(far + near) / (far - near)
        projection[2, 3] = -2.0 * far * near / (far - near)
        projection[3, 2] = -1.0
        
        self.geometry_program['view'].write(view.tobytes())
        self.geometry_program['projection'].write(projection.tobytes())
        
        # Render each renderable entity
        for entity in scene.entities:
            if not entity.active:
                continue
                
            renderable = entity.get_component('Renderable')
            if renderable and renderable.visible:
                # Get model matrix from transform
                model_matrix = entity.transform.get_matrix()
                self.geometry_program['model'].write(model_matrix.tobytes())
                
                # Render the mesh (simplified - would need actual mesh data)
                self._render_mesh(renderable.mesh)
    
    def _lighting_pass(self, scene: Scene):
        """Apply lighting using G-buffer"""
        # Bind screen framebuffer
        self.ctx.bind_framebuffer(0)  # Default framebuffer
        
        # Use lighting shader
        self.lighting_program.use()
        
        # Bind G-buffer textures
        self.position_texture.use(location=0)
        self.normal_texture.use(location=1) 
        self.albedo_texture.use(location=2)
        
        self.lighting_program['g_position'].value = 0
        self.lighting_program['g_normal'].value = 1
        self.lighting_program['g_albedo'].value = 2
        self.lighting_program['camera_pos'].value = (0.0, 0.0, 5.0)  # Camera position
        
        # Render fullscreen quad
        self.screen_quad_vao.render(moderngl.TRIANGLE_STRIP)
    
    def _render_mesh(self, mesh):
        """Render a mesh (placeholder - would implement actual mesh rendering)"""
        # This is a placeholder for actual mesh rendering
        # In a real implementation, this would render actual geometry
        pass
    
    def cleanup(self):
        """Clean up renderer resources"""
        if self.geometry_fbo:
            self.geometry_fbo.release()
        if self.position_texture:
            self.position_texture.release()
        if self.normal_texture:
            self.normal_texture.release()
        if self.albedo_texture:
            self.albedo_texture.release()
        if self.depth_texture:
            self.depth_texture.release()
        if self.screen_quad_vao:
            self.screen_quad_vao.release()
        if self.geometry_program:
            self.geometry_program.release()
        if self.lighting_program:
            self.lighting_program.release()
        if self.screen_program:
            self.screen_program.release()