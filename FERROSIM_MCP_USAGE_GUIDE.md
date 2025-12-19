# FerroSim MCP Server - Complete Usage Guide

## Overview

The enhanced FerroSim MCP server now supports all scenarios from `FerroSim_v3.ipynb`:
- ✅ Default simulations
- ✅ Custom electric fields (sine, step, polynomial, zero)
- ✅ Custom defects (random, periodic)
- ✅ Ground state calculations
- ✅ Visualization generation (viewable in Claude Desktop)

## Available Tools

### 1. initialize_simulation
Create simulations with basic or advanced parameters.

### 2. run_simulation
Execute a created simulation.

### 3. get_simulation_results
Retrieve numerical results.

### 4. visualize_simulation
Generate plots that Claude can display.

### 5. compare_with_afm_data
Compare simulation with experimental data.

### 6. list_simulations
List all active simulations.

---

## Example Prompts for Claude Desktop

### Basic Simulation (Default)
```
"Create a FerroSim simulation with n=20, k=1.5, and run it. Show me the results."
```

### Custom Electric Field - Sine Wave
```
"Create a simulation with a custom sine wave electric field:
- n=20
- mode='tetragonal'
- field_config: {
    type: 'sine',
    params: {
      amplitude_x: 180,
      amplitude_y: 180,
      freq_x: 2.0,
      freq_y: 2.0,
      phase: 0
    }
  }
- Run it and show me a quiver plot"
```

### Custom Electric Field - Step Function (Ground State)
```
"Create a ground state simulation:
- n=20
- mode='tetragonal'
- k=10.0
- dep_alpha=0.2
- init='random'
- t_end=3.0
- n_steps=800
- field_config: {
    type: 'step',
    params: {
      Ex: -0.5,
      Ey: -0.5,
      step_fraction: 0.25
    }
  }
- Run it and visualize the magnitude and angle"
```

### Custom Electric Field - Polynomial Modulation
```
"Run a simulation with polynomial-modulated electric field:
- n=20
- mode='tetragonal'  
- init='random'
- t_end=2.0
- n_steps=500
- field_config: {
    type: 'polynomial',
    params: {
      amplitude_x: 180,
      amplitude_y: 180,
      freq_x: 2.0,
      freq_y: 2.0,
      power: 2.0,
      offset: 0.5
    }
  }
- Show me the summary plot"
```

### Random Defects
```
"Create a simulation with random defects:
- n=20
- k=1.0
- dep_alpha=0.05
- defect_config: {
    type: 'random',
    params: {
      num_defects: 8,
      strength_mean: 15.0,
      strength_std: 0.5,
      seed: 42
    }
  }
- Run and visualize"
```

### Periodic Defects
```
"Create a simulation with periodic defects:
- n=10
- mode='tetragonal'
- t_end=4.0
- n_steps=500
- defect_config: {
    type: 'periodic',
    params: {
      row_spacing: 5,
      col_spacing: 10,
      strength_mean: 15.5,
      strength_std: 0.5
    }
  }
- field_config: {
    type: 'sine',
    params: {
      amplitude_x: 10,
      amplitude_y: 190,
      freq_x: 1.0,
      freq_y: 1.0
    }
  }
- Run and show me a quiver plot"
```

### Ground State - Tetragonal
```
"Find the tetragonal ground state:
- n=20
- mode='tetragonal'
- k=10.0
- dep_alpha=0.2
- init='random'
- t_end=3.0
- n_steps=800
- field_config: {
    type: 'step',
    params: {
      Ex: -0.5,
      Ey: -0.5,
      step_fraction: 0.25
    }
  }
- Run and show magnitude_angle visualization"
```

### Ground State - Rhombohedral
```
"Find the rhombohedral ground state:
- n=20
- mode='rhombohedral'
- k=4.0
- dep_alpha=0.1
- init='random'
- t_end=10.0
- n_steps=800
- field_config: {
    type: 'step',
    params: {
      Ex: -5.5,
      Ey: -5.5,
      step_fraction: 0.25
    }
  }
- Run and visualize"
```

### Ground State - Squareelectric
```
"Find the squareelectric ground state:
- n=30
- mode='squareelectric'
- k=4.0
- dep_alpha=10.1
- init='random'
- t_end=3.0
- n_steps=100
- field_config: {
    type: 'step',
    params: {
      Ex: -8.5,
      Ey: -8.5,
      step_fraction: 0.25
    }
  }
- Run and show results"
```

---

## Electric Field Types

### 1. Sine Wave (`type: 'sine'`)
**Parameters:**
- `amplitude_x`: Amplitude in x direction (default: 0.0)
- `amplitude_y`: Amplitude in y direction (default: 10.0)
- `freq_x`: Frequency in x direction (default: 1.0)
- `freq_y`: Frequency in y direction (default: 1.0)
- `phase`: Phase shift for y component (default: 0.0)

**Formula:**
```
Ex(t) = Ax * sin(2π * fx * t)
Ey(t) = Ay * sin(2π * fy * t + phase)
```

