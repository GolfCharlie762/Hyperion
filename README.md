# Cross-Platform 2D/3D Game Engine

A high-performance game engine written in Python with Qt-based editor UI, supporting real-time simulation of fluid dynamics, destructible environments, and physically-based rendering.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Editor UI Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Qt Editor     │  │   Asset         │  │   Profiler &    │  │
│  │   (PyQt6)       │  │   Manager       │  │   Debug Vis     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Engine Core Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │   Physics   │  │  Rendering  │  │   Audio     │  │ Input   ││
│  │   System    │  │   System    │  │   System    │  │ System  ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
│         │                 │              │              │      │
│         ▼                 ▼              ▼              ▼      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │  SPH Solver │  │  Deferred   │  │  Audio      │  │ Event   ││
│  │  (Taichi)   │  │  Renderer   │  │  Engine     │  │ Handler ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Backend Abstraction Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │   OpenGL    │  │  Vulkan     │  │   OpenCL    │  │ Platform││
│  │  (ModernGL) │  │  (PyVulkan) │  │  (PyOpenCL) │  │  Layer  ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Physics System
- **SPH Fluid Simulation**: Smoothed Particle Hydrodynamics with Numba-accelerated kernels
- **Destructible Environments**: Voronoi-based fracture mechanics with rigid body breakage
- **Real-time Simulation**: Optimized for 60+ FPS performance

### Rendering System
- **Deferred Shading**: G-buffer based rendering pipeline with lighting pass
- **PBR Materials**: Physically-based rendering with metallic-roughness workflow
- **Shadow Mapping**: Real-time shadow generation (simplified implementation)

### Editor UI
- **Qt-based Interface**: Cross-platform editor with OpenGL viewport
- **Live Editing**: Real-time scene manipulation and debugging
- **Performance Profiling**: Built-in tools for optimization

## Core Implementation

### SPH Fluid Simulation
The SPH system uses Numba JIT compilation for performance:
- Cubic spline kernel for density calculation
- Pressure and viscosity force computation
- Boundary collision handling
- Structure of Arrays (SoA) layout for cache efficiency

### Fracture System
- Voronoi tessellation for realistic fracture patterns
- Stress distribution calculations
- Rigid body physics for fragments
- Configurable material strength parameters

### Deferred Renderer
- Geometry pass: Renders to G-buffer (position, normal, albedo)
- Lighting pass: Applies PBR lighting using G-buffer data
- Modular shader system for extensibility

## Performance Optimizations

1. **Data-Oriented Design**: Structure of Arrays for particle systems
2. **JIT Compilation**: Numba for physics calculations
3. **GPU Acceleration**: ModernGL for rendering pipeline
4. **Multi-threading**: Qt event loop with background processing
5. **Memory Management**: Pool allocation for dynamic objects

## Usage

```bash
pip install -r requirements.txt
python main.py
```

Click on the destructible cube to break it into fragments, or observe the fluid simulation.

## MVP Features Demonstrated

1. **Qt Application**: OpenGL widget with event handling
2. **SPH Particle System**: Numba-accelerated fluid simulation
3. **Deferred Shading**: Basic G-buffer and lighting pass
4. **Destructible Cube**: Mouse-click triggered fracture simulation
5. **Modular Architecture**: Separated core, physics, rendering, and UI systems

## Roadmap

### Phase 1: Core Foundation
- [x] Basic Qt editor with OpenGL viewport
- [x] Simple rendering pipeline
- [x] Particle system foundation

### Phase 2: Physics Implementation
- [x] SPH solver with Numba
- [x] Basic fracture mechanics
- [x] Collision detection

### Phase 3: Advanced Features
- [x] Deferred rendering pipeline
- [x] PBR material system
- [x] Advanced fracture simulation

## Dependencies

- PyQt6: Cross-platform UI framework
- ModernGL: Modern OpenGL wrapper
- Numba: JIT compilation for physics
- NumPy: Vectorized operations
- SciPy: Scientific computing (Voronoi tessellation)
- Taichi: Alternative for GPU-accelerated physics (optional)

## Cross-Platform Support

The engine is designed to work on Windows, macOS, and Linux through:
- Qt for UI and platform abstraction
- OpenGL for graphics rendering
- Python standard library for core functionality
- No platform-specific APIs used