### 2. Step Function (`type: 'step'`)
**Parameters:**
- `Ex`: Field strength in x direction (default: 0.0)
- `Ey`: Field strength in y direction (default: 0.5)
- `step_fraction`: Fraction of time field is on (default: 0.25)

**Use case:** Ground state calculations - apply field initially, then remove

### 3. Polynomial Modulation (`type: 'polynomial'`)
**Parameters:**
- `amplitude_x`: Base amplitude for x (default: 180.0)
- `amplitude_y`: Base amplitude for y (default: 180.0)
- `freq_x`: Frequency in x (default: 2.0)
- `freq_y`: Frequency in y (default: 2.0)
- `power`: Polynomial exponent (default: 2.0)
- `offset`: Time offset (default: 0.5)

**Formula:**
```
Ex(t) = Ax * (t + offset)^power * sin(2π * fx * t)
Ey(t) = Ay * (t + offset)^power * cos(4π * fy * t)
```

### 4. Zero Field (`type: 'zero'`)
No field applied - for pure relaxation studies.

---

## Defect Types

### 1. No Defects (`type: 'none'`)
Clean lattice, no defects.

### 2. Random Defects (`type: 'random'`)
**Parameters:**
- `num_defects`: Number of random defects (default: 5)
- `strength_mean`: Mean defect strength (default: 15.0)
- `strength_std`: Standard deviation (default: 0.5)
- `seed`: Random seed for reproducibility (optional)

Random field defects placed at random locations with random orientations.

### 3. Periodic Defects (`type: 'periodic'`)
**Parameters:**
- `row_spacing`: Row spacing for periodic grid (default: 5)
- `col_spacing`: Column spacing (default: 10)
- `strength_mean`: Mean defect strength (default: 15.5)
- `strength_std`: Standard deviation (default: 0.5)
- `seed`: Random seed (default: 42)

Defects placed on a periodic grid pattern.

---

## Visualization Types

### 1. Summary (`viz_type: 'summary'`)
Full time evolution showing:
- Total polarization vs time
- Energy vs time
- Spatial polarization pattern evolution

### 2. Quiver (`viz_type: 'quiver'`)
Vector field plot showing polarization direction and magnitude at each lattice site.

### 3. Magnitude and Angle (`viz_type: 'magnitude_angle'`)
Two plots:
- Polarization magnitude at each site
- Polarization angle at each site

---

## Material Modes

- **`tetragonal`**: Tetragonal phase (coupled Px, Py with specific Landau coefficients)
- **`rhombohedral`**: Rhombohedral phase (different coupling)
- **`uniaxial`**: Single polarization component
- **`squareelectric`**: Decoupled Px and Py components

---

## Tips for Using with Claude Desktop

1. **Start Simple**: Begin with basic simulations, then add complexity
2. **Visualize Often**: Request visualizations to understand what's happening
3. **Compare Modes**: Try the same parameters with different modes
4. **Ground States**: Use `init='random'` + step field + high k for ground states
5. **Parameter Exploration**: Ask Claude to vary parameters systematically

## Example Workflow

```
You: "Let's explore tetragonal ferroelectrics. First, create a basic simulation 
      with n=20, k=1.5, and run it."

Claude: [Initializes and runs simulation]
        "I've created simulation xyz123 and run it. The final polarization is..."

You: "Now show me a quiver plot of the final state."

Claude: [Generates visualization]
        "Here's the quiver plot showing the polarization vectors..."

You: "Great! Now let's find the ground state. Create a new simulation with 
      init='random', k=10.0, and a step field that turns off after 25% of the time."

Claude: [Creates ground state simulation]
        "I've set up a ground state calculation with those parameters..."
```

---

## Advanced Example: Full Ground State Study

```
"Let's do a comprehensive ground state study:

1. Create a tetragonal ground state simulation with n=20, k=10.0, init='random', 
   step field (Ey=-0.5 for 25% of time), run for t=3.0

2. Run the simulation

3. Show me three visualizations: summary, quiver, and magnitude_angle

4. Get the numerical results for the final timestep

5. Tell me about the domain structure you observe"
```

Claude will execute all steps and provide detailed analysis with visual results!

---

## Troubleshooting

**Server not responding?**
- Restart Claude Desktop (⌘+Q and reopen)
- Check: `~/Library/Logs/Claude/mcp-server-ferrosim.log`

**Simulations taking too long?**
- Reduce `n` (lattice size)
- Reduce `n_steps` (time resolution)  
- Increase `k` (faster convergence for ground states)

**Want to see progress?**
- Add `verbose: true` to run_simulation (progress bars go to log file)

---

## What's Different from Notebook?

| Feature | Notebook | MCP Server |
|---------|----------|------------|
| Interface | Jupyter cells | Natural language prompts |
| Visualization | Inline plots | Base64 images Claude can display |
| Parameter Setting | Python code | JSON-like descriptions |
| Workflow | Sequential cells | Conversational back-and-forth |
| State | Variables in memory | Persistent simulations by ID |

**Advantage**: With Claude Desktop, you can describe what you want in natural language and Claude handles the technical details!